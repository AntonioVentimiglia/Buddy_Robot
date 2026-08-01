# Mac and Windows Development Workflows

> **Setting up a new machine? See [`connecting_to_buddy.md`](connecting_to_buddy.md)** —
> concrete SSH/key/config steps for macOS and Windows, how the Jetson pulls from
> GitHub with its own deploy key (so no laptop is the "blessed" one), and how to
> flash the drive MCU regardless of which computer you are sitting at.

## macOS

Recommended:

- VS Code Remote SSH into the Jetson or Linux dev machine.
- Docker for non-hardware package development.
- Foxglove in browser/desktop.

Avoid relying on native macOS ROS builds for hardware integration unless you intentionally want toolchain work.

## Windows

Recommended:

- VS Code Remote SSH into the Jetson or Linux dev machine.
- WSL2 for ROS CLI experiments and non-hardware work.
- Docker Desktop for dev containers.
- Foxglove in browser/desktop.

Avoid relying on native Windows as the only hardware integration environment.
