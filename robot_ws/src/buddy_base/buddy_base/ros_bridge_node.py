"""buddy_base bridge node — the thin rclpy shell around BaseCore.

All drive logic (kinematics, odometry, clamping) lives in base_core.py and is
host-tested against the mock MCU (test_integration_mock.py); this file only
does ROS plumbing + serial I/O. Runs on the Jetson against either the real
MCU (/dev/ttyACM* via the udev rule) or `python3 mock_mcu.py`'s pty — same
code path, which is the point.

    ros2 run buddy_base bridge_node --ros-args -p port:=/dev/ttyACM0
"""

from __future__ import annotations

import math

import rclpy
import serial  # python3-serial / pyserial
from geometry_msgs.msg import TransformStamped, Twist
from nav_msgs.msg import Odometry as OdomMsg
from rclpy.node import Node
from sensor_msgs.msg import BatteryState, JointState
from tf2_ros import TransformBroadcaster

from buddy_base.base_core import BaseCore, bp, params_from_design

JOINT_NAMES = ["left_front_wheel_joint", "left_rear_wheel_joint",
               "right_front_wheel_joint", "right_rear_wheel_joint"]


class BridgeNode(Node):
    def __init__(self):
        super().__init__("buddy_base_bridge")
        self.declare_parameter("port", "/dev/ttyACM0")
        self.declare_parameter("baud", 921600)
        self.declare_parameter("repo_root", "")  # for buddy_calcs params
        self.declare_parameter("auto_arm", False)

        from pathlib import Path
        repo = self.get_parameter("repo_root").value
        repo_root = Path(repo) if repo else Path(__file__).resolve().parents[4]
        self.core = BaseCore(params_from_design(repo_root))

        port = self.get_parameter("port").value
        self.ser = serial.Serial(port, self.get_parameter("baud").value,
                                 timeout=0)
        self.parser = bp.Parser()
        self.get_logger().info(f"bridge up on {port}; params: "
                               f"r={self.core.params.wheel_radius_m} m, "
                               f"track={self.core.params.track_m} m")

        self.create_subscription(Twist, "cmd_vel", self.on_cmd_vel, 5)
        self.pub_odom = self.create_publisher(OdomMsg, "odom", 10)
        self.pub_joints = self.create_publisher(JointState, "joint_states", 10)
        self.pub_batt = self.create_publisher(BatteryState, "battery_state", 5)
        self.tf = TransformBroadcaster(self)

        self._last_cmd_stamp = self.get_clock().now()
        self._armed_sent = False
        p = self.core.params
        self.create_timer(1.0 / p.cmd_resend_hz, self.keepalive)
        self.create_timer(0.005, self.pump_serial)  # 200 Hz read
        self.create_timer(1.0, self.housekeeping)

    # ---------------------------------------------------------------- ROS in
    def on_cmd_vel(self, msg: Twist) -> None:
        self.core.set_cmd(msg.linear.x, msg.angular.z)
        self._last_cmd_stamp = self.get_clock().now()

    # ------------------------------------------------------------- timers
    def keepalive(self) -> None:
        # ROS-side dead-man: zero the command if /cmd_vel goes silent
        age = (self.get_clock().now() - self._last_cmd_stamp).nanoseconds * 1e-9
        if age > self.core.params.cmd_vel_timeout_s:
            self.core.stop()
        self.ser.write(self.core.next_cmd_frame())

    def pump_serial(self) -> None:
        data = self.ser.read(512)
        if not data:
            return
        now = self.get_clock().now()
        for f in self.parser.feed(data):
            if f.type == bp.T_TELEMETRY:
                self.core.handle_telemetry(bp.Telemetry.unpack(f.payload),
                                           now.nanoseconds * 1e-9)
                self.publish_state(now)
            elif f.type == bp.T_FAULT_EVT:
                # FAULT_EVT is emitted on ANY state transition (drive_protocol.md:
                # "on transition"), not only on faults - main.c sends it whenever
                # state or fault_bits change. Logging all of them at WARN buried
                # real faults under routine SAFE_IDLE->ARMED chatter, so split on
                # whether any fault bit is actually set.
                #
                # Use the state carried IN the event payload rather than
                # core.state_name(): the latter is whatever the last telemetry
                # frame said, which is not necessarily the state this transition
                # was about.
                bits = int.from_bytes(f.payload[:2], "little")
                state = f.payload[2] if len(f.payload) > 2 else None
                sname = (bp.STATE_NAMES[state]
                         if state is not None and state < len(bp.STATE_NAMES)
                         else self.core.state_name())
                if bits:
                    self.get_logger().warn(f"MCU fault: bits=0x{bits:04x} state={sname}")
                else:
                    self.get_logger().info(f"MCU state -> {sname}")

    def housekeeping(self) -> None:
        if (self.get_parameter("auto_arm").value and not self._armed_sent
                and self.core.mcu_state == bp.STATE_SAFE_IDLE):
            self.get_logger().info("auto-arm: requesting ARM")
            self.ser.write(self.core.mode_frame(bp.MODE_ARM))
            self._armed_sent = True

    # ---------------------------------------------------------------- ROS out
    def publish_state(self, now) -> None:
        o = self.core.odom
        qz, qw = math.sin(o.theta / 2.0), math.cos(o.theta / 2.0)

        msg = OdomMsg()
        msg.header.stamp = now.to_msg()
        msg.header.frame_id = "odom"
        msg.child_frame_id = "base_footprint"
        msg.pose.pose.position.x = o.x
        msg.pose.pose.position.y = o.y
        msg.pose.pose.orientation.z = qz
        msg.pose.pose.orientation.w = qw
        msg.twist.twist.linear.x = o.v
        msg.twist.twist.angular.z = o.w
        self.pub_odom.publish(msg)

        t = TransformStamped()
        t.header = msg.header
        t.child_frame_id = "base_footprint"
        t.transform.translation.x = o.x
        t.transform.translation.y = o.y
        t.transform.rotation.z = qz
        t.transform.rotation.w = qw
        self.tf.sendTransform(t)

        js = JointState()
        js.header.stamp = msg.header.stamp
        js.name = JOINT_NAMES
        js.position = list(self.core.wheel_positions_rad())
        self.pub_joints.publish(js)

        if self.core.last_telemetry is not None:
            b = BatteryState()
            b.header.stamp = msg.header.stamp
            b.voltage = self.core.last_telemetry.vbat_mv / 1000.0
            b.present = True
            self.pub_batt.publish(b)


def main(args=None):
    rclpy.init(args=args)
    node = BridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.core.stop()
        try:
            node.ser.write(node.core.next_cmd_frame())  # parting zero-command
        except Exception:
            pass
        node.destroy_node()


if __name__ == "__main__":
    main()
