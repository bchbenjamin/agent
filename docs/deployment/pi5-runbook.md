# Raspberry Pi 5 Operational Runbook

## Host Information
- **Hardware**: Raspberry Pi 5 Model B (4 GB RAM)
- **OS**: Debian GNU/Linux 13 (trixie) aarch64
- **Primary User**: `bchbenjamin` (UID 1000)
- **Root/Boot**: 64 GB microSD (`mmcblk0`)
- **Secondary Data**: 256 GB OSC SATA SSD (`/mnt/pi_data`)

---

## Service Management

### Check Services
```bash
# System services
systemctl status beeper.service lightdm.service wayvnc.service tailscaled.service

# User services
systemctl --user status hermes-gateway-e86e8d0b.service at-spi-dbus-bus.service
```

### Restart Beeper
```bash
sudo systemctl restart beeper.service
curl -s -i http://127.0.0.1:23373/v0/mcp
```

### Restart Hermes Gateway
```bash
export HERMES_HOME="$HOME/.hermes-pi"
hermes gateway restart
curl -s http://127.0.0.1:8642/health
```

---

## Health Verification
Run the automated verification suite:
```bash
bash nodes/pi5/verify.sh
```
