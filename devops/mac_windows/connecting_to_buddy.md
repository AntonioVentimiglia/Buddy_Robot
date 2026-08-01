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

## One-time: let the Jetson pull from GitHub

The repo is private, so the Jetson needs its own credential. It has a dedicated
deploy key at `~/.ssh/github_buddy` (generated 2026-07-31).

**Add the public key to GitHub** → repo **Settings** → **Deploy keys** →
**Add deploy key**. Title it `buddy-jetson`. Tick **Allow write access** only if
you intend to commit *from* the robot; read-only is the safer default.

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPiQ8pta1nDYJt9VicxUHcucGZP9/cj9vUSzHivRFLrM buddy-jetson-deploy
```

Then, on the Jetson, point git at that key and attach the remote:

```bash
git config --global core.sshCommand "ssh -i ~/.ssh/github_buddy -o IdentitiesOnly=yes"
cd ~/Buddy_Robot && git init -q 2>/dev/null; git remote add origin git@github.com:AntonioVentimiglia/Buddy_Robot.git 2>/dev/null
git fetch origin && git reset --hard origin/main
```

After that, refreshing the robot from any machine is just:

```bash
ssh buddy 'cd ~/Buddy_Robot && git pull'
```

> Note: `~/Buddy_Robot` was originally populated by `rsync` from the Mac and is
> not yet a git checkout. The `git fetch` + `reset --hard` above converts it.
> **CAD/ and site/ were excluded from that rsync** and will appear on first pull;
> that is expected, and CAD is unused on the robot.

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
