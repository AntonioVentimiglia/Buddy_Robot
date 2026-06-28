# Repeat ROS 2 Simulation Startup Routine

This guide is for the steps you repeat after turning on your computer when you want to open RViz, Gazebo, teleop, topic inspection, and torque tools for the Buddy robot workspace.

It assumes:

- You are on Windows.
- You are using WSL2 with Ubuntu 24.04.
- ROS 2 Jazzy is already installed.
- Your workspace is located at `~/robot_ws` inside Ubuntu.
- Your workspace has already been built at least once with `colcon build --symlink-install`.

---

# Fast startup checklist

## 1. Open Ubuntu

Open **Windows Terminal** or **PowerShell**, then start Ubuntu:

```powershell
wsl -d Ubuntu-24.04
```

You should see a Linux prompt like:

```bash
venti@Antonio-PC:~$
```

If you see this instead:

```powershell
PS C:\Users\venti>
```

you are still in PowerShell, not Ubuntu.

---

## 2. Go to your robot workspace

```bash
cd ~/robot_ws
```

---

## 3. Load ROS and your workspace

If you added both setup files to `~/.bashrc`, this may already be done automatically. Running this again is safe:

```bash
source /opt/ros/jazzy/setup.bash
source ~/robot_ws/install/setup.bash
```

Quick check:

```bash
echo $ROS_DISTRO
ros2 pkg list | grep buddy
```

Expected ROS distro:

```text
jazzy
```

Expected package output should include packages such as:

```text
buddy_description
buddy_simulation
```

---

## 4. Rebuild only if you changed files

If you edited URDF, Xacro, launch files, package files, or Python nodes, rebuild:

```bash
colcon build --symlink-install
source install/setup.bash
```

If you only want to run the existing simulation and changed nothing, skip this step.

---

## 5. Open RViz robot model viewer

Use this when you want to inspect the robot model, frames, links, joints, and sensor placement:

```bash
ros2 launch buddy_description view_model.launch.py
```

Leave this running while you inspect the model.

Stop it with:

```text
Ctrl+C
```

---

## 6. Open Gazebo simulation

Open a **second Ubuntu terminal**.

Then run:

```bash
cd ~/robot_ws
source /opt/ros/jazzy/setup.bash
source ~/robot_ws/install/setup.bash
ros2 launch buddy_simulation gazebo_lab.launch.py
```

Gazebo should open and spawn the Buddy simulation model.

---

## 7. Open keyboard teleop

Open a **third Ubuntu terminal**.

Then run:

```bash
source /opt/ros/jazzy/setup.bash
source ~/robot_ws/install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/cmd_vel
```

Use the keyboard controls shown in the terminal to drive the robot.

Keep the teleop terminal focused while driving.

Stop teleop with:

```text
Ctrl+C
```

---

## 8. Inspect topics while simulation is running

Open a **fourth Ubuntu terminal**.

Run:

```bash
source /opt/ros/jazzy/setup.bash
source ~/robot_ws/install/setup.bash
ros2 topic list
```

Useful checks:

```bash
ros2 topic echo /odom --once
ros2 topic echo /scan --once
ros2 topic echo /cmd_vel --once
```

Useful rate checks:

```bash
ros2 topic hz /odom
ros2 topic hz /scan
```

Stop rate checks with:

```text
Ctrl+C
```

---

## 9. Run torque sweep calculations

This does not require Gazebo or RViz. From any Ubuntu terminal:

```bash
cd ~/robot_ws
python3 tools/torque_sweep.py \
  --mass-kg 30 \
  --wheel-radius-m 0.06 \
  --driven-wheels 4 \
  --speed-mps 1.5 \
  --ramp-deg 20
```

For a safer early prototype comparison:

```bash
python3 tools/torque_sweep.py \
  --mass-kg 20 \
  --wheel-radius-m 0.06 \
  --driven-wheels 4 \
  --speed-mps 0.5 \
  --ramp-deg 5
```

---

## 10. Normal shutdown

In each running terminal, stop ROS/Gazebo/RViz/teleop with:

```text
Ctrl+C
```

Then exit Ubuntu terminals with:

```bash
exit
```

Optional full WSL shutdown from PowerShell:

```powershell
wsl --shutdown
```

---

# Common terminal layout

A useful simulation session usually uses four terminals:

| Terminal | Purpose | Main command |
|---|---|---|
| 1 | RViz model viewer | `ros2 launch buddy_description view_model.launch.py` |
| 2 | Gazebo simulation | `ros2 launch buddy_simulation gazebo_lab.launch.py` |
| 3 | Keyboard teleop | `ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/cmd_vel` |
| 4 | Debugging and topic checks | `ros2 topic list`, `ros2 topic echo`, `ros2 topic hz` |

You do not always need all four. For example, if you are only editing the robot model, RViz may be enough. If you are testing driving, Gazebo plus teleop plus topic inspection is more useful.

---

# In-depth explanation of each repeated step

## 1. Opening Ubuntu from PowerShell

Command:

```powershell
wsl -d Ubuntu-24.04
```

### What it does

This starts your Ubuntu 24.04 WSL2 environment from Windows.

WSL means **Windows Subsystem for Linux**. It lets you run a Linux terminal inside Windows. ROS 2 and Gazebo are much easier to run in Linux than directly in Windows, so Ubuntu is your main robot development environment.

### Command syntax

```text
wsl      = Windows command for starting/managing WSL
-d       = choose a specific installed Linux distribution
Ubuntu-24.04 = the name of your Ubuntu distribution
```

### How to know you are in Ubuntu

Ubuntu/Linux prompt:

```bash
venti@Antonio-PC:~$
```

PowerShell prompt:

```powershell
PS C:\Users\venti>
```

Run Linux commands only from the Ubuntu prompt.

---

## 2. Going to the workspace

Command:

```bash
cd ~/robot_ws
```

### What it does

`cd` means **change directory**. This moves your terminal into your ROS workspace folder.

Your workspace is where ROS packages, launch files, URDF/Xacro files, simulation worlds, tools, and build outputs live.

### Command syntax

```text
cd          = change directory
~           = your Linux home folder, usually /home/venti
~/robot_ws  = /home/venti/robot_ws
```

### Why it matters

Many commands should be run from the workspace root, especially:

```bash
colcon build --symlink-install
rosdep install --from-paths src --ignore-src -r -y
python3 tools/torque_sweep.py
```

If you run workspace commands from the wrong folder, ROS may not find your packages or tools.

---

## 3. Sourcing ROS and workspace setup files

Commands:

```bash
source /opt/ros/jazzy/setup.bash
source ~/robot_ws/install/setup.bash
```

### What `source` means

`source` runs a shell script inside your current terminal session.

That is different from running a normal program. A normal program starts, does something, and exits. A sourced setup file changes your current terminal environment.

### What the ROS setup file does

```bash
source /opt/ros/jazzy/setup.bash
```

This teaches the terminal where ROS 2 Jazzy is installed.

It sets environment variables such as:

```text
ROS_DISTRO
AMENT_PREFIX_PATH
COLCON_PREFIX_PATH
PATH
PYTHONPATH
LD_LIBRARY_PATH
```

You do not need to memorize all of these now. The important idea is that sourcing ROS lets commands like this work:

```bash
ros2 topic list
ros2 launch ...
ros2 run ...
```

### What the workspace setup file does

```bash
source ~/robot_ws/install/setup.bash
```

This teaches the terminal about your own packages that were built into:

```text
~/robot_ws/install
```

Without this, ROS may know about system packages like `rviz2`, but not your custom packages such as:

```text
buddy_description
buddy_simulation
```

### Why source both files?

The first setup file loads the ROS installation.

The second setup file loads your robot workspace on top of ROS.

Think of it like this:

```text
Ubuntu terminal
  -> source ROS 2 Jazzy
    -> source Buddy robot workspace
      -> run Buddy launch files
```

### Why add these to `.bashrc`?

Your `~/.bashrc` file runs automatically whenever you open a new Ubuntu terminal.

If you add these lines:

```bash
source /opt/ros/jazzy/setup.bash
source ~/robot_ws/install/setup.bash
```

to `~/.bashrc`, then new terminals will already know about ROS and your workspace.

Still, manually running `source ...` again is safe.

---

## 4. Checking ROS and workspace state

Commands:

```bash
echo $ROS_DISTRO
ros2 pkg list | grep buddy
```

### `echo $ROS_DISTRO`

`echo` prints text.

`$ROS_DISTRO` is an environment variable.

Command:

```bash
echo $ROS_DISTRO
```

Expected output:

```text
jazzy
```

This confirms your terminal knows which ROS distribution is active.

### `ros2 pkg list | grep buddy`

Command:

```bash
ros2 pkg list | grep buddy
```

This lists ROS packages, then filters the list to only show package names containing `buddy`.

Command parts:

```text
ros2 pkg list = list all ROS 2 packages visible to this terminal
|             = pipe output from one command into another command
grep buddy    = only show lines containing the word buddy
```

If this command prints nothing, likely causes are:

1. You did not build the workspace yet.
2. You did not source `~/robot_ws/install/setup.bash`.
3. The workspace is not located where you think it is.
4. The package names are different than expected.

---

## 5. Rebuilding the workspace

Commands:

```bash
colcon build --symlink-install
source install/setup.bash
```

### What `colcon build` does

`colcon` is the standard build tool for ROS 2 workspaces.

When you run:

```bash
colcon build --symlink-install
```

it looks in your workspace's `src/` folder, finds ROS packages, and builds them.

The build creates or updates these folders:

```text
build/
install/
log/
```

### What `--symlink-install` means

`--symlink-install` makes development easier by linking some installed files back to the source files.

This can make changes to Python files, launch files, config files, and resources show up without needing a full rebuild every time.

For C++ code, package metadata, and some structural changes, rebuilding is still required.

### When to rebuild

Rebuild after changing:

```text
package.xml
CMakeLists.txt
setup.py
launch files
URDF/Xacro files if they are installed as package resources
Python nodes
C++ nodes
config files
world/model files that are installed by the package
```

When in doubt, rebuild. It is slower, but safer.

### Why source after building?

After building, the workspace setup file may have changed. Running:

```bash
source install/setup.bash
```

reloads the newest workspace environment into your current terminal.

---

## 6. Launching RViz

Command:

```bash
ros2 launch buddy_description view_model.launch.py
```

### What RViz is

RViz is a ROS visualization tool. It does not simulate physics. It shows robot models, coordinate frames, transforms, sensor data, maps, paths, and markers.

Use RViz to inspect:

```text
robot shape
link positions
joint positions
TF frame tree
LiDAR frame
camera frame
IMU frame
odom/map frames later
```

### What `ros2 launch` means

`ros2 launch` starts one or more ROS nodes using a launch file.

Command parts:

```text
ros2 launch          = run a ROS 2 launch file
buddy_description    = package containing the launch file
view_model.launch.py = launch file name
```

### What probably starts in this launch file

A typical model-view launch starts things like:

```text
robot_state_publisher
joint_state_publisher_gui
rviz2
```

`robot_state_publisher` reads the robot description and publishes transforms.

`joint_state_publisher_gui` lets you move joints in a GUI if joints exist.

`rviz2` opens the visualization window.

### When to use this

Use RViz first when you change geometry. Before worrying about Gazebo physics, confirm the model looks right.

---

## 7. Launching Gazebo

Command:

```bash
ros2 launch buddy_simulation gazebo_lab.launch.py
```

### What Gazebo is

Gazebo is the simulator. It can simulate physics, gravity, collisions, joints, sensors, and robot motion.

Use Gazebo to test:

```text
whether the robot spawns
whether wheels contact the ground
whether /cmd_vel moves the robot
whether /odom is published
whether simulated /scan exists
whether the model behaves roughly as expected
```

### Command parts

```text
ros2 launch             = run a ROS 2 launch file
buddy_simulation        = package containing simulation files
gazebo_lab.launch.py    = launch file that starts Gazebo and spawns the robot
```

### Why Gazebo is separate from RViz

RViz visualizes ROS data.

Gazebo simulates a world.

They can be used together, but they do different jobs:

```text
Gazebo = simulated physics world
RViz   = ROS data and robot-state viewer
```

---

## 8. Opening multiple Ubuntu terminals

You will often need multiple terminals because one ROS command can keep running until you stop it.

For example, Gazebo keeps running in one terminal. Teleop needs another terminal. Topic inspection needs a third terminal.

### Windows Terminal method

Click the small dropdown next to the `+` button and choose:

```text
Ubuntu-24.04
```

### PowerShell method

Open another PowerShell window and run:

```powershell
wsl -d Ubuntu-24.04
```

### Start Menu method

Open:

```text
Ubuntu 24.04
```

from the Windows Start Menu.

---

## 9. Running keyboard teleop

Command:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/cmd_vel
```

### What teleop does

`teleop_twist_keyboard` lets you drive the robot with your keyboard.

It publishes velocity commands.

The robot or simulator listens to those velocity commands and moves.

### Command parts

```text
ros2 run                = run one executable from one ROS package
teleop_twist_keyboard   = package name
teleop_twist_keyboard   = executable name
--ros-args              = everything after this is a ROS-specific argument
-r                      = remap a ROS name
cmd_vel:=/cmd_vel       = publish to /cmd_vel instead of a default relative topic
```

### What `/cmd_vel` is

`/cmd_vel` is the standard velocity command topic for mobile robots.

It usually uses this message type:

```text
geometry_msgs/msg/Twist
```

That message contains:

```text
linear velocity
angular velocity
```

For a differential-drive robot:

```text
linear.x  = forward/backward speed
angular.z = turning speed
```

### Why the terminal must stay focused

Keyboard teleop reads key presses from the terminal window. If you click another window, the teleop node will not receive your keyboard input.

---

## 10. Inspecting topics

Command:

```bash
ros2 topic list
```

### What it does

This lists active ROS topics.

A topic is a named stream of messages. Examples:

```text
/cmd_vel
/odom
/scan
/tf
/tf_static
```

### Useful topic commands

Print one odometry message:

```bash
ros2 topic echo /odom --once
```

Print one LiDAR scan message:

```bash
ros2 topic echo /scan --once
```

Measure odometry rate:

```bash
ros2 topic hz /odom
```

Measure LiDAR scan rate:

```bash
ros2 topic hz /scan
```

### Command syntax

```text
ros2 topic echo /topic_name --once
```

means:

```text
subscribe to /topic_name
print one message
exit
```

```text
ros2 topic hz /topic_name
```

means:

```text
subscribe to /topic_name
measure how many messages per second arrive
keep running until Ctrl+C
```

---

## 11. Running torque sweeps

Command:

```bash
python3 tools/torque_sweep.py \
  --mass-kg 30 \
  --wheel-radius-m 0.06 \
  --driven-wheels 4 \
  --speed-mps 1.5 \
  --ramp-deg 20
```

### What this does

This runs your torque calculation script.

It estimates wheel RPM and torque requirements based on robot mass, wheel radius, number of driven wheels, speed, ramp angle, efficiency, rolling resistance, and safety factor.

### Why it does not need ROS

This is just a Python calculation. It does not need RViz, Gazebo, or ROS topics.

You can run it any time.

### Command syntax

```text
python3                 = run Python 3
 tools/torque_sweep.py  = script path
 --mass-kg 30           = robot mass assumption
 --wheel-radius-m 0.06  = wheel radius in meters
 --driven-wheels 4      = number of wheels/motor outputs sharing traction
 --speed-mps 1.5        = target speed in meters per second
 --ramp-deg 20          = ramp angle in degrees
```

The backslash character:

```bash
\
```

means the command continues on the next line.

This:

```bash
python3 tools/torque_sweep.py \
  --mass-kg 30
```

is equivalent to:

```bash
python3 tools/torque_sweep.py --mass-kg 30
```

The multi-line version is just easier to read.

---

## 12. Stopping programs

Command/key combo:

```text
Ctrl+C
```

### What it does

`Ctrl+C` sends an interrupt signal to the currently running program in that terminal.

Use it to stop:

```text
RViz launch
Gazebo launch
teleop
ros2 topic echo
ros2 topic hz
```

### Why not just close the terminal?

Closing the terminal often works, but `Ctrl+C` is cleaner. It gives ROS nodes a chance to shut down properly.

---

## 13. Exiting Ubuntu and shutting down WSL

Exit a terminal:

```bash
exit
```

Fully shut down WSL from PowerShell:

```powershell
wsl --shutdown
```

### What `exit` does

`exit` closes the current Ubuntu shell session.

### What `wsl --shutdown` does

This stops all running WSL distributions. Use it if you want to fully shut down the Linux environment, free memory, or reset a stuck WSL session.

Do not run `wsl --shutdown` while you still need Gazebo, RViz, or ROS nodes running.

---

# Minimal daily routine

Use this when everything is already installed and built.

Terminal 1:

```powershell
wsl -d Ubuntu-24.04
```

Then inside Ubuntu:

```bash
cd ~/robot_ws
source /opt/ros/jazzy/setup.bash
source ~/robot_ws/install/setup.bash
ros2 launch buddy_description view_model.launch.py
```

Terminal 2:

```powershell
wsl -d Ubuntu-24.04
```

Then inside Ubuntu:

```bash
cd ~/robot_ws
source /opt/ros/jazzy/setup.bash
source ~/robot_ws/install/setup.bash
ros2 launch buddy_simulation gazebo_lab.launch.py
```

Terminal 3:

```powershell
wsl -d Ubuntu-24.04
```

Then inside Ubuntu:

```bash
source /opt/ros/jazzy/setup.bash
source ~/robot_ws/install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/cmd_vel
```

Terminal 4, optional debug terminal:

```powershell
wsl -d Ubuntu-24.04
```

Then inside Ubuntu:

```bash
source /opt/ros/jazzy/setup.bash
source ~/robot_ws/install/setup.bash
ros2 topic list
ros2 topic echo /odom --once
ros2 topic echo /scan --once
```

---

# Minimal rebuild routine after editing robot files

Use this when you changed robot files and want to test again.

```bash
cd ~/robot_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
ros2 launch buddy_description view_model.launch.py
```

Then launch Gazebo and teleop in separate terminals if the model looks correct.

---

# Files you are most likely editing during simulation work

Focus on these first:

```text
src/buddy_description/urdf/buddy.urdf.xacro
src/buddy_simulation/models/buddy_v0_1/model.sdf
src/buddy_simulation/worlds/empty_lab.sdf
tools/torque_sweep.py
```

Avoid changing many files at once. Change one thing, rebuild, relaunch, and confirm the result.
