# MANEXA AI

**Your Intelligent Personal Assistant.**

A Windows 11 desktop assistant under incremental development. The main screen contains a real
animated blue 3D particle orb and a small settings gear on black. A rippling particle membrane
surrounds a gently moving inner nucleus, with a spaced luminous **MANEXA** name at its center.
There is no chat interface, conversation history or response text
on the main screen.

**Current release: 0.2.4 — Phase 1 desktop verified.** The original desktop architecture is
preserved. Real local SAPI speech drives orb expansion, waves and brightness from measured PCM.
Optional local Faster-Whisper and Ollama provide explicitly activated spoken turns after setup.
Camera tracking, always-on wake word, acoustic barge-in, PC commands and reminders remain pending.
The latest particle-sphere reference replaces the earlier face concepts. The running app renders
actual GPU particles, without a raster image, face, neck or shoulders. No reference audio was
available for voice matching. See [the orb update](docs/PARTICLE_ORB.md) and
[voice setup and limits](docs/HOLOGRAM_UPGRADE.md).

The current [Phase 1 plan](docs/PHASE_1_PLAN.md) preserves this existing design and verifies
fullscreen launch, animations, the native gear, settings Save/Cancel and packaged assets.
No robotic head, humanoid avatar or interface redesign is included. Phase 2 is on hold.

## What works now

- Fullscreen PySide6 desktop with a locally bundled Three.js WebGL2 scene; no web server or CDN.
- A blue particle sphere with an organic rippling silhouette and a moving inner nucleus. It
  breathes, rotates, responds to speech, disperses and reconstructs. No face or body is rendered.
- Typed renderer inputs for listening/thinking/speaking/error, smooth bounded orientation, and
  speech-amplitude animation connected to actual PCM playback, with immediate stop/reset.
- A small animated native settings gear; keyboard fullscreen and settings controls.
- Persistent, validated SQLite appearance and AI preferences. No general conversation storage.
- Windows Credential Manager key storage scoped to the provider **and** endpoint, with no
  plaintext fallback. Keys are never passed into the scene.
- Actual asynchronous model-list connection tests for Ollama, OpenAI, Gemini, Claude, and custom
  OpenAI-compatible endpoints. Cloud providers require your optional credentials; tests do not
  generate text. Live voice replies currently use loopback Ollama; cloud generation/fallback is pending.
- Local Windows voice enumeration, voice/rate selection, test speech and cancellation; missing Sinhala
  voices are reported honestly. Optional real multilingual ASR runs on CPU with local weights only.
- Hardware detection; explicit performance, balanced and high renderer modes; software fallback.
- Automated persistence/security/provider-contract/native-widget tests and real WebGL launch and
  articulation checks.

## Windows installation

Use **64-bit Python 3.12**. The tested environment uses CPython 3.12.12 and PySide6 6.8.3. Python
3.13 is allowed by package metadata but has not been used to validate this release. No CUDA,
Node.js, Ollama, microphone, webcam or paid API is needed for the current desktop application.

Clone your repository after publishing this source to GitHub, or open the existing project folder:

```powershell
git clone <YOUR_REPOSITORY_URL>
cd <YOUR_REPOSITORY_FOLDER>
```

No remote was configured in the initial repository. The placeholder above is intentionally not a
claim that a public repository has been created or pushed.

The setup script uses [uv](https://docs.astral.sh/uv/) if installed (including a managed Python 3.12
download). Otherwise install Python 3.12 from [python.org](https://www.python.org/downloads/windows/)
with the Python launcher, then run:

```powershell
.\scripts\setup.ps1
.\scripts\run.ps1
```

`run.ps1` launches `pythonw.exe`, so the application does not open a terminal window. To install
test tools as well, use `setup.ps1 -Development`. Installation downloads dependencies; afterward
the desktop and its renderer run offline. The setup script does not download ML models.

Use `.\scripts\run.ps1 -Fullscreen` to explicitly start fullscreen regardless of a saved windowed
preference, or `-Windowed` for a normal window. Without an override, the launcher respects saved
preferences. The two display overrides cannot be combined.

If your PowerShell policy blocks these local scripts, use the manual commands below. No global
execution-policy change is necessary.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m app.main
```

Or activate the environment and use the simple module entry point:

```powershell
.\.venv\Scripts\Activate.ps1
python -m app.main
```

The exact runtime versions are in [requirements-lock.txt](requirements-lock.txt). For an editable
development installation, use `pip install -e ".[dev]"` inside the environment. The wheel package
includes active orb renderer files and the bundled Three.js license; historical face assets are excluded.

Build a wheel with `.\scripts\build.ps1` (requires uv). This uses a fresh staging directory and
checks the wheel against the active renderer asset list, preventing stale files in `build/` from
shipping. The resulting wheel is written to `artifacts\wheel\`.

## Controls and settings

| Control | Action |
|---|---|
| Small gear, lower right | Open settings |
| `Ctrl+,` | Open settings |
| `F11` | Toggle fullscreen |
| `Esc` | Leave fullscreen; dismiss settings when settings has focus |
| `Alt+F4` or `Ctrl+Q` | Quit |
| `Ctrl+D` | Dissolve and reconstruct when motion and advanced effects are enabled |
| `Ctrl+Space` | Interrupt speech and capture one real spoken turn after ASR setup/permission |
| `Ctrl+Backspace` | Stop microphone, pending speech/reply delivery and audio playback |

Settings → Appearance changes quality, particle density, animation speed, advanced effects,
ambient animation, brightness and fullscreen.
Save applies them immediately and persists them. Cancel discards edits. In windowed mode the
native window frame may appear; the fullscreen scene shows only the orb, MANEXA name and settings gear.

Settings → AI defaults to **Ollama / Offline / `http://127.0.0.1:11434` / `qwen3:1.7b`**. A blank
key field keeps an existing key for the same endpoint. Remove stored key deletes that credential
after confirmation. Provider switching clears any unsaved key and selects that provider's URL.
For a remote service use HTTPS; unencrypted HTTP is restricted to loopback. Offline preferences
only permit loopback Ollama. Automatic mode is a saved preference for Phase 9, not an active
fallback service in this increment.

Test connection runs on a worker and checks `/api/tags` (Ollama) or the appropriate provider model
list. It reports unreachable servers, authentication failure, invalid responses and missing models.
It does not silently download a model, generate a response or call a paid completion endpoint.
Enter the exact model ID offered by your cloud provider; no stale cloud model is hardcoded.

Settings → Voice & camera selects installed voices, speech rate/language, microphone and local ASR
model folder. Use Find installed voices, then Speak test sentence for real synchronized playback.
Voice previews use unsaved voice choices without persisting them. Camera remains inactive.
Settings → System & privacy includes on-demand CPU/RAM/GPU detection and the data-folder path.

## Offline AI and model preparation

Install [Ollama for Windows](https://ollama.com/download/windows) and prepare a lightweight model
to enable real local replies after configuring recognition:

```powershell
ollama pull qwen3:1.7b
ollama list
```

Keep Ollama running, then test the connection in MANEXA settings. This verifies a real server and
the configured model's presence. Recognition needs its separate local model. Model downloads
need internet once; weights can be used offline afterward. Ollama stores its own models outside
this repository. No mandatory subscription is involved. Install recognition explicitly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-voice.txt
.\.venv\Scripts\python.exe -m scripts.download_asr --model base --directory models\whisper-base
```

Select that model folder in Voice settings, save, then press Ctrl+Space. The application requests
microphone consent for the session and captures one turn until silence or 15 seconds. It releases
the microphone, recognizes locally, queries loopback Ollama and speaks the reply. No audio is saved.
The optional dependencies/model were installed for development verification; cloned installations
must provision them explicitly. See [the upgrade guide](docs/HOLOGRAM_UPGRADE.md) for limits.

For 4 GB VRAM, the planned starting point is quantized Qwen3 1.7B with 2K context, CPU int8
multilingual Whisper small, and CPU TTS. This is a starting resource budget, not a measured
quality/performance guarantee. Smaller `qwen3:0.6b` is a fallback. Avoid large LLM/ASR models
sharing the GPU. Ollama manages supported GPU offload and CPU fallback when its integration is
active; the desktop, CPU recognition and SAPI speech have no CUDA dependency.

Faster-Whisper GPU acceleration additionally needs compatible cuBLAS/CUDA 12 and cuDNN 9
runtime libraries. A CUDA number reported by `nvidia-smi` does not prove those DLLs are installed.
ASR currently uses CPU int8; a speech GPU path is not added in this release. Do not replace your display
driver or install CUDA merely to run this release.

Sinhala ASR quality, Singlish/mixed speech, an efficient custom Hey MANEXA wake model, a verified
offline Sinhala TTS voice remain technical acceptance
gates. Read [models, hardware and limitations](docs/MODELS_AND_LIMITATIONS.md) for selections,
resource tradeoffs, required future dependencies and primary references.

## Privacy and data

- No microphone or camera opens at startup. Microphone capture requires explicit activation and
  consent, remains RAM-only, is bounded and releases after a turn or stop. Camera remains inactive.
- The scene reads only its bundled assets. Its browser profile is off the record, disk cache/local
  storage are disabled, and outbound requests are blocked. Its bridge exposes renderer health only.
- Default startup makes no AI/network calls. Connection tests occur only when explicitly clicked;
  an activated voice turn may query the configured loopback Ollama server.
  Choosing an online provider does not start background polling in this release.
- Non-secret settings live at `%LOCALAPPDATA%\MANEXA\settings.db`. Override the data directory
  with process environment variable `MANEXA_DATA_DIR`. `.env` files are not auto-loaded.
- API keys go into Windows Credential Manager under `MANEXA AI`, never SQLite, `.env`, the
  renderer or Git. Secure-storage failures are surfaced without falling back to plaintext.
- No automation or generic shell execution exists in the renderer bridge. Later destructive actions
  and email sending require specific explicit confirmation.

To reset preferences, close MANEXA, back up the data folder, and rename `settings.db`. Credentials
are separate and can be removed in Settings or Windows Credential Manager. Corrupt/unsupported
settings are reported instead of silently overwritten.

## Verification

Install development dependencies, then run the complete suite:

```powershell
.\scripts\setup.ps1 -Development
.\scripts\verify.ps1
```

This checks bundled dependency hashes, formatting/lint, tests, native desktop startup, real WebGL
frames, centered MANEXA branding, orientation interpolation, speech-driven orb expansion and release, thinking state
scans, quality changes, fullscreen/Escape/F11, gear clicks, all settings tabs, live Save/Cancel,
reopened preferences and settings access. Windows briefly appear and close.
It never requests a microphone, webcam or cloud API key.

Manual commands are also supported:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\ruff.exe check app tests scripts
.\.venv\Scripts\python.exe -m pytest -q --basetemp artifacts\pytest-local
.\.venv\Scripts\python.exe -m app.main --smoke-test --smoke-report artifacts\smoke.json --screenshot artifacts\head.png
.\.venv\Scripts\python.exe -m scripts.check_renderer
```

The separate voice check is opt-in because it intentionally plays actual speech:

```powershell
.\.venv\Scripts\python.exe -m scripts.check_voice
# Also opens the microphone briefly in memory and releases it:
.\.venv\Scripts\python.exe -m scripts.check_voice --microphone
```

Use only a disposable `--basetemp` path: pytest may delete existing contents there. The verify
script generates a new unique directory each time. `artifacts/` is ignored by Git and contains only
test reports and explicit application-window screenshots. See [verification evidence](docs/VERIFICATION.md)
for checks actually executed; simulated HTTP responses are distinguished from live service tests.

## Troubleshooting

| Symptom | Action |
|---|---|
| `No module named PySide6` | Use `.venv\Scripts\python.exe`, or rerun setup. Avoid installing into a different global Python. |
| Broken Python launcher entry | Use Python 3.12 explicitly or the uv-assisted setup script. The inspected machine had a stale 3.10 entry. |
| Blank scene or WebGL error | Start `.venv\Scripts\python.exe -m app.main --windowed --software-rendering`. Keep the bundled `app/ui/web/vendor/` files intact. |
| High GPU/CPU usage | Select Performance quality and disable ambient animation; reduce resolution. Software rendering trades GPU use for CPU use. |
| Remote Desktop graphics failure | Try software rendering and the software smoke test below. No GPU is required for that compatibility path. |
| Ollama connection fails | Install/start Ollama, check the loopback base URL, and run `ollama list`. The app reports missing server/models honestly. |
| Cloud model not listed | Check the exact model ID, account permissions, API key and base URL. Custom endpoints must support OpenAI-style `/models`. |
| API key cannot be saved | Verify Windows Credential Manager access. No plaintext storage fallback is enabled. |
| Existing temp folder access denied in pytest | Use the verify script's fresh workspace test directory; do not change system folder ACLs. |
| No microphone response | Install optional ASR dependencies, select a local model, save and use Ctrl+Space. Check Windows microphone permission. |
| Sinhala speech unavailable | This machine has only English SAPI voices. A real Sinhala-capable installed voice is required; no English substitute is used. |
| No camera response | Camera tracking is not implemented in this release. |

```powershell
.\.venv\Scripts\python.exe -m app.main --smoke-test --software-rendering
```

On Windows, software mode requests Direct3D WARP (Microsoft Basic Render Driver). Smoke reports
include the actual WebGL adapter, so this can be distinguished from NVIDIA rendering. Qt 6.8's
installed wheels do not provide a working SwiftShader path on this machine. Software mode is a
CPU compatibility option and can be slower, especially at high resolution.

## Next development steps

[ROADMAP.md](docs/ROADMAP.md) preserves the twelve-phase plan and historical foundation gates.
The [0.2 upgrade guide](docs/HOLOGRAM_UPGRADE.md) records the current visual, speech, optional ASR
and local-reply integration. Human Sinhala/Singlish recognition and pronunciation still need testing;
only English SAPI voices are installed here. Reference voice matching, acoustic barge-in, wake word,
camera, PC automation, cloud fallback and persistent reminders remain pending.

Source license: [MIT](LICENSE). Bundled and installed dependencies retain their own terms; see
[third-party notices](THIRD_PARTY_NOTICES.md). No credentials, model weights or personal data are
included, and no GitHub remote is created automatically.

