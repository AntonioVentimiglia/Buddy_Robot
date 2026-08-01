# Connecting to Buddy from Any Machine

The robot's Jetson is the one place the code has to be current. Everything else
— Mac, Windows, whatever you sit at next — is a terminal into it. This document
is the setup for a new machine.

**The rule that makes this work: the Jetson pulls from GitHub itself.** It does
not depend on a sync from one blessed laptop, so there is no "wrong computer"
to be sitting at.

## Facts

| | |
|---|---|
| Hostname | `venti.local` (mDNS) — falls back to the DHCP address if mDNS is flaky |
| User | `venti` |
| Repo on robot | `~/Buddy_Robot` |
| Wi-Fi MAC | `9C:C7:D3:F6:CA:0B` (interface `wlP1p1s0`) — for a DHCP reservation |
| ROS domain | `ROS_DOMAIN_ID=42`, set in `~/.bashrc` by the setup script |

## The Jetson pulls from GitHub (configured 2026-07-31)

The repo is private, so the Jetson has its own deploy key at
`~/.ssh/github_buddy`, registered on GitHub under repo **Settings** →
**Deploy keys** as `buddy-jetson`. `~/Buddy_Robot` is a real checkout on branch
`main` tracking `origin/main`.

Refreshing the robot from any machine:

```bash
ssh buddy 'cd ~/Buddy_Robot && git pull'
```

That is the whole workflow. Push from whichever laptop you are on, pull on the
robot. No machine is authoritative and there is no rsync step.

### If the key ever needs re-creating

```bash
ssh-keygen -t ed25519 -f ~/.ssh/github_buddy -N "" -C "buddy-jetson-deploy"
git config --global core.sshCommand "ssh -i ~/.ssh/github_buddy -o IdentitiesOnly=yes"
```

Then add `~/.ssh/github_buddy.pub` to the repo's deploy keys. Grant **write
access** only if you intend to commit *from* the robot; read-only is the default
and is enough for `git pull`.

> **Gotcha worth knowing:** `git init` may create a `master` branch with no
> upstream, in which case `git pull` prints tracking advice and silently does
> nothing — HEAD never moves and the robot looks up to date when it isn't.
> Fix with `git checkout -B main origin/main`.

> `robot_ws/install/`, `build/` and `log/` are colcon build artifacts and are
> gitignored. They live only on the robot and survive `git pull`; a rebuild is
> `colcon build` in `robot_ws/` (about 6 s).

## macOS (already configured)

Key at `~/.ssh/buddy_jetson`, stanza in `~/.ssh/config`:

```
Host buddy
    HostName venti.local
    User venti
    IdentityFile ~/.ssh/buddy_jetson
    IdentitiesOnly yes
    ServerAliveInterval 30
    ServerAliveCountMax 6
```

## Windows

Windows 10/11 ships an OpenSSH client — no PuTTY needed. In **PowerShell**:

**1. Generate a key for this machine.** Use a separate key per device so one can
be revoked without disturbing the others.

```powershell
ssh-keygen -t ed25519 -f $env:USERPROFILE\.ssh\buddy_jetson -C "buddy-windows"
```

**2. Send the public key over** — paste the output of this into a message and it
gets appended to the Jetson's `authorized_keys`:

```powershell
type $env:USERPROFILE\.ssh\buddy_jetson.pub
```

Or do it yourself in one line (it will ask for the Jetson password once):

```powershell
type $env:USERPROFILE\.ssh\buddy_jetson.pub | ssh venti@venti.local "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

**3. Create `%USERPROFILE%\.ssh\config`** with the same stanza as macOS, but
with the Windows path:

```
Host buddy
    HostName venti.local
    User venti
    IdentityFile ~/.ssh/buddy_jetson
    IdentitiesOnly yes
    ServerAliveInterval 30
    ServerAliveCountMax 6
```

If `venti.local` does not resolve on Windows, use the IP instead — Windows mDNS
support is less reliable than macOS. This is the case where a **DHCP reservation
earns its keep**; see the MAC address above.

**4. Verify:**

```powershell
ssh buddy "hostname && hostname -I"
```

## Editing code

Use **VS Code Remote-SSH** against host `buddy` from either machine. You are then
editing the files the robot actually runs — no sync step, no divergence, and the
same experience on Mac and Windows.

Local checkouts on a laptop are still fine for docs, CAD, and running
`tools/build.py`, but the robot should be updated with `git pull`, not by copying
files around.

## Flashing the drive MCU

**The Nucleo lives on the Jetson's USB-A port**, so flashing does not depend on
which laptop you are using — or on having the right USB adapter:

```bash
ssh buddy '~/Buddy_Robot/tools/flash/flash_drive_mcu.sh --probe'
```

Full build-and-flash needs PlatformIO, which is currently only on the Mac. The
Jetson has `stlink-tools`, which flashes a prebuilt binary:

```bash
ssh buddy 'st-flash --reset write /tmp/buddy_firmware.bin 0x08000000'
```

Installing PlatformIO on the Jetson would make it self-sufficient for firmware
work. Not done yet — Ubuntu 24.04 marks its Python environment as externally
managed (PEP 668), so it needs `pipx` or a venv rather than a plain
`pip install --user`.

## Verifying the robot after any change

```bash
ssh buddy '~/Buddy_Robot/devops/jetson/verify_drive_mcu_link.py'
```

```bash
ssh buddy '~/Buddy_Robot/devops/jetson/verify_zero_hardware_stack.sh'
```
