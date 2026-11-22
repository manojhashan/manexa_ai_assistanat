# Cyan network head — 0.2.1

**Historical design record.** The user replaced this direction with the
[blue particle orb](PARTICLE_ORB.md) in 0.2.3. No head is currently rendered.

This section records the previous image direction. The latest 0.2.2 reference replaces the scan
with a neutral face template, slim eye contours, blue glow and a sparse wire shoulder network.
See the current changes below.

The latest supplied image supersedes the earlier blue/orange bust description. The main scene now
shows a centered cyan head and short neck on black: fine irregular network connections, brighter
surface nodes around the crown/ears/face contour, anatomical nose/lips and small glowing irises.
Orange facial surfaces, shoulders, chest core and external orbital rings are removed.

This is an actual 3D mesh, not the supplied image used as a texture. Facial geometry adapts the
attributed Lee Perry-Smith scan; source, license and modifications are in
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md). No skin maps or photographic textures are
loaded. Original application code remains MIT; the source facial geometry is CC BY 3.0.

The existing `createHead`/`enhanceHologram` interfaces and PySide6/Three.js architecture remain.
The new renderer uses a depth surface, one network-line batch, one particle batch, and small iris
meshes. Jaw and eyelid weights deform the actual GPU-rendered facial vertices. The real speech
playback envelope drives jaw articulation and cyan facial energy; interruption resets those inputs.
Recognition, TTS, microphone consent, local AI, credential storage and saved preferences are retained.

Default balanced mode renders 7,000 particles and approximately 17,162 triangles in 10 scene draw
calls, compared with the previous bust's 49,986 triangles/202 draw calls. Performance/high quality,
particle density, glow, animation speed, ambient motion and manual dissolution controls still apply.
Processing activity is conveyed by a scan over the facial network rather than external rings.

`scripts/prepare_head_asset.py` reproduces the bundled geometry from a pinned, checksum-verified
source GLB during development. Runtime loads a local JavaScript geometry asset; it never fetches a
head model or requires a CDN. Source textures and the unused original GLB are not packaged.

Renderer verification now checks the head-only cyan style and actual absence of orange pixels,
along with speech articulation, blinking, pose, dissolution/reconstruction and performance controls.
The rendered-pixel check samples an area around the face rather than a single solid center patch,
because empty spaces between fine lines are intentional.

See [VERIFICATION.md](VERIFICATION.md) for executed checks and screenshots under `artifacts/`.

## Neutral face and blue network — 0.2.2

The latest reference asks for a softer, more balanced face rather than the earlier scanned male
likeness. The actual facial geometry now derives from the Apache-2.0 MediaPipe canonical template,
with normalized proportions, a procedural cranium, small ears and one Loop subdivision. Runtime
still uses local 3D vertex data; no raster face or MediaPipe camera/detection engine is loaded.

The large circular iris lights are replaced by slim upper/lower eye contours. The face and short
wire collar have brighter blue/cyan connections, sparse star-like glints, and a deep navy radial
background. Glow spills around front-facing nodes independently of the depth surface, avoiding
the old clipped point halos. The new reference's shoulder lines are represented by a transparent
spatial wire lattice; no solid torso, chest core or surrounding rings are introduced.

The existing state, pose, blink, measured-speech envelope and interruption inputs remain connected.
The face, node cloud and network lines share the same jaw/eyelid deformation. Particle quality,
density, glow, motion, speed and dissolve/reconstruct settings retain their existing behavior.

Current default scene: 7,000 head particles, 90 collar nodes, approximately 7,992 surface triangles
and 9 scene draw calls. Source attribution, full license and reproduction instructions are in
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).
