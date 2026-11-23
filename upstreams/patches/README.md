# Upstream Patches Policy

## Policy
1. Upstream open-source repositories must be consumed from official pinned releases or commit hashes whenever possible.
2. In-tree forks or full copies of upstream projects are strictly prohibited.
3. If an upstream project requires customization to interface with the Personal AI API:
   - The minimal patch file must be stored in this directory.
   - The patch must be referenced in `upstreams/manifest.yaml`.
   - The reason for the patch, upstream issue URL (if filed), and instructions for re-applying or removing upon upstream release must be documented.

## Active Patches
- None currently required. Core integrations (Hermes, computer-use-linux, Beeper) are running unpatched using official release builds and configuration APIs.
