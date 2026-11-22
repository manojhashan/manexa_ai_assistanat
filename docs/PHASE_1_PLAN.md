# Phase 1 — preserve and verify the existing desktop

## Scope and design contract

Keep the existing blue particle orb, moving nucleus, bold widely spaced luminous MANEXA name,
black background, subtle animations and lower-right settings gear. No robotic head, humanoid
face, character, chatbot, conversation history or dashboard is part of this phase. Preserve
existing working speech/recognition/provider/settings modules; do not extend later phases.

## Repository and environment inspection

- Local Git repository: `E:\Web Development\My Project\manexa_ai_assistanat`. Only the initial
  commit is present; the application source is currently untracked. No Git remote is configured,
  so this inspection covers the actual local working tree, not an unprovided GitHub URL.
- Windows 11 build 26300; Python 3.12.12 in `.venv`; PySide6 6.8.3; bundled Three.js r170.
- NVIDIA RTX 3050 Laptop GPU, 4,096 MiB VRAM; 15.8 GiB system RAM; 16 logical CPUs.
- `app/main.py`: application/CLI lifecycle. `app/ui/window.py`: native fullscreen shell and
  local-only WebEngine/WebChannel. `scene.js`, `orb.js`, `hologram.js`: particle rendering,
  assistant-state/audio response and reconstruction. `scene.css`: existing animated branding.
- Native `SettingsDialog` provides appearance, AI, voice and system tabs; validated preferences
  persist in SQLite. API credentials use the existing Windows vault. Hardware/probes run on workers.
- Existing speech uses real SAPI PCM playback; optional local ASR and Ollama replies are present.
  Wake word, camera tracking, PC automation, reminders and cloud generation/fallback remain
  incomplete and are not Phase 1 acceptance claims. No devices or model downloads start on launch.

## Implementation order

1. Strengthen launch validation without changing the approved visual: include CSS among required
   assets, provide an explicit fullscreen CLI/launcher option, and report actual fullscreen state.
2. Exercise real fullscreen WebGL and animation, gear clicks, settings Save/Cancel/reopen,
   live appearance updates, persisted preferences and window/fullscreen keyboard controls.
3. Restrict packaged renderer assets to the active orb implementation; retain historical facial
   sources/attribution in the repository without loading or shipping them as active UI assets.
4. Run unit/native tests, renderer checks, fullscreen and software launch checks. Build/install
   a fresh wheel, launch it outside the source tree, inspect screenshots, and fix failures.

## Acceptance gate

**Passed for 0.2.4.** See the current Phase 1 entry in [VERIFICATION.md](VERIFICATION.md):
56 unit/native tests, 39 fullscreen/renderer checks, NVIDIA/WARP launches and installed-wheel launch.

- Actual fullscreen app renders the unchanged orb and bold spaced brand on black with the gear.
- Frames and idle motion advance; quality, density, glow, animation speed and motion controls work.
- Gear opens native settings; Save applies and persists; Cancel discards; reopened/restarted settings
  agree with disk. F11 toggles and Escape leaves fullscreen. Close shuts down cleanly.
- No startup network/device capture, chat interface or avatar is introduced.
- Successful installed-package launch, explicit evidence and final screenshot are recorded in
  [VERIFICATION.md](VERIFICATION.md). Stop after this gate; do not begin Phase 2.
