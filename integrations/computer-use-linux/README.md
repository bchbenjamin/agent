# computer-use-linux Integration

## Overview
`computer-use-linux` provides local screen observation and UI interaction on Linux.
- **Backend**: Wayland (`labwc` virtual display `NOOP-1` 1920x1080) and Xwayland.
- **Tools**: Accessibility tree inspection (`at-spi2`), screenshot capture (`xdg-desktop-portal`), window targeting (`wlr-foreign-toplevel`), and input injection (`xdotool`, `wtype`, `uinput`).
- **Security**:
  - `COMPUTER_USE_LINUX_ENABLE_SHELL` is disabled.
  - No unauthenticated network endpoints.
  - Stdio transport used for Hermes and Claude Code integrations.
