# Redmi Note 5 Pro (whyred) inference node

Dedicated low-power inference appliance, not a second personal agent or
Beeper/desktop worker. Planned ROM: Nusantara Project Android 11, vanilla
if available, enforcing SELinux. Actual flashed ROM/kernel not yet verified.
Native ARM64 Termux + Termux:Boot, no DroidSpaces, PRoot or Linux rootfs.
Stable kernel 4.4+ is sufficient for CPU inference. Root optional.
Use Tailscale and SSH with authenticated private networking; do not expose
llama-server publicly. Benchmark CPU first, investigate Vulkan/OpenCL only
if actual Adreno 509 drivers support it. Initial candidate Qwen3.5-2B Q4_K_M
subject to available RAM, tool-call behavior and actual measured throughput.
Build native llama.cpp from an inspected pinned release and verify model
license/checksum; do not download arbitrary weights or enable cloud billing.
Start with modest context and a single slot, measure memory/thermal limits,
then configure boot recovery. Gateway registration must reflect actual
tool-call/stream support. No model or ROM has been installed by this repo.

Run install.sh only inside native Termux after flashing to install basic
build/network prerequisites. Termux:Boot should be installed from the same
trusted distribution as Termux and opened once; configure autostart after
manual inference acceptance.
