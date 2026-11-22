# Models are provisioned explicitly

No model weights are included or downloaded at application startup.

The head and local Windows TTS need no downloaded ML weights. For real local voice replies,
install Ollama from its official Windows installer and run:

```powershell
ollama pull qwen3:1.7b
ollama list
```

Then use Settings → AI → Test connection to verify the model list. Live voice turns use the
configured loopback Ollama server after recognition. See [the voice upgrade](../docs/HOLOGRAM_UPGRADE.md).

For optional local recognition, install `requirements-voice.txt` and run
`python -m scripts.download_asr --model base --directory models/whisper-base`. Select that folder
in Voice settings. Nothing downloads at application startup. A custom wake-word model is not supplied.
Downloaded weights, recordings and credentials must not be committed to Git.

