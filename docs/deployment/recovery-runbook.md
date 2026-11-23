# Full Node Disaster Recovery Runbook

## Rebuilding the Pi 5 from Scratch

If the 64 GB microSD card fails or must be replaced:

### 1. Flash Base OS
- Flash Debian 13 (trixie) 64-bit or Raspberry Pi OS 64-bit to a new microSD card.
- Configure default user `bchbenjamin`.

### 2. Connect Storage & Remount Data SSD
- Attach the 256 GB OSC SATA SSD via the USB adapter.
- Confirm SSD identity via `/dev/disk/by-id/ata-OSC_SSD_256GB_OSC20091900000001448`.
- Add fstab entry:
  ```fstab
  UUID=cbdf283b-2951-44de-945e-c082bf87f337 /mnt/pi_data ext4 defaults,nofail,x-systemd.device-timeout=10s 0 2
  ```
- Mount storage: `sudo mount -a`.

### 3. Clone Infrastructure Repository
```bash
git clone https://github.com/awarespan/personal-ai-infrastructure.git ~/personal-ai-infrastructure
cd ~/personal-ai-infrastructure
bash deployment/install/bootstrap-node.sh pi5
```

### 4. Restore Secrets & State
- Restore `.env` from secure offline backup into `~/.hermes-pi/.env` (mode `0600`).
- Restore operational state databases from `/mnt/pi_data/backups/`.
- Run `bash nodes/pi5/verify.sh` to confirm full recovery.
