# Jetson Orin Nano Super Setup

**Status 2026-07-15:** Jetson is flashed and running JetPack/Ubuntu. The next
step is ROS 2 Jazzy + the Buddy workspace — scripted, ~15–30 min, no purchased
hardware needed:

```bash
git clone <repo-url> ~/Buddy_Robot   # or pull latest
cd ~/Buddy_Robot
./devops/jetson/setup_ros2_jazzy.sh
```

The script is idempotent (safe to re-run) and finishes by running the full
host-side test suite and building `buddy_base`/`buddy_bringup` with
`--symlink-install` (required — in-repo imports).

## The zero-hardware milestone (do this right after)

Prove the entire drive stack on the robot's real computer before any parts arrive:

```bash
# Terminal A — the mock MCU prints its pty path:
python3 robot_ws/src/buddy_firmware_interfaces/python/mock_mcu.py

# Terminal B — bridge against the mock:
ros2 launch buddy_bringup base.launch.py port:=/dev/pts/N auto_arm:=true

# Terminal C — drive it and watch odometry:
ros2 run teleop_twist_keyboard teleop_twist_keyboard
ros2 topic echo /odom
```

Success = keyboard driving moves `/odom` and `/joint_states`, and killing
Terminal C (or B) shows the watchdog stop in the bridge log. From your Mac on
the same network with `ROS_DOMAIN_ID=42`, Foxglove/RViz will see the topics —
that validates the whole operator path too.

## Remaining checklist

- [ ] Run `setup_ros2_jazzy.sh`; complete the zero-hardware milestone above.
- [ ] SSH keys + hostname per `devops/networking/network_plan.md`.
- [ ] Enable MAXN/super power mode only after checking cooling under load.
- [ ] NVMe for bags/builds if not already the boot device.
- [ ] Gazebo (`ros-jazzy-ros-gz`) for on-Jetson sim — optional, sim also runs on a desktop.
- [ ] When hardware arrives: udev rule check (`ls -l /dev/buddy*`), then the
      bench checklist in TODO Phase 5.
