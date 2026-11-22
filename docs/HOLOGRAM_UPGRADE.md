# Hologram and voice upgrade (0.2)

This documents the earlier blue/orange visual request and the voice integration that is retained.
The current 0.2.3 approved head-only design is described in [REFERENCE_HEAD.md](REFERENCE_HEAD.md).

## Inspected baseline and reference availability

The inspected project had PySide6 6.8.3, a bundled Three.js r170 renderer, a procedural articulated
head, native settings, SQLite preferences, provider connection probes and security boundaries.
It had no implemented TTS, microphone recognition, AI generation, wake word, camera or PC actions.
Those findings matter: there was no existing synthesized voice or conversation pipeline to retune.

No video or audio file was available in the supplied attachments. Only text attachments were found.
No claim is made about the reference's pitch, accent, pace, naturalness, Sinhala pronunciation or
speaker identity. The visual upgrade follows the written description. The default Windows SAPI
voice, its pitch and its normal rate are preserved; no guessed futuristic pitch/filter is applied.

## Integration, rather than replacement

- The existing PySide6 window, native gear, Three.js renderer, WebChannel health boundary, local
  assets, profile privacy, settings database, credential vault and all provider probes remain.
- `head.js` retains the original eye/lid/jaw geometry and animation rig. `hologram.js` samples its
  actual surfaces into a GPU point cloud and adds a transparent bust, collar/shoulder channels,
  circular chest reactor, cyan orbital scans and an orange/yellow facial energy shader.
- A GPU displacement shader disperses thousands of surface points and reconstructs them back
  onto the original geometry. Surfaces fade with the same dissolve parameter. A manual cycle has
  a cooldown so it cannot immediately overlap an ambient cycle. Animation-speed changes advance
  a continuous clock rather than jumping the effect phase.
- Default balanced particle count is 7,000. Performance defaults to 2,400; high to 15,000. Density
  adjusts these budgets with an absolute cap of 20,000 sampled particles, plus 110 sparse ambient
  points. Buffer attributes are allocated once and the draw range changes; each frame does not
  rebuild particle geometry or transfer thousands of positions from Python.
- Idle/listening/thinking/speaking use the existing typed states. Listening boosts eyes/particles;
  thinking accelerates orbital scans; idle breathes and periodically dissolves/reassembles.
- Advanced effects and ambient motion can be disabled independently. The 30/45/60 FPS and
  pixel-ratio caps remain. WARP software rendering remains available and separately verified.

## Real speech and synchronization

`app/speech/sapi.py` synthesizes plain text into a Windows SAPI memory stream on a worker.
The adapter explicitly disables XML/filename interpretation, uses cancellation and size/time bounds,
enumerates installed language capabilities and never writes a WAV or recording to disk.

`SpeechService` converts that PCM to the actual output device's native format on the worker, then
plays it through `QAudioSink`. A 25 ms timer reads `processedUSecs()` and measures the original
PCM samples at that playback time. The resulting envelope drives the real jaw, orange facial
energy, particles and chest glow. A speaking flag does not generate a repeating fake waveform.
This is amplitude synchronization, not phoneme/viseme lip reading. Driver/device buffering can
introduce small alignment differences; it is not a claim of sample-perfect visual timing.

The actual Qt Windows engines advertise PCM synthesis capability, but the installed PySide6 6.8
bindings do not expose the templated `QTextToSpeech.synthesize` method. The SAPI memory-stream
adapter provides real PCM without replacing Qt or upgrading the rendering architecture.

Stopping increments a generation token, cancels pending synthesis/recognition/inference, resets
the audio sink to flush queued device audio, sends zero amplitude and clears jaw/energy immediately.
Stale worker results are ignored. A new microphone turn then enters listening only when capture
actually becomes active. `Ctrl+Backspace` stops everything and returns to idle.

## Microphone, recognition and local reply

`Ctrl+Space` stops speech and starts one microphone turn after the per-session consent prompt.
It requires an explicitly selected local Faster-Whisper model and optional recognition dependencies.
Capture uses the microphone's preferred native format, resamples in memory to 16 kHz mono PCM,
and ends after approximately 0.9 seconds of silence or 15 seconds maximum. Input memory is bounded.
Frames/audio are never uploaded or saved. Closing the window releases capture and playback.

Faster-Whisper loads local weights only, with CPU int8, four threads, VAD, language auto/English/
Sinhala and no previous-transcription conditioning. Recognition and stateless Ollama inference
run off the Qt thread. A new turn invalidates old work. Ollama uses the existing provider/model/URL
preferences, a 2K context and bounded output. Only a loopback Ollama endpoint is permitted by this
voice-reply adapter. It neither issues PC actions nor claims that an action happened.

Optional cloud connection probes are preserved, but live voice generation through cloud providers
is not added here. No Ollama server/model was available for live inference validation on the target
machine. Contract tests verify its streaming protocol, error handling and local endpoint boundary.

This is push-to-talk activation with silence-based turn completion. Always-on Hey MANEXA detection,
acoustic barge-in/echo cancellation, camera tracking, PC automation and reminders remain pending.
Keyboard interruption is immediate; no untested always-on voice-interruption claim is made.

## Sinhala, Singlish and reference voice limitations

- On this computer, SAPI exposes Microsoft David Desktop and Microsoft Zira Desktop, both English.
  No Sinhala voice is installed. A Sinhala utterance is rejected before any partial utterance plays;
  it is not read through an English substitute.
- Mixed Sinhala/English script is split into language runs and requires an appropriate installed
  voice for every run. The saved voice is used when it supports that run; Windows/default matching
  voice selection is stable for the other language.
- Latin-script Singlish cannot be reliably separated from English using script detection. The
  explicit Sinhala/Singlish language hint routes it to a Sinhala voice if one is installed; it does
  not transliterate arbitrary romanized Sinhala or guarantee its pronunciation. Natural Singlish
  understanding and Sinhala recognition accuracy require real speaker tests.
- The English recognizer was tested using an actual SAPI-generated test utterance passed through
  the real local Faster-Whisper model. That validates decoding, not human Sinhala/accent accuracy.
- A suitable reference video/audio and a Sinhala-capable TTS voice are still needed before claiming
  a matching multilingual voice experience. No cloud voice, paid API or unofficial voice wrapper
  is selected automatically.

## Settings and controls

Appearance adds persistent particle density, animation speed, advanced effects and a reconstruction
button, while preserving quality, glow, motion and fullscreen. Voice settings add real installed
voice enumeration, SAPI engine selection, rate -5…+5 (0 is the unchanged Windows rate), a test
sentence/play/stop control, language hint, microphone device and local recognition model folder.
The scrollable settings content fits smaller screens. Cancel discards preference edits; a voice
preview uses unsaved voice/rate choices only for that preview.

Old version-1 SQLite preference JSON loads the new fields using defaults and keeps existing model,
endpoint, appearance and credential scope. Nothing overwrites the database on startup.

| Control | Action |
|---|---|
| Gear / Ctrl+, | Existing settings |
| F11 / Esc | Existing fullscreen controls |
| Ctrl+D | Dissolve and reconstruct (requires motion and advanced effects enabled) |
| Ctrl+Space | Interrupt playback; capture one real turn after configuration/consent |
| Ctrl+Backspace | Stop capture, synthesis, inference response delivery and playback |
| Voice settings → Speak test sentence | Actual local synthesis/playback and synchronized animation |

## Model setup and verification

```powershell
.\scripts\setup.ps1 -Development
.\.venv\Scripts\python.exe -m pip install -r requirements-voice.txt
.\.venv\Scripts\python.exe -m scripts.download_asr --model base --directory models\whisper-base
```

The download command is an explicit network operation, not application startup behavior. Select
the resulting absolute model folder in Voice settings and save. Multilingual `small` is a quality
option (`--model small --directory models\whisper-small`) with more CPU/RAM cost. Neither is an
English-only `.en` model. Ollama/model setup remains in the main README.

```powershell
.\scripts\verify.ps1
.\scripts\verify.ps1 -SoftwareRendering
.\.venv\Scripts\python.exe -m scripts.check_voice
# Explicit extra hardware check: opens the microphone briefly, RAM-only, then releases it.
.\.venv\Scripts\python.exe -m scripts.check_voice --microphone
```

Standard verification is silent and does not open devices. The voice check intentionally speaks
a test sentence through the real installed voice. Its report distinguishes actual playback,
measured envelopes, rendered mouth/core energy, stopping, and optional real microphone activity.
No synthetic speech-recognition result or fake model reply is used in the application.

Primary API references: [SAPI Speak flags](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/ms720892(v=vs.85)),
[Qt AudioSink](https://doc.qt.io/qt-6/qaudiosink.html),
[Qt speech engines](https://doc.qt.io/qtforpython-6.8/overviews/qttexttospeech-engines.html),
[Faster-Whisper](https://github.com/SYSTRAN/faster-whisper),
[Ollama chat](https://docs.ollama.com/api/chat).
