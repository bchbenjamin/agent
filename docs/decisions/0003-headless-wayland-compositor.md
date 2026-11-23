# ADR 0003: Headless Wayland Compositor (labwc) Architecture

## Context
Beeper Desktop is an Electron graphical application requiring an active display server to start its local API (port 23373). The Raspberry Pi 5 runs headless without an HDMI monitor. Traditional setups rely on Xvfb, which lacks native Wayland support and modern accessibility integration.

## Decision
Utilize Debian trixie's native `lightdm.service` autologin into `labwc -m` compositor.
- When no physical monitor is connected, `labwc` automatically creates a virtual output (`NOOP-1`, 1920x1080) on socket `wayland-0` and Xwayland `:0`.
- `wayvnc.service` attaches to this display for remote maintenance; disconnecting VNC does not stop the session or kill applications.
- Beeper starts under systemd with `ExecStartPre` waiting for `wayland-0`.
- `computer-use-linux` interacts directly with this session via `at-spi2` and `xdg-desktop-portal`.

## Consequences
- No separate virtual framebuffers (Xvfb) needed.
- Unified graphical session accessible concurrently by Beeper, Computer-Use MCP, and VNC.
- Preserves full GPU acceleration and Wayland protocol security.
