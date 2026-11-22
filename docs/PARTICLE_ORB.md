# Blue particle orb — 0.2.3

The user's latest spherical particle reference supersedes all earlier facial concepts. The main
screen now shows a blue orb on black: a gently rippling membrane of points, a dim moving inner
nucleus and sparse nearby dust. No face, neck, shoulders, mesh texture or supplied raster image
is rendered. Earlier generated face previews are historical concepts only.

The centered **MANEXA** name uses six widely spaced blue letters with soft glow, a subtle breathing
animation and a staggered shimmer. It stays upright while the orb moves. Measured speech energy
adds a restrained brightness pulse and resets immediately on interruption. Text animation follows
the existing motion/speed settings and the system's reduced-motion preference. No remote font or
image is loaded, and the overlay does not intercept the native settings or keyboard controls.

`orb.js` uses one GPU point batch with a maximum allocation of 20,000 particles. The existing
PySide6 window, local Three.js r170 renderer, WebChannel interface, saved settings and real voice
pipeline remain. An unlit shader supplies the color, so the old environment map and scene lights
are no longer created. The sphere does not require an external model or network request.

Idle motion comes from slow 3D rotation and several smooth spatial waves. Inner particles move
independently. Listening adds a restrained energy increase; thinking speeds rotation and a scan
through the cloud. Actual PCM playback amplitude drives radial expansion, membrane turbulence,
nucleus expansion and brightness. Merely entering the speaking state does not manufacture a
fake waveform. Stopping playback immediately resets the speech response; idle movement continues.
Synchronization is amplitude-based, subject to device buffering, rather than sample-perfect.

Quality retains 2,400 / 7,000 / 15,000 particles and 30 / 45 / 60 FPS caps. Density changes the draw
range, with an absolute 20,000-point cap. Glow, animation speed, ambient motion and advanced effects
continue to use existing saved settings. Disabling advanced effects suppresses outer dust and fine
turbulence; the main orb and audio response remain. `Ctrl+D` disperses and reconstructs the cloud.

Voice engine, language handling, local recognition and inference are unchanged. No reference
audio was supplied, so the installed voice has not been altered to an invented reference sound.
See [voice setup and current limits](HOLOGRAM_UPGRADE.md).
