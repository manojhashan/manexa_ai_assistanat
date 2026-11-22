# Verification log

The current visual is the [blue particle orb](PARTICLE_ORB.md). Earlier face/bust and Phase 1/2
entries below are historical checks.

## Phase 2 visual integration — implementation completed

Baseline:

- Branch: `phase2/visual-integration`
- Verified Phase 1 baseline: tag `phase1-0.2.4-verified`, commit `679840d`
- Audit: [PHASE_2_AUDIT.md](PHASE_2_AUDIT.md)
- Implementation phase did not modify the orb geometry, branding, settings UI or asset manifest.

Implemented and verified:

- Smoke launches now poll for stable diagnostic frames instead of using a fixed post-ready delay.
- Smoke JSON reports typed stages for assets, page load, WebChannel/graphics and stable diagnostics.
- Three.js cleanup owns the bloom target, scene/post-process resources, resize listeners and
  global/window listeners through an idempotent disposal path.
- WebGL context-loss pauses frame work and reports a recoverable graphics state.
- WebGL context restoration recreates the bloom target, reapplies settings and state, and resumes
  the existing orb and brand with no visual redesign.
- Window teardown centrally stops the startup timer, gear timer, voice, dialogs, shortcuts and
  pending application work before WebEngine page detachment.
- Settings Save validates and persists preferences with credential rollback compensation. If
  SQLite persistence fails after a credential write, the previous credential is restored or the
  newly created credential is deleted.
- Closed settings dialogs invalidate provider, hardware and voice-worker callbacks; stale results
  no longer update UI state.
- SettingsStore diagnostics now report current, uninitialized, corrupt or unsupported schemas
  without exposing secret values or silently overwriting data.

Acceptance results:

- **62 tests passed**, preserving all 56 existing Phase 1 tests and adding six focused regression
  tests for migration, credential rollback and stale worker behavior.
- Ruff vendor/lint/format checks passed.
- Hardware NVIDIA RTX 3050 smoke and fullscreen renderer checks passed.
- WARP Microsoft Basic Render Driver smoke and fullscreen renderer checks passed.
- Hardware and WARP runs both produced real particles, one draw call, visible centered `MANEXA`
  branding and the native settings gear.
- **39/39 renderer/settings integration checks passed** in both hardware and WARP verification.
- Three repeated WARP fullscreen startup/shutdown smoke cycles passed.
- Fresh wheel build passed and contains seven active orb assets with no legacy avatar assets.
- No robotic head, humanoid face, chatbot, dashboard, wake word, camera or recognition behavior
  was introduced.

## Phase 1 gate — 0.2.4, existing design preserved

- Inspected the local repository, all application subsystems, settings, renderer, tests, scripts
  and environment. No GitHub remote is configured. The working tree contains the existing app;
  no commit, remote creation or push was performed. The active [Phase 1 plan](PHASE_1_PLAN.md)
  supersedes historical avatar requirements.
- Preserved the blue particle orb, nucleus, bold spaced luminous MANEXA name, black background
  and gear. Added no robotic head, face, chatbot or dashboard. Existing voice/provider modules
  remain, without extending or accepting a later phase.
- Fixed startup preflight to include CSS and all current renderer assets. Added mutually exclusive
  fullscreen/windowed launch overrides, including fullscreen smoke verification against the
  actual display geometry. The launcher still respects saved preferences without an override.
- **56 unit/native tests passed**, along with Ruff lint/format and vendor integrity checks.
  New coverage includes launch arguments, missing CSS, Save changing actual fullscreen state,
  persisted appearance settings, reopened controls and Cancel retaining the saved values.
- **All 39 real fullscreen/renderer checks passed** on NVIDIA RTX 3050. Verified actual frames,
  idle/state/audio-response animations, quality/density/speed controls, Escape/F11, gear click,
  all four settings tabs, visible Save/Cancel, disk persistence and immediate renderer updates.
  This uses test amplitude inputs and does not claim a new real microphone/AI acceptance test.
- Inspected `phase1-fullscreen.png` and the four `phase1-settings-*.png` screenshots. The native
  fullscreen window matches the 1536×864 logical display (1920×1080 pixels at 125% scaling).
  The main scene retains one point draw call plus its separate bloom composite.
- A package-content assertion caught retired files surviving in setuptools' old `build/` cache.
  Added `scripts/build.ps1` using fresh staging and `scripts.verify_package` checking the exact
  active asset manifest. The 0.2.4 wheel contains seven renderer assets and no legacy avatar assets.
- Installed the fresh wheel into `artifacts/package-env` and launched outside the source tree
  with `--smoke-test --fullscreen`: passed. NVIDIA packaged launch and WARP software fullscreen
  launch both rendered real particles, centered branding and a visible gear, and exited normally.
- Current evidence: `renderer-check.json`, `smoke.json`, `phase1-package-smoke.json`,
  `phase1-software-smoke.json`, `phase1-complete.png`, and settings screenshots under `artifacts/`.
  Phase 1 is accepted for this scope. Phase 2 remains on hold.

## Centered luminous MANEXA branding

- `scripts/verify.ps1` passed again: **51 unit/native-widget tests** and **28 renderer checks**,
  including six centered letters with a visible gap, speech-driven text brightness and decay,
  and disabling text motion with the existing motion control.
- Inspected the real desktop screenshot at `artifacts/brand-preview.png`. The orb still renders
  in one GPU point draw call; the name is a lightweight local CSS overlay without an external font.
- Startup smoke checks now expect only the requested MANEXA label as visible scene text.

## Current blue particle orb — 0.2.3

- `scripts/verify.ps1` passed: **51 unit/native-widget tests**, lint/format, vendor integrity,
  actual NVIDIA WebGL launch, and **25 renderer integration checks**. They verify rendered
  particles, the nucleus, no face/body, state delivery, amplitude-driven expansion and decay,
  orientation, reconstruction, appearance controls and native settings access.
- Real SAPI → PCM playback → WebGL passed **all 9 voice checks**. Measured audio reached 0.98,
  rendered orb response reached 0.86, and interruption cleared speech energy and released the
  output device. The stop call took 1.28 ms in this run, which is not a physical speaker-latency
  guarantee. No microphone was reopened for this visual regression check.
- NVIDIA RTX 3050 and Microsoft Basic Render Driver (WARP) smoke launches passed. Balanced mode
  uses 7,000 particles, zero surface triangles and one scene draw call, plus a separate bloom
  composite. It retains the 45 FPS cap; this is not a sustained performance benchmark.
- Built/installed the 0.2.3 wheel into `artifacts/package-env`. Its actual WebGL launch outside
  the source package passed and loaded the packaged `orb.js` correctly.
- Evidence under ignored `artifacts/`: `renderer-check.json`, `orb-voice-check.json`,
  `orb-software-smoke.json`, `orb-package-smoke.json`, `orb-speaking.png`, `orb-final.png`.
  Voice/language availability and optional AI/ASR limits remain unchanged.

Checks executed on the Windows 11 target machine. Development is incremental: this log does not
mark microphone, Sinhala speech, wake word, Ollama inference or camera tracking as tested.

## Phase 1 gate — passed before building the head

- `python -m compileall -q app tests`: passed.
- `python -m pytest -q --basetemp artifacts/pytest-phase1 --tb=short`: **35 passed**.
- `ruff check app tests`: passed after formatting.
- `python -m app.main --smoke-test --smoke-report artifacts/phase1-smoke.json --screenshot artifacts/phase1.png`:
  exit code 0; 1280 × 800 native window; scene loaded from disk; visible settings gear;
  off-the-record browser profile confirmed.
- Native Qt tests saved appearance preferences and reopened the dialog, clicked the gear, entered
  fullscreen and returned to a normal window, and checked provider-switch credential clearing.
- Persistence tests reopened SQLite, rejected invalid/corrupt settings and verified no conversation
  or credential fields/tables exist.
- Provider contract tests used HTTP test transports to verify API headers, missing models,
  authentication failures, invalid payloads and redirect refusal. These are **protocol tests, not
  live cloud provider verification**. No API credentials or paid calls were used.
- The first pytest invocation encountered an existing inaccessible directory in the host's shared
  temp area. An isolated workspace `--basetemp` resolved it without changing Windows permissions.
  The verification script uses a fresh workspace path on every run.

## Phase 2 gate — implementation and hardware verification

- Complete `scripts/verify.ps1`: **37 tests passed**, hash verification, Ruff checks and native
  startup passed; the actual renderer integration check passed **all 13 assertions**.
- Actual hardware renderer: ANGLE / NVIDIA GeForce RTX 3050 Laptop GPU / Direct3D11,
  WebGL 2.0, 25,900 rendered triangles, 70 draw calls, one canvas, no visible DOM text.
- The hardware smoke report observed 70 rendered frames in approximately 1.59 animation seconds
  with the 45 FPS cap; this short sample is not a sustained performance benchmark.
- Visually inspected the generated head screenshot. Head geometry, metal shading and electric
  eyes render; the setting gear is the only other main-screen visual control. This procedural
  mechanical face is not a photorealistic artist-made model.
- Renderer inputs were exercised through the real Python → Qt WebChannel/JavaScript boundary:
  listening state; faster thinking scan; supplied 0.85 amplitude opening the jaw to about 0.246
  radians; stale amplitude closing the jaw; bounded yaw/pitch moving the mesh; quality/resolution
  settings; ambient motion control; independently changing eyelid geometry and settings access.
  The amplitude is explicitly a **renderer test stimulus**, not a claim of real speech playback.
- An initial combined verification exposed overly short wall-clock assumptions in pose/blink
  sampling. Pose settling now has more time, blink verification observes the minimum openness
  actually rendered, and the frame cap preserves fractional intervals (45 FPS no longer rounds
  down to every second 60 Hz frame). The combined hardware run subsequently passed.
- A real temporary Windows Credential Manager write/read/delete round trip passed. The temporary
  self-test entry was removed and its absence checked. No actual user API key was used.
- A real loopback Ollama probe reported the server unavailable, accurately; no model inference
  was claimed and no weights were installed.
- `setup.ps1 -Development` ran successfully against the project environment.
- `uv build --wheel` produced a wheel containing the Python packages, all scene files, Three.js
  module and license. Final isolated package launch and software-run results are recorded below.

No later phase is accepted based on these renderer tests. Real microphones, Sinhala recognition,
TTS, wake word, camera tracking, system actions and reminders remain unimplemented in this increment.

## Software rendering investigation

The first SwiftShader flag still selected the NVIDIA adapter, so it was not accepted as a software
test. Mesa/`--disable-gpu` attempts could not create WebGL2. The working Windows fallback uses
`QSG_RHI_BACKEND=d3d11`, `QSG_RHI_PREFER_SOFTWARE_RENDERER=1` and Chromium's
`--ignore-gpu-blocklist` for the software adapter. A real smoke check then reported **Microsoft
Basic Render Driver**, WebGL2 and actual head pixels. No drivers were changed and no additional
graphics binaries were downloaded. The final `--software-rendering` option uses this configuration.

The GitHub Actions Windows workflow is provided for repeatable checks but has **not** been executed
on GitHub; the repository has no remote configured.

## Final software and package gates — passed

- `scripts/verify.ps1 -SoftwareRendering`: **37 tests and all 13 renderer assertions passed**;
  actual WebGL adapter reported **Microsoft Basic Render Driver / Direct3D11**.
- Built the wheel with `uv build --wheel`, installed it into a separate environment under
  `artifacts/package-env`, and launched from `artifacts/` rather than the source directory.
  `app.__file__` resolved to that environment's `site-packages/app`, confirming the source checkout
  did not mask missing package assets. The installed package's native/WebGL smoke test passed,
  including actual head pixels, no visible text, the native gear and an off-the-record profile.
- Native settings screenshot was inspected for readable controls and explanatory capability status.
- Final preview and reports are under ignored `artifacts/`; no model, recording or user key was
  included in the package or source.

## Hologram and voice upgrade 0.2

- Inspected all application components, settings, tests, scripts, dependency/license files and
  documentation before modifying them. No video/audio attachment was available; visual changes
  follow the text description and default voice pitch/timbre were not guessed.
- **51 unit/native-widget tests passed.** New checks cover legacy preference compatibility,
  persistent effects/voice controls, invalid settings, sample-derived envelopes, resampling across
  irregular native-format chunks, mixed-script routing, missing ASR weights, SAPI plain-text flags,
  refusal to substitute a missing Sinhala voice, stateless Ollama streaming and loopback boundaries.
- **All 22 renderer checks passed on NVIDIA and Microsoft Basic Render Driver (WARP).** Actual
  WebGL renders the blue/orange bust, chest core and thousands of particles, and verifies jaw/lid
  articulation, voice energy, pose, state scans, rotation, dissolution/reconstruction, advanced-effect
  disabling, density/quality/speed settings and native settings access. Balanced scene: 49,986
  triangles, 202 draw calls and 7,000 sampled particles. These counts are not a long-term benchmark.
- The dissolution test exposed a manual/ambient-cycle overlap; a cooldown fixed it. Animation
  speed now uses a continuously accumulated clock, avoiding jumps when a saved speed changes.
- Native speaker/microphone devices required their preferred PCM formats. The implementation
  converts SAPI mono int16 output to native output PCM on a worker and converts microphone PCM
  to 16 kHz mono in memory. It does not reject the working devices simply because they do not
  advertise 22.05 kHz or 16 kHz mono as native formats.
- An actual SAPI → native audio playback → processed-sample clock → WebGL check passed. Measured
  levels reached about 0.96 and rendered jaw/chest energy responded. Playback interruption reset the
  device, zeroed mouth/energy and returned to idle. Recorded stop-call duration was approximately
  1–2 ms in these short tests; this is not a physical speaker-latency guarantee.
- The opt-in real microphone check received PCM, drove the actual listening state with no residual
  speaking jaw movement, and released the microphone. Captured audio stayed in RAM and was discarded.
- SAPI enumeration found only Microsoft David Desktop and Microsoft Zira Desktop, both English.
  Actual Sinhala synthesis correctly reported a missing Sinhala voice before playing anything.
- Explicitly provisioned multilingual Faster-Whisper base into ignored `models/whisper-base` for
  development testing. A real SAPI-generated English test sentence was resampled and decoded by
  actual local CPU int8 Faster-Whisper: "This is a local speech recognition test. Please open the
  settings." The combined synthesis/first-model-load/recognition check took about 11.2 seconds.
  This is not a warm ASR benchmark or a test of human Sinhala/Singlish accuracy. No audio was saved.
- Built the 0.2 wheel, installed it into `artifacts/package-env`, and launched it from `artifacts/`
  outside the source package. The installed package's actual WebGL smoke test passed with the new
  `hologram.js`, speech/voice modules and COM dependency included.
- Live Ollama generation could not be tested because Ollama is not installed/running. The adapter
  is implemented and protocol-tested; optional cloud probes remain intact. No paid API call, fake
  assistant answer, camera access, PC action or conversation-history storage was introduced.

Current audit artifacts: `upgrade-visual.png`, `hologram-dissolved.png`, `renderer-check.json`,
`voice-check.json`, `asr-check.json`, and `upgrade-package-smoke.json` under ignored `artifacts/`.
The audible voice check and microphone option are separate from the silent standard verification.

## Reference image correction — 0.2.1

- The newly supplied image replaces the earlier orange/blue bust direction. The actual app now
  renders only a cyan anatomical network head and short neck on black, with fine irregular lines,
  glowing surface nodes, small luminous irises and no orange face, chest core, shoulders or rings.
- Adapted the attributed CC BY 3.0 Lee Perry-Smith facial geometry; cropped shoulders/neck,
  normalized/welded the geometry and bundled a local geometry-only JavaScript asset. Both the
  derived asset and its attribution are checked by SHA-256. No photographic material is rendered.
- All **51 unit/native desktop tests** and **24 actual renderer assertions** passed. The updated
  renderer checks explicitly verify the cyan head-only design and zero warm/orange pixels in the
  sampled facial area. Blink/jaw animation, amplitude-driven energy, pose, dissolution/reconstruction,
  quality/density/speed controls and settings access still pass.
- The scene reports **17,162 triangles, 23,944 network edges, 7,000 particles and 10 draw calls** in
  balanced mode. A short NVIDIA smoke sample rendered approximately 69 frames in 1.60 animation
  seconds with the 45 FPS cap; this is not a sustained benchmark. Sparse network pixel checks now
  sample a facial area instead of expecting a solid center pixel. The frame cap no longer allows
  an early-render tolerance to accidentally draw twice near a frame boundary.
- Source credit and reproduction instructions are in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)
  and [REFERENCE_HEAD.md](REFERENCE_HEAD.md). The existing voice/microphone/AI/settings services
  and privacy boundaries are retained.
- The actual WARP software renderer smoke check passed with the new head and no orange pixels.
  The audible SAPI playback check passed all nine assertions, including measured PCM driving the
  new facial network, immediate stop/reset, and normal completion returning to idle. No microphone
  was reopened for this visual-only regression check.

