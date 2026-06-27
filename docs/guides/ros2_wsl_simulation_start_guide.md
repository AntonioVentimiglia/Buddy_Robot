# Buddy Robot: WSL2, ROS 2 Jazzy, Gazebo, and Simulation Startup Guide

This guide starts from opening PowerShell on Windows and ends with running the current `robot_ws` simulation tools:

1. Install and open Ubuntu 24.04 through WSL2.
2. Install ROS 2 Jazzy and Gazebo/ROS integration.
3. Move the patched `robot_ws` into the Ubuntu filesystem.
4. Build the workspace.
5. Run the ROS talker/listener test.
6. View the Buddy robot model in RViz.
7. Launch the Buddy Gazebo simulation.
8. Drive the simulated robot with keyboard teleop.
9. Inspect `/cmd_vel`, `/odom`, `/scan`, and `/tf`.
10. Run torque requirement sweeps.

The goal is not to learn every part of ROS at once. The goal is to get a repeatable loop:

```text
edit model -> build workspace -> view model -> run Gazebo -> drive robot -> check topics -> run torque sweep
```

---

## Part 1 - Fast command sequence

Use this section when you just need the commands. Explanations are in Part 2.

---

### 1. Open PowerShell as Administrator

On Windows:

1. Press the Windows key.
2. Search `PowerShell`.
3. Right-click `Windows PowerShell`.
4. Choose `Run as administrator`.

The prompt will look like:

```powershell
PS C:\Users\venti>
```

---

### 2. Enable or update WSL from PowerShell

Run these in PowerShell:

```powershell
wsl --update
wsl --set-default-version 2
wsl --list --verbose
```

If Ubuntu 24.04 is not installed, run:

```powershell
wsl --install -d Ubuntu-24.04
```

If an old broken Ubuntu 24.04 install exists and you have no important files inside it yet, reset it:

```powershell
wsl --unregister Ubuntu-24.04
wsl --install -d Ubuntu-24.04
```

Warning: `wsl --unregister Ubuntu-24.04` deletes that Ubuntu installation.

---

### 3. Open Ubuntu

Option A: From PowerShell:

```powershell
wsl -d Ubuntu-24.04
```

Option B: From the Windows Start Menu:

```text
Ubuntu 24.04
```

When you are inside Ubuntu, your prompt should look similar to:

```bash
venti@Antonio-PC:~$
```

or sometimes:

```bash
venti@Antonio-PC:/mnt/c/WINDOWS/system32$
```

If you see `PS C:\Users\venti>`, you are still in PowerShell, not Ubuntu.

---

### 4. Move to your Ubuntu home folder

Run this inside Ubuntu:

```bash
cd ~
pwd
```

Expected output:

```text
/home/venti
```

---

### 5. Update Ubuntu and install basic tools

Run:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl wget unzip build-essential python3-pip software-properties-common
```

---

### 6. Add ROS 2 package repository

Run:

```bash
sudo add-apt-repository universe -y
sudo apt update
sudo apt install -y curl gnupg lsb-release
```

Add the ROS package signing key:

```bash
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
```

Add the ROS 2 apt repository:

```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

---

### 7. Install ROS 2 Jazzy

Run:

```bash
sudo apt update
sudo apt install -y ros-jazzy-desktop
```

Set ROS 2 Jazzy to load automatically in new Ubuntu terminals:

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

Check ROS environment:

```bash
echo $ROS_DISTRO
which ros2
ros2 pkg list | sed -n '1,10p'
```

Expected:

```text
jazzy
/opt/ros/jazzy/bin/ros2
```

---

### 8. Install ROS build tools, Gazebo integration, and robot visualization tools

Run:

```bash
sudo apt install -y \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-vcstool \
  ros-jazzy-xacro \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-joint-state-publisher-gui \
  ros-jazzy-rviz2 \
  ros-jazzy-teleop-twist-keyboard \
  ros-jazzy-ros-gz
```

Initialize rosdep:

```bash
sudo rosdep init
rosdep update
```

If `sudo rosdep init` says it already exists, run only:

```bash
rosdep update
```

---

### 9. Test ROS with talker and listener

Terminal 1, inside Ubuntu:

```bash
ros2 run demo_nodes_cpp talker
```

Open a second Ubuntu terminal.

Terminal 2:

```bash
source ~/.bashrc
ros2 run demo_nodes_py listener
```

Expected result:

Terminal 1 prints:

```text
Publishing: 'Hello World: 1'
Publishing: 'Hello World: 2'
```

Terminal 2 prints:

```text
I heard: [Hello World: 1]
I heard: [Hello World: 2]
```

Stop both programs with:

```text
Ctrl+C
```

---

### 10. Move `robot_ws` into Ubuntu

Do not build from `/mnt/c/...`. Copy the workspace into your Ubuntu home directory.

If the zip is in Windows Downloads and is named `buddy_sim_start_ws.zip`:

```bash
cd ~
cp /mnt/c/Users/venti/Downloads/buddy_sim_start_ws.zip ~/
unzip buddy_sim_start_ws.zip
mv buddy_sim_start_ws robot_ws
```

If the zip is named `robot_ws.zip`:

```bash
cd ~
cp /mnt/c/Users/venti/Downloads/robot_ws.zip ~/
unzip robot_ws.zip
```

If the folder is already named `robot_ws` in Windows Downloads:

```bash
cd ~
cp -r /mnt/c/Users/venti/Downloads/robot_ws ~/robot_ws
```

Now check the workspace:

```bash
cd ~/robot_ws
ls
```

You should see something like:

```text
src  tools
```

---

### 11. Build `robot_ws`

Run:

```bash
cd ~/robot_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

Make the workspace load automatically in new Ubuntu terminals:

```bash
echo "source ~/robot_ws/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

Check that ROS can see the Buddy packages:

```bash
ros2 pkg list | grep buddy
```

---

### 12. Run Simulation 1: RViz robot model view

Run:

```bash
ros2 launch buddy_description view_model.launch.py
```

Expected result:

```text
RViz opens.
The Buddy robot model appears.
The base, wheels, lidar frame, camera frame, and IMU frame are visible.
```

If RViz opens but the robot is not visible, change the RViz fixed frame to:

```text
base_link
```

or:

```text
base_footprint
```

---

### 13. Run Simulation 2: Gazebo lab simulation

Open a new Ubuntu terminal.

Run:

```bash
cd ~/robot_ws
source ~/.bashrc
ros2 launch buddy_simulation gazebo_lab.launch.py
```

Expected result:

```text
Gazebo opens.
An empty lab world loads.
The Buddy robot spawns in the world.
```

---

### 14. Drive the robot with keyboard teleop

Open another Ubuntu terminal.

Run:

```bash
source ~/.bashrc
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/cmd_vel
```

Use the keyboard instructions shown by `teleop_twist_keyboard` to drive.

Common keys usually include:

```text
i = forward
, = backward
j = turn left
l = turn right
k = stop
```

---

### 15. Inspect the running ROS topics

Open another Ubuntu terminal while Gazebo is running.

Run:

```bash
source ~/.bashrc
ros2 topic list
```

Look for topics such as:

```text
/cmd_vel
/odom
/scan
/tf
/tf_static
```

Check odometry once:

```bash
ros2 topic echo /odom --once
```

Check lidar once:

```bash
ros2 topic echo /scan --once
```

Check topic rates:

```bash
ros2 topic hz /odom
```

Stop rate checking with:

```text
Ctrl+C
```

---

### 16. Run torque sweep calculations

From the workspace root:

```bash
cd ~/robot_ws
python3 tools/torque_sweep.py \
  --mass-kg 30 \
  --wheel-radius-m 0.06 \
  --driven-wheels 4 \
  --speed-mps 1.5 \
  --ramp-deg 20
```

Run a safer early-prototype comparison:

```bash
python3 tools/torque_sweep.py \
  --mass-kg 20 \
  --wheel-radius-m 0.06 \
  --driven-wheels 4 \
  --speed-mps 0.5 \
  --ramp-deg 5
```

---

### 17. Normal edit/build/run loop

After editing the robot model:

```bash
cd ~/robot_ws
colcon build --symlink-install
source install/setup.bash
ros2 launch buddy_description view_model.launch.py
```

For Gazebo:

```bash
ros2 launch buddy_simulation gazebo_lab.launch.py
```

---

## Part 2 - Command explanations

This section explains what each command does, why it matters, and basic shell syntax.

---

## 1. PowerShell vs Ubuntu terminal

You are using two different command environments:

```text
PowerShell prompt:
PS C:\Users\venti>

Ubuntu/bash prompt:
venti@Antonio-PC:~$
```

They are not the same.

PowerShell is Windows. Use it for WSL management commands such as:

```powershell
wsl --install -d Ubuntu-24.04
wsl --list --verbose
wsl -d Ubuntu-24.04
```

Ubuntu/bash is Linux. Use it for ROS commands such as:

```bash
sudo apt update
ros2 topic list
colcon build --symlink-install
```

If a command begins with `sudo`, `apt`, `ros2`, `colcon`, or `source`, it usually belongs inside Ubuntu, not PowerShell.

---

## 2. WSL commands

### `wsl --update`

```powershell
wsl --update
```

Updates the Windows Subsystem for Linux engine. WSL is the compatibility layer that lets Ubuntu run inside Windows.

Why it matters:

- Newer WSL versions improve Linux GUI support.
- ROS tools like RViz and Gazebo need graphical support.
- Updating WSL avoids many strange install and display issues.

---

### `wsl --set-default-version 2`

```powershell
wsl --set-default-version 2
```

Tells Windows that new Linux distributions should use WSL2 instead of WSL1.

Why WSL2 matters:

- WSL2 runs a real Linux kernel inside a lightweight virtual machine.
- ROS 2 and Gazebo behave much more like normal Linux inside WSL2.
- WSL1 is not appropriate for this simulation workflow.

---

### `wsl --install -d Ubuntu-24.04`

```powershell
wsl --install -d Ubuntu-24.04
```

Installs the Ubuntu 24.04 Linux distribution through WSL.

Syntax notes:

- `wsl` is the command.
- `--install` is an option meaning install a distribution.
- `-d Ubuntu-24.04` means choose the distribution named `Ubuntu-24.04`.

---

### `wsl -d Ubuntu-24.04`

```powershell
wsl -d Ubuntu-24.04
```

Starts Ubuntu 24.04 from PowerShell.

Use this when you are in PowerShell and want to enter Linux.

---

## 3. Basic Linux navigation

### `cd ~`

```bash
cd ~
```

Changes your current directory to your Ubuntu home folder.

For your user, that is usually:

```text
/home/venti
```

Syntax notes:

- `cd` means change directory.
- `~` is shorthand for your home directory.

Why it matters:

When you first opened Ubuntu, you were in:

```text
/mnt/c/WINDOWS/system32
```

That is a Windows system path mounted into Linux. You do not want to build ROS workspaces there.

---

### `pwd`

```bash
pwd
```

Prints the current working directory.

Use it to confirm where you are.

Example output:

```text
/home/venti
```

---

### `ls`

```bash
ls
```

Lists files and folders in the current directory.

Example:

```bash
cd ~/robot_ws
ls
```

Expected output:

```text
src  tools
```

---

## 4. Ubuntu package management

Ubuntu uses `apt` to install software.

---

### `sudo`

```bash
sudo apt update
```

`sudo` means run the command as administrator/root.

Why it matters:

Installing system packages modifies protected system folders. Ubuntu requires administrator permission.

When you use `sudo`, Ubuntu may ask for your password. The password will not visibly type on screen. That is normal.

---

### `apt update`

```bash
sudo apt update
```

Downloads the latest package lists from configured software repositories.

It does not upgrade software by itself. It refreshes Ubuntu's knowledge of what packages and versions are available.

---

### `apt upgrade -y`

```bash
sudo apt upgrade -y
```

Installs available updates for packages already on your system.

Syntax notes:

- `upgrade` means upgrade installed packages.
- `-y` automatically answers yes to prompts.

---

### `&&`

```bash
sudo apt update && sudo apt upgrade -y
```

`&&` means run the second command only if the first command succeeds.

This is common in Linux shells.

Important:

- `&&` works in Ubuntu/bash.
- It may not work in older Windows PowerShell versions the same way.

---

### `apt install -y ...`

```bash
sudo apt install -y git curl wget unzip build-essential python3-pip software-properties-common
```

Installs packages.

The packages here are:

- `git`: version control.
- `curl`: downloads data from URLs.
- `wget`: another download tool.
- `unzip`: extracts zip files.
- `build-essential`: compilers and basic build tools.
- `python3-pip`: Python package installer.
- `software-properties-common`: tools for managing software repositories.

---

## 5. Adding the ROS package repository

Ubuntu does not include ROS 2 packages by default. You add the ROS repository so `apt` can install ROS.

---

### `sudo add-apt-repository universe -y`

```bash
sudo add-apt-repository universe -y
```

Enables Ubuntu's `universe` repository.

Why it matters:

ROS depends on packages that may live in the `universe` repository.

---

### Downloading the ROS key

```bash
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
```

This downloads the ROS package signing key.

Why it matters:

Ubuntu uses package signing keys to verify that packages come from a trusted source.

Syntax notes:

- `curl` downloads from the internet.
- `-sSL` means silent mode, follow redirects, and show errors when needed.
- `-o file` writes the output to a file.
- The backslash `\` at the end of the line means the command continues on the next line.

---

### Adding the ROS apt source

```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

This creates a file that tells Ubuntu where to download ROS packages.

Important pieces:

- `echo "..."` prints text.
- `$(dpkg --print-architecture)` inserts your system architecture, such as `amd64`.
- `$(. /etc/os-release && echo $UBUNTU_CODENAME)` inserts your Ubuntu codename, such as `noble` for Ubuntu 24.04.
- `|` is a pipe. It sends output from the command on the left into the command on the right.
- `tee file` writes input into a file.
- `sudo tee ...` is used because the destination is a protected system directory.
- `> /dev/null` hides duplicate output.

---

## 6. Installing and sourcing ROS

### `sudo apt install -y ros-jazzy-desktop`

```bash
sudo apt install -y ros-jazzy-desktop
```

Installs the ROS 2 Jazzy desktop package.

This includes important tools such as:

- ROS 2 command-line tools.
- RViz.
- common message packages.
- demo nodes.
- core ROS libraries.

---

### `source /opt/ros/jazzy/setup.bash`

```bash
source /opt/ros/jazzy/setup.bash
```

Loads the ROS 2 environment into the current terminal.

Why it matters:

Without sourcing the setup file, your terminal may not know where `ros2`, ROS packages, message definitions, and launch files are.

---

### `echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc`

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
```

Adds the ROS source command to your `.bashrc` file.

What `.bashrc` does:

`.bashrc` runs automatically whenever you open a new Ubuntu terminal.

Syntax notes:

- `echo "text"` prints text.
- `>>` appends text to a file.
- `~/.bashrc` is the bash startup file in your home folder.

Why it matters:

After this, new Ubuntu terminals automatically know about ROS 2.

---

### `echo $ROS_DISTRO`

```bash
echo $ROS_DISTRO
```

Prints the currently loaded ROS distribution name.

Expected:

```text
jazzy
```

Syntax notes:

- `$ROS_DISTRO` is an environment variable.
- Environment variables are named values stored in your shell session.

---

### `which ros2`

```bash
which ros2
```

Shows the path to the `ros2` executable.

Expected:

```text
/opt/ros/jazzy/bin/ros2
```

---

### Why `ros2 --version` failed

You tried:

```bash
ros2 --version
```

That failed because this ROS 2 CLI does not accept `--version` as a top-level argument.

That does not mean ROS is broken.

Use these instead:

```bash
echo $ROS_DISTRO
which ros2
ros2 pkg list | sed -n '1,10p'
```

---

## 7. Installing build and simulation tools

### `python3-colcon-common-extensions`

```bash
sudo apt install -y python3-colcon-common-extensions
```

Installs `colcon`, the common ROS 2 workspace build tool.

You use it to build packages inside `robot_ws/src`.

---

### `python3-rosdep`

```bash
sudo apt install -y python3-rosdep
```

Installs `rosdep`, which checks your ROS packages and installs missing system dependencies.

Example:

```bash
rosdep install --from-paths src --ignore-src -r -y
```

---

### `ros-jazzy-xacro`

```bash
sudo apt install -y ros-jazzy-xacro
```

Installs Xacro processing.

Xacro is a macro language used to generate URDF robot description files.

Why it matters:

Your robot model likely lives in a file like:

```text
src/buddy_description/urdf/buddy.urdf.xacro
```

---

### `ros-jazzy-robot-state-publisher`

```bash
sudo apt install -y ros-jazzy-robot-state-publisher
```

Installs the node that publishes robot transforms from the URDF model.

Why it matters:

RViz and other ROS tools need to know where each robot part is relative to every other part.

---

### `ros-jazzy-joint-state-publisher-gui`

```bash
sudo apt install -y ros-jazzy-joint-state-publisher-gui
```

Installs a GUI tool that can publish fake or manual joint states.

Why it matters:

For early modeling, it helps you view wheel and joint frames before real hardware exists.

---

### `ros-jazzy-rviz2`

```bash
sudo apt install -y ros-jazzy-rviz2
```

Installs RViz, the main ROS visualization tool.

Use RViz to see:

- robot model
- frames
- lidar scans
- odometry
- maps
- navigation costmaps

---

### `ros-jazzy-teleop-twist-keyboard`

```bash
sudo apt install -y ros-jazzy-teleop-twist-keyboard
```

Installs a keyboard control tool that publishes velocity commands.

It sends messages to a topic like:

```text
/cmd_vel
```

---

### `ros-jazzy-ros-gz`

```bash
sudo apt install -y ros-jazzy-ros-gz
```

Installs ROS-Gazebo integration packages.

Why it matters:

Gazebo and ROS are separate systems. `ros_gz` lets them communicate.

---

## 8. rosdep initialization

### `sudo rosdep init`

```bash
sudo rosdep init
```

Initializes rosdep system-wide by creating configuration files.

Usually this only needs to be done once.

If it says the file already exists, that is okay.

---

### `rosdep update`

```bash
rosdep update
```

Downloads dependency rules used by rosdep.

Why it matters:

Without updated rosdep rules, dependency installation may fail or miss packages.

---

## 9. ROS talker/listener test

### `ros2 run demo_nodes_cpp talker`

```bash
ros2 run demo_nodes_cpp talker
```

Runs a demo ROS node called `talker` from the package `demo_nodes_cpp`.

Syntax:

```text
ros2 run <package_name> <executable_name>
```

What it does:

- Starts a node.
- Publishes repeated `Hello World` messages.
- Uses a ROS topic.

---

### `ros2 run demo_nodes_py listener`

```bash
ros2 run demo_nodes_py listener
```

Runs a demo ROS node called `listener` from the package `demo_nodes_py`.

What it does:

- Subscribes to the messages from the talker.
- Prints what it receives.

Why this test matters:

If talker and listener work, ROS 2 communication is functioning.

---

### Opening a second Ubuntu terminal

Use one of these:

1. Windows Terminal: click the `+` button.
2. Dropdown next to `+`: choose `Ubuntu-24.04`.
3. Start Menu: open `Ubuntu 24.04`.
4. PowerShell: run `wsl -d Ubuntu-24.04`.

---

## 10. Windows paths vs Ubuntu paths

WSL lets Ubuntu access Windows files through `/mnt/c`.

Example:

```text
/mnt/c/Users/venti/Downloads
```

This corresponds to Windows:

```text
C:\Users\venti\Downloads
```

For copying files, `/mnt/c` is fine.

For building ROS workspaces, avoid `/mnt/c`.

Use this instead:

```text
/home/venti/robot_ws
```

Reason:

- Linux file performance is much better inside the WSL Linux filesystem.
- ROS builds create many small files.
- Building under `/mnt/c` can be slow and can cause odd permission/path behavior.

---

## 11. Copying and unzipping the workspace

### `cp`

```bash
cp /mnt/c/Users/venti/Downloads/buddy_sim_start_ws.zip ~/
```

Copies a file.

Syntax:

```text
cp <source> <destination>
```

Here:

- source is the zip file in Windows Downloads.
- destination is your Ubuntu home folder.

---

### `cp -r`

```bash
cp -r /mnt/c/Users/venti/Downloads/robot_ws ~/robot_ws
```

Copies a folder recursively.

Syntax notes:

- `-r` means recursive.
- Recursive copy is needed for folders.

---

### `unzip`

```bash
unzip buddy_sim_start_ws.zip
```

Extracts a zip file into the current directory.

---

### `mv`

```bash
mv buddy_sim_start_ws robot_ws
```

Renames or moves a file/folder.

Syntax:

```text
mv <old_name> <new_name>
```

Here, it renames the extracted folder to `robot_ws`.

---

## 12. ROS workspace structure

A ROS 2 workspace typically looks like:

```text
robot_ws/
  src/
    buddy_description/
    buddy_simulation/
    ...
  tools/
    torque_sweep.py
```

The key folder is:

```text
robot_ws/src
```

ROS packages live inside `src`.

---

## 13. Installing workspace dependencies

### `rosdep install --from-paths src --ignore-src -r -y`

```bash
rosdep install --from-paths src --ignore-src -r -y
```

Installs missing system dependencies for packages in `src`.

Meaning:

- `rosdep install`: install dependencies.
- `--from-paths src`: inspect packages under `src`.
- `--ignore-src`: do not try to install packages that are already in your workspace source folder.
- `-r`: continue even if some dependencies fail.
- `-y`: automatically answer yes.

---

## 14. Building the workspace

### `colcon build --symlink-install`

```bash
colcon build --symlink-install
```

Builds all ROS 2 packages in the workspace.

Why `--symlink-install` matters:

It creates symbolic links for certain files instead of copying them. This is useful during development because changes to launch files, config files, and Python files may be picked up without a full rebuild.

After building, the workspace has folders like:

```text
build/
install/
log/
```

Do not manually edit files in `build/` or `install/`. Edit source files in `src/`.

---

### `source install/setup.bash`

```bash
source install/setup.bash
```

Loads your newly built workspace into the current terminal.

Why it matters:

Before this command, ROS knows about system packages like `rviz2`.

After this command, ROS also knows about your workspace packages like:

```text
buddy_description
buddy_simulation
```

---

### `echo "source ~/robot_ws/install/setup.bash" >> ~/.bashrc`

```bash
echo "source ~/robot_ws/install/setup.bash" >> ~/.bashrc
```

Makes new terminals automatically load your workspace.

Important:

The order matters inside `.bashrc`:

```bash
source /opt/ros/jazzy/setup.bash
source ~/robot_ws/install/setup.bash
```

ROS itself should be sourced first. Your workspace should be sourced second.

---

## 15. Finding packages

### `ros2 pkg list | grep buddy`

```bash
ros2 pkg list | grep buddy
```

Lists ROS packages and filters for names containing `buddy`.

Syntax notes:

- `ros2 pkg list` prints all known packages.
- `|` sends output into another command.
- `grep buddy` keeps only lines containing `buddy`.

If no Buddy packages appear, likely causes are:

1. You did not build the workspace.
2. You did not source `install/setup.bash`.
3. Your workspace folder structure is wrong.

---

## 16. Launching the RViz robot model

### `ros2 launch buddy_description view_model.launch.py`

```bash
ros2 launch buddy_description view_model.launch.py
```

Launches a ROS launch file.

Syntax:

```text
ros2 launch <package_name> <launch_file_name>
```

What this should do:

- Process the Buddy Xacro/URDF robot model.
- Start `robot_state_publisher`.
- Start joint state tools if configured.
- Open RViz.
- Show the robot frames and model.

Why this matters:

Before physics simulation, you must verify that the robot model exists and its frames are reasonable.

---

## 17. Launching Gazebo simulation

### `ros2 launch buddy_simulation gazebo_lab.launch.py`

```bash
ros2 launch buddy_simulation gazebo_lab.launch.py
```

Launches the Gazebo simulation for the Buddy robot.

Expected responsibilities of this launch file:

- Start Gazebo.
- Load the simulation world.
- Spawn the Buddy robot model.
- Connect simulated robot motion and sensors to ROS topics.

Why this matters:

Gazebo lets you test robot geometry, wheel placement, lidar placement, `/cmd_vel`, `/odom`, and `/scan` before hardware exists.

---

## 18. Keyboard teleop

### `ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/cmd_vel`

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/cmd_vel
```

Runs a keyboard teleoperation node.

It publishes velocity commands.

Important pieces:

```text
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Runs the executable.

```text
--ros-args
```

Means the following arguments are ROS-specific arguments.

```text
-r cmd_vel:=/cmd_vel
```

Remaps a topic name.

Remapping means:

```text
Use /cmd_vel as the output topic instead of the node's default name.
```

Why this matters:

Robot base controllers usually listen for motion commands on `/cmd_vel`.

---

## 19. ROS topics

### What is a topic?

A topic is a named communication channel in ROS.

Examples:

```text
/cmd_vel  - velocity commands
/odom     - odometry estimate
/scan     - lidar scan
/tf       - coordinate transforms
```

Nodes publish and subscribe to topics.

---

### `ros2 topic list`

```bash
ros2 topic list
```

Lists active ROS topics.

Use it to verify that Gazebo and the robot are publishing the expected data.

---

### `ros2 topic echo /odom --once`

```bash
ros2 topic echo /odom --once
```

Prints one message from the `/odom` topic.

Syntax notes:

- `echo` means print messages.
- `/odom` is the topic name.
- `--once` prints only one message, then exits.

Why it matters:

Odometry tells you where the robot thinks it is relative to its starting motion frame.

---

### `ros2 topic echo /scan --once`

```bash
ros2 topic echo /scan --once
```

Prints one lidar scan message.

Why it matters:

If `/scan` exists and contains data, your simulated 2D lidar is publishing.

---

### `ros2 topic hz /odom`

```bash
ros2 topic hz /odom
```

Measures the publishing rate of a topic.

Example output might show something like:

```text
average rate: 30.0
```

Stop it with:

```text
Ctrl+C
```

---

## 20. Torque sweep script

### Command

```bash
python3 tools/torque_sweep.py \
  --mass-kg 30 \
  --wheel-radius-m 0.06 \
  --driven-wheels 4 \
  --speed-mps 1.5 \
  --ramp-deg 20
```

This runs a Python script that estimates wheel torque and wheel RPM requirements.

Arguments:

```text
--mass-kg 30
```

Robot gross mass in kilograms. Gross mass means robot plus payload.

```text
--wheel-radius-m 0.06
```

Wheel radius in meters. A 0.06 m radius means a 0.12 m diameter wheel.

```text
--driven-wheels 4
```

Number of powered wheel outputs sharing the driving load.

```text
--speed-mps 1.5
```

Target linear speed in meters per second.

```text
--ramp-deg 20
```

Ramp angle in degrees.

Why it matters:

Motor selection depends heavily on mass, wheel radius, target speed, ramp angle, acceleration, drivetrain efficiency, and safety factor. This script gives you a first estimate before buying motors.

---

## 21. Basic syntax notes

### Backslash line continuation

This:

```bash
python3 tools/torque_sweep.py \
  --mass-kg 30 \
  --wheel-radius-m 0.06
```

is the same as:

```bash
python3 tools/torque_sweep.py --mass-kg 30 --wheel-radius-m 0.06
```

The backslash `\` lets you split a long command across multiple lines.

Do not put spaces after the backslash.

---

### Flags and options

Commands often use flags like:

```text
-y
-r
--ignore-src
--symlink-install
```

Short flags usually start with one dash:

```text
-y
```

Long flags usually start with two dashes:

```text
--symlink-install
```

---

### Environment variables

Environment variables store settings for the shell.

Example:

```bash
echo $ROS_DISTRO
```

`ROS_DISTRO` stores the ROS distribution name.

Expected:

```text
jazzy
```

---

### Pipes

A pipe sends output from one command into another command.

Example:

```bash
ros2 pkg list | grep buddy
```

Meaning:

1. `ros2 pkg list` prints all package names.
2. `grep buddy` filters for lines containing `buddy`.

---

### Redirection

`>` writes output to a file and replaces the file.

`>>` appends output to the end of a file.

Example:

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
```

This appends a line to `.bashrc`.

---

## 22. Troubleshooting

### Problem: `sudo apt ...` fails in PowerShell

You are in PowerShell instead of Ubuntu.

PowerShell prompt:

```text
PS C:\Users\venti>
```

Ubuntu prompt:

```text
venti@Antonio-PC:~$
```

Fix:

```powershell
wsl -d Ubuntu-24.04
```

Then run the `sudo apt` command inside Ubuntu.

---

### Problem: `ros2 --version` fails

This is not a useful test for this ROS install.

Use:

```bash
echo $ROS_DISTRO
which ros2
ros2 pkg list | sed -n '1,10p'
```

---

### Problem: `BrokenPipeError` after `ros2 pkg list | head`

This can happen because `head` stops reading after 10 lines while `ros2 pkg list` is still trying to print.

It is harmless.

Use this instead:

```bash
ros2 pkg list | sed -n '1,10p'
```

---

### Problem: RViz or Gazebo does not open

Try:

```powershell
wsl --update
```

from PowerShell, then restart WSL:

```powershell
wsl --shutdown
wsl -d Ubuntu-24.04
```

Then inside Ubuntu:

```bash
source ~/.bashrc
rviz2
```

If `rviz2` opens, GUI support works.

---

### Problem: `ros2 launch buddy_description view_model.launch.py` cannot find package

Check:

```bash
cd ~/robot_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 pkg list | grep buddy
```

If no Buddy package appears, rebuild:

```bash
cd ~/robot_ws
colcon build --symlink-install
source install/setup.bash
```

---

### Problem: `cd ~/robot_ws` says no such file or directory

Your workspace is not copied into Ubuntu yet.

Check Downloads:

```bash
ls /mnt/c/Users/venti/Downloads
```

Then copy the zip or folder into Ubuntu home.

---

### Problem: Build is very slow

Make sure your workspace is under:

```text
/home/venti/robot_ws
```

not:

```text
/mnt/c/Users/venti/...
```

---

## 23. What to edit first in the robot model

For now, edit only these files:

```text
src/buddy_description/urdf/buddy.urdf.xacro
src/buddy_simulation/models/buddy_v0_1/model.sdf
src/buddy_simulation/worlds/empty_lab.sdf
tools/torque_sweep.py
```

Start by changing:

```text
base_length
base_width
base_height
wheel_radius
wheel_width
wheel_x
wheel_y
mass
lidar height
camera height
camera pitch
```

After changes:

```bash
cd ~/robot_ws
colcon build --symlink-install
source install/setup.bash
ros2 launch buddy_description view_model.launch.py
```

Then test Gazebo:

```bash
ros2 launch buddy_simulation gazebo_lab.launch.py
```

---

## 24. Milestones

### Milestone 1 - ROS installed

Successful commands:

```bash
echo $ROS_DISTRO
which ros2
```

Expected:

```text
jazzy
/opt/ros/jazzy/bin/ros2
```

---

### Milestone 2 - ROS communication works

Successful test:

```bash
ros2 run demo_nodes_cpp talker
ros2 run demo_nodes_py listener
```

Expected:

```text
listener hears talker messages
```

---

### Milestone 3 - Workspace builds

Successful command:

```bash
colcon build --symlink-install
```

Expected:

```text
Summary: all packages finished
```

---

### Milestone 4 - Robot model appears

Successful command:

```bash
ros2 launch buddy_description view_model.launch.py
```

Expected:

```text
RViz opens and shows Buddy model
```

---

### Milestone 5 - Gazebo simulation runs

Successful command:

```bash
ros2 launch buddy_simulation gazebo_lab.launch.py
```

Expected:

```text
Gazebo opens and robot spawns
```

---

### Milestone 6 - Robot drives in simulation

Successful command:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/cmd_vel
```

Expected:

```text
Keyboard commands move robot in Gazebo
/odom changes when robot moves
```

---

### Milestone 7 - Torque calculations run

Successful command:

```bash
python3 tools/torque_sweep.py --mass-kg 30 --wheel-radius-m 0.06 --driven-wheels 4 --speed-mps 1.5 --ramp-deg 20
```

Expected:

```text
Script prints wheel RPM and torque estimates
```

---

## 25. Recommended next work after this guide

Once the above works, do not add Nav2 yet. First tune the base model.

Your next design loop should be:

1. Choose a wheel radius.
2. Update the Xacro/SDF model.
3. View in RViz.
4. Drive in Gazebo.
5. Run torque sweep.
6. Record the numbers.
7. Repeat for different wheel sizes and masses.

Only after that should you add navigation, maps, SLAM, and Nav2.

