# MANEXA AI implementation roadmap

## Active scope — Phase 1 desktop verification

The latest user instruction supersedes all historical head/avatar design requirements. Preserve
the blue particle orb, bold luminous MANEXA name and black background. The active work is the
[Phase 1 plan](PHASE_1_PLAN.md); later phases are on hold. Previously implemented voice and provider
services remain intact, without treating their presence as acceptance of later development gates.

This repository began with only `.git` and `.gitattributes`. There was no application to preserve
and no Git remote configured. Development starts with a tested desktop foundation, then proceeds
through the gates below. A renderer animation is not proof that a voice or automation feature works.

## Architecture

```text
app/main.py                  CLI, QApplication and lifecycle
app/config/                  validated non-secret preferences, SQLite persistence
app/core/                    typed assistant state and bounded head pose
app/security/                explicit Windows Credential Manager backend
app/ai/                      actual provider connection probes
app/services/                background tasks and read-only hardware inventory
app/ui/                      native PySide6 shell, settings and narrow Qt WebChannel
app/ui/web/                  local Three.js geometry, animation, shaders, bundled dependency
tests/                       persistence, endpoint/authentication, security and desktop tests
scripts/                     Windows setup, launch and repeatable verification
docs/                        roadmap, hardware/model decisions and verification evidence
models/                      documentation only; downloaded weights remain ignored
```

The 0.2 upgrade adds real `app/speech/` and `app/voice/` packages, a local Ollama reply adapter and
`app/ui/web/hologram.js`. Remaining wakeword, camera, tracking, automation, reminders and calendar
packages will be introduced with working implementations rather than placeholder functions.

The main Qt thread handles widgets and renderer events. HTTP requests, model inference, speech
synthesis, microphone segmentation and camera capture must run in bounded workers with cancellation.
Workers send typed events to the renderer. The embedded browser must never receive API keys,
recordings, file contents or a generic system-execution bridge.

## Phases and required gates

| Phase | Implementation | Required verification before advancing |
|---|---|---|
| 1. Foundation | Python 3.12 environment; modular PySide6 desktop; dark fullscreen main window; tiny animated settings gear; validated SQLite settings; background tasks; secure vault; setup and launch scripts | Actual Windows launch; fullscreen escape; settings reopen/save/restart; offline renderer boundary; credential failure does not write plaintext; responsive background operation |
| 2. Visual integration (on hold) | Preserve the existing local Three.js particle orb and luminous brand; refine integration only if required; no head, humanoid face or character | Real WebGL frames; actual state/audio response; low/high quality settings; offline local dependencies; no chat UI or avatar |
| 3. Recognition | Optional Faster-Whisper and sounddevice; in-memory 16 kHz segmentation; device enumeration and permission; language auto/si/en; CPU int8 fallback; explicit model provisioning | Real microphone English/Sinhala/mixed corpus; missing-device and corrupt/missing-model behavior; silence hallucinations; latency/RAM measurement; no audio files written |
| 4. Local AI | Ollama `/api/chat`; Qwen3 1.7B Q4; 2K context; short stateless prompts; disable thinking where supported; cancellation; model/server readiness | Real local inference with internet disconnected; missing Ollama/model error; bounded context and output; no conversation table or log; UI remains responsive |
| 5. Speech | Windows SAPI fallback; optional CPU Piper English; selected-language capability report; PCM envelope drives jaw; playback cancellation and resource release | Listen to real output; measure animation against actual samples; interruption stops playback; unsupported Sinhala voice produces an honest capability message; do not read Sinhala through an English voice |
| 6. Wake word | In-memory recognition phrase gate as an explicit temporary fallback; train or supply a custom ONNX Hey MANEXA model for efficient always-on openWakeWord | Real voice in quiet/noise across speakers and accents; false accept/reject rates; phrase followed immediately by a command; echo suppression; wake while speaking; microphone permission |
| 7. Tracking | Local camera capture after explicit consent; MediaPipe face landmarks or OpenCV fallback; head position/pose; smoothing; camera/device/sensitivity/speed/calibration controls; active indicator | Actual webcam permission, movement, occlusion, unavailable device, camera switching and disconnect; close releases device; no frame files or uploads; indicator follows real capture state |
| 8. Windows actions | Deterministic bilingual intent router; installed-app registry; allowlisted subprocess arguments with `shell=False`; safe file roots; volume/media/screenshot adapters; read-only monitoring; confirmation transactions | Actual supported operations and postcondition checks; failure speech; restricted paths; expiry/cancel/replay of destructive confirmations; prompt injection cannot execute shell; hardware-dependent controls honestly reported |
| 9. Online AI | Explicitly chosen provider; OpenAI-compatible, native Gemini and Claude adapters; provider reachability checks; offline fallback; return to preference after recovery | Contract tests plus optional user-configured live calls; internet drop/recovery; no network in offline mode; no key in URL/log/SQLite; no duplicate charge after an uncertain POST; cancellation |
| 10. Reminders, calendar, web | SQLite reminder/event repository; timezone-aware scheduler; next-occurrence English/Singlish parser; notifications and TTS; safe encoded web searches; selected weather source | Real persistent reminder after restart; overdue/repeated/DST handling; notification and spoken delivery; disambiguation; offline-only web failure; recipient/message readback and explicit confirmation for configured email transport |
| 11. Complete settings/security | Real device selection; consent; voice status; startup opt-in; permissions; default folders; settings migration; atomic changes; secure scoped credentials | Reopen/restart across all settings; explicit permission revocation; model/provider capabilities shown accurately; mail/delete confirmations cannot be bypassed; uninstall remains gated |
| 12. Integration/performance | Cold start; soak test; memory/VRAM budgets; worker shutdown; package/release instructions and acceptance checklist | End-to-end real microphone → local command/LLM → actual TTS → mouth motion; interruptions and reminders during inference; camera plus LLM resource use; test target PC offline and online |

## Privacy and security rules for subsequent phases

- Store settings, reminders and calendar events only. Keep each conversational turn in RAM only
  while it is being handled. Never persist conversations or general personal memory.
- Do not automatically download models, enable startup, open devices or select paid providers.
- Keep the default offline: local Ollama and local models; no connectivity polling to public hosts.
- Camera tracking preference may default ON, but capture must wait for an affirmative camera grant.
  No indicator is displayed while capture is inactive.
- An LLM may propose a structured action. A deterministic validator must authorize it. Never execute
  an LLM-generated shell command, PowerShell text, Python snippet or executable path.
- Confirm recipient and message aloud before email sending. Deletion, uninstall and other destructive
  actions require a specific, expiring confirmation bound to the exact action.
- Ask before reading sensitive files. Limit normal file search to explicit configured roots.
- Retrieve a provider key only for its exact provider and endpoint. Do not forward authentication on
  redirects. Fail closed if secure storage is unavailable.

## Foundation delivery boundary (0.1, historical)

This first development increment targets Phase 1 and the Phase 2 renderer. Connection tests are
useful real groundwork for Phase 4/9, not a claim that model generation is integrated. The main
scene stays idle until a real service emits a state event. Voice, wake-word and camera access are
not faked or enabled in this increment. Later acceptance criteria remain pending until tested with
the appropriate devices and models. See [VERIFICATION.md](VERIFICATION.md) for executed checks.

## Current upgrade (0.2)

The [hologram and voice upgrade](HOLOGRAM_UPGRADE.md) retains this architecture and adds the
blue/orange particle bust, scanning/core energy, dissolution/reconstruction, real SAPI PCM playback
and synchronization, immediate keyboard interruption, optional local microphone/ASR turns and a
stateless local Ollama reply adapter. Installed English speech, microphone capture and actual local
English ASR have been tested. Human Sinhala/Singlish accuracy, Sinhala TTS (no installed voice),
live Ollama inference (no server), reference audio matching and the remaining phases are not marked
accepted. The verification log distinguishes these boundaries.

