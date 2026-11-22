# Hardware, models and technical limits

This document includes the original model-selection rationale. For the current 0.2 implementation,
real voice capability checks and remaining limits, see [HOLOGRAM_UPGRADE.md](HOLOGRAM_UPGRADE.md).

## Detected development computer

Read using Windows CIM, Python and `nvidia-smi` during repository inspection:

| Item | Result |
|---|---|
| OS | Windows 11 Pro, build 10.0.26300 |
| CPU | AMD Ryzen 7 7435HS, 8 cores / 16 logical processors |
| System RAM | approximately 15.8 GiB (16 GB class) |
| GPU | NVIDIA GeForce RTX 3050 Laptop GPU, 4096 MiB VRAM |
| NVIDIA driver | 596.21; `nvidia-smi` advertises CUDA compatibility 13.2 |
| Existing Python | 3.13.14; launcher also contained a broken Python 3.10 entry |
| Project Python | isolated CPython 3.12.12 installed through uv |
| Ollama | not found during inspection |
| Git remote | none configured |

The CUDA number in `nvidia-smi` is the driver's supported version, **not evidence that cuBLAS or
cuDNN runtime DLLs are installed**. Do not report speech GPU acceleration ready based on it.
No OS, GPU driver, microphone, camera or startup settings are changed by this project.

## Free offline starting point

| Component | Initial selection | Hardware and quality tradeoff |
|---|---|---|
| Local reasoning | `qwen3:1.7b` through Ollama, quantized Q4 variant | Ollama lists approximately 1.4 GB model storage. Start with 2K context and short output; runtime/KV-cache/renderer overhead is additional. Use Ollama partial/CPU offload when necessary. A small model's Sinhala fluency is not assured. |
| Smaller LLM fallback | `qwen3:0.6b` | Approximately 523 MB model storage; reduced reasoning and language quality. Useful for a resource fallback, never a guarantee of equivalent answers. |
| Recognition | Multilingual Faster-Whisper `small`, CPU `int8`, 4–6 CPU threads | Leaves VRAM for the LLM and desktop. `base` is a lower-latency, lower-accuracy fallback. Never choose `.en` variants for Sinhala. Benchmark before enabling GPU. |
| English speech | Windows-installed SAPI voice initially; optional Piper English ONNX on CPU later | SAPI requires no model download but is often less natural. Piper is lightweight; each voice requires `.onnx` and `.onnx.json` files and its own license review. No voice weights are redistributed here. |
| Sinhala speech | No verified free offline model selected yet | Do not advertise offline Sinhala TTS until a voice has been installed and listened to. Piper's currently documented voice catalog does not list Sinhala. Windows voice availability must be enumerated and tested. |
| Wake word | Custom `Hey MANEXA` ONNX model for openWakeWord (not supplied) | The standard model list does not contain MANEXA. Custom training and real speaker/noise evaluation are required. Whisper phrase-gating can be a disclosed slower interim approach, not an equivalent lightweight wake detector. |
| Tracking | MediaPipe face landmarks/pose, CPU at 15–24 FPS | Load only after permission. If landmark wheel/model compatibility fails, an OpenCV Haar face-center fallback can track position but must not be called true 3D pose estimation. |
| Head | Locally bundled Three.js inside PySide6 QtWebEngine | Actual 3D mesh parts and shader animation. No static image. The procedural mechanical face is not a photorealistic sculpt or a phoneme-trained facial rig. |

Default budget: one small LLM on the GPU, ASR and TTS on the CPU, capped renderer resolution/frame
rate and camera frame rate. Do not simultaneously load large Whisper and multi-billion-parameter
LLM weights into 4 GB VRAM. Actual memory/latency figures need measurement, not estimates labeled
as benchmarks.

## Sinhala, Singlish and mixed speech

Whisper includes the `si` Sinhala language code. Support in its vocabulary is not a promise of
accuracy. Its model card explicitly reports performance variation by language, accent and dataset.
Small models can lose low-resource-language detail. Very short utterances and background music
can produce hallucinated transcription; silence gating and confidence checks are necessary.

Singlish is romanized Sinhala rather than an independent Whisper language code. ASR may return
Sinhala script, English approximations or both. A command router needs script/romanization aliases
and a real recorded test corpus. No deterministic normalizer alone establishes natural language
understanding. Short mixed-language sentences require empirical testing; forcing `si` or `en` may
help one case while hurting another. Provide auto detection and manual language preference.

Small offline language models may struggle with Sinhala grammar and mixed-script instructions.
Use deterministic routing for common local commands and disclose model limits. Response language
must also account for installed TTS capabilities.

## Sinhala voice

Microsoft documents `si-LK-ThiliniNeural` and `si-LK-SameeraNeural` as online Azure voices. Those
are not offline Windows SAPI models and Azure is not a mandatory free local solution. A future
optional online voice needs explicit provider configuration, tested availability and clear network
disclosure. Unofficial Edge service wrappers are not a guaranteed offline or stable voice backend.

No fake prerecorded greeting or English voice reading Sinhala is accepted as working Sinhala TTS.
Offline English operation can be complete while this capability remains unavailable.

## Wake word and interruption

openWakeWord's documented pretrained models are primarily English; MANEXA requires a custom
trained model with suitable negative examples and local accent evaluation. English support does
not by itself prove reliable recognition of a name pronounced in Sinhala.

An always-on ASR phrase detector costs more CPU and latency than a small wake classifier. Acoustic
echo from the assistant's own speech can self-trigger or prevent interruption. A final implementation
needs playback cancellation, fresh command capture, echo suppression or headphones, and measured
tests of barge-in. A keyboard activation fallback should remain available.

## 3D facial animation

The head uses individually animated eyelids and a hinged mechanical jaw. The 0.2 speech service
supplies measured PCM amplitude using the real output-device playback clock. This drives jaw and
facial/chest/particle energy; it is amplitude synchronization, not phoneme/viseme lip reading.
Renderer checks also inject known amplitudes to isolate geometry tests; a separate audible SAPI
check verifies the actual synthesis/playback/envelope/rendering path and interruption.

Balanced mode caps rendering at 45 FPS and pixel ratio at 1.5. Performance mode caps at 30 FPS
and pixel ratio 1. High mode permits 60 FPS and ratio 2. These are targets, not guaranteed measured
frame rates. Low-power/remote desktop environments may require software WebGL. Software mode
uses Windows Direct3D WARP (Microsoft Basic Render Driver) and more CPU; it is a compatibility
fallback, not CUDA acceleration. The installed Qt 6.8 distribution does not bundle SwiftShader;
an initial `--use-angle=swiftshader` attempt still selected the NVIDIA adapter. The corrected
configuration requests Qt's software D3D11 device and permits that adapter in Chromium.
The adapter is recorded in smoke diagnostics so a fallback claim can be verified.

## Dependencies by phase

- **Installed runtime now:** PySide6 (WebEngine, WebChannel and Multimedia), httpx, keyring,
  psutil, comtypes on Windows, standard-library SQLite; bundled Three.js and its MIT license.
- **Development now:** pytest, Ruff; setup/verify PowerShell scripts. No Node server is needed.
- **Optional recognition now:** faster-whisper and its numpy/CTranslate2/ONNX dependencies;
  Qt Multimedia captures audio. Model download is explicit; inference is local CPU int8.
- **Phase 5:** Windows SAPI/pywin32 or optional piper-tts + sounddevice. Piper's engine is GPL;
  review engine and individual model licenses before packaging a combined release.
- **Phase 6:** openwakeword/onnxruntime, trained custom model; evaluate Windows/Python wheels.
- **Phase 7:** opencv-python, mediapipe and its downloaded face-landmarker task asset where required.
- **Phase 8:** platform-specific pywin32, pycaw/comtypes, screenshot/keyboard libraries and optional
  screen-brightness-control only for implemented adapters. Wi-Fi/Bluetooth/brightness may require
  hardware support or elevation and must fail honestly.
- **Phase 10:** dateparser or a reviewed timezone-aware parser; notification adapter. Keep SQLite.

Do not install unused large ML frameworks into the Phase 1 environment. Optional dependencies
receive their own tested lock/supported Python version when their integration is implemented.

## Primary references checked during implementation

- [Qt for Python installation](https://doc.qt.io/qtforpython-6/gettingstarted.html)
- [QtWebEngineWidgets](https://doc.qt.io/qtforpython-6/PySide6/QtWebEngineWidgets/index.html)
- [Qt Windows graphics and WARP software rendering](https://doc.qt.io/qt-6/windows-graphics.html)
- [QWebEngineProfile privacy and off-the-record profiles](https://doc.qt.io/qtforpython-6/PySide6/QtWebEngineCore/QWebEngineProfile.html)
- [Three.js installation](https://threejs.org/manual/#en/installation)
- [Ollama Qwen3 tags and model sizes](https://ollama.com/library/qwen3/tags)
- [Ollama model-list API](https://docs.ollama.com/api/tags)
- [Faster-Whisper requirements and CUDA libraries](https://github.com/SYSTRAN/faster-whisper)
- [Whisper language codes](https://github.com/openai/whisper/blob/main/whisper/tokenizer.py)
- [Whisper model card and limitations](https://github.com/openai/whisper/blob/main/model-card.md)
- [openWakeWord capabilities and custom training](https://github.com/dscripka/openWakeWord)
- [Piper voice catalog](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/VOICES.md)
- [Piper licensing](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/LICENSING.md)
- [Microsoft Sinhala voice availability](https://learn.microsoft.com/azure/ai-services/speech-service/language-support)

