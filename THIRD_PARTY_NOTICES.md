# Third-party notices

The original MANEXA source and procedural geometry are MIT licensed; see [LICENSE](LICENSE).
Dependency licenses are separate from the project's own source license.

## Bundled Three.js

- Version: **0.170.0** (r170), used for WebGL2 compatibility with Qt 6.8 Chromium.
- Project: https://github.com/mrdoob/three.js
- License: MIT; complete notice is bundled in
  [app/ui/web/vendor/THREE-LICENSE.txt](app/ui/web/vendor/THREE-LICENSE.txt).
- Distribution: https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js
- SHA-256: `ce1fa418de16a19495a9f72495580e3015d7745c296d3ce0485897f902ddedfb`
- License SHA-256: `4c40a1ef62450b857c3b2aaf294936304cd552d965fbcd9d32d4c5bcf4ba4454`

The files are vendored unchanged. No CDN requests are made at runtime. Verify with
`python -m scripts.verify_vendor`. Upgrade by reviewing API/Qt WebGL compatibility, replacing
the distribution and notice, updating both hashes, and rerunning renderer verification.

## Installed Python packages

PySide6/Qt are provided under their respective LGPLv3/GPL/commercial terms. See
[Qt licensing](https://doc.qt.io/qtforpython-6/licenses.html) and the notices supplied in the
installed wheels. Distributing a packaged application requires preserving the applicable notices
and meeting the selected license's requirements. httpx, keyring, psutil and all transitive packages
retain their own licenses. Python itself and its SQLite library retain their respective licenses.

## Retained legacy facial geometry (not rendered by 0.2.3)

The retained, unused face asset adapts the **MediaPipe canonical face model**, Copyright The MediaPipe Authors,
under [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).

- Pinned source: [canonical_face_model.obj, MediaPipe v0.10.14](https://github.com/google-ai-edge/mediapipe/blob/v0.10.14/mediapipe/modules/face_geometry/data/canonical_face_model.obj).
- Source SHA-256: `8bac80443397e113f41a8b565ea72c59390bc031d9defab289dba7bc0c54e618`.
- Full legacy license is retained in the repository at [MEDIAPIPE-LICENSE.txt](app/ui/web/vendor/MEDIAPIPE-LICENSE.txt).
- Changes: neutralized head-only proportions, opened eye/lip cavities, added a procedural cranium
  and small ears, smoothed with one Loop subdivision, then resampled the front into a fine irregular
  network. The application adds cyan/blue line, point, iris and restrained glow shaders.
- Derived [face-geometry.js](app/ui/web/vendor/face-geometry.js) SHA-256:
  `7a1ce1b1a2354ac8a5864e6d1783cef4b3d1d6398c5f35e45387a04f68e97bde`.
- The canceled face-development converter is archived in local development artifacts. The current
  orb is original procedural geometry and does not import this asset or require MediaPipe. The
  0.2.4 wheel excludes legacy face geometry and its unused renderer assets.

## Previous facial geometry (0.2.1, no longer rendered)

The cyan network head adapts **Infinite, 3D Head Scan by Lee Perry-Smith**, based on work at
[triplegangers.com](https://www.triplegangers.com/), distributed under
[Creative Commons Attribution 3.0 Unported](https://creativecommons.org/licenses/by/3.0/).

- Source: [three.js r170 LeePerrySmith.glb](https://github.com/mrdoob/three.js/blob/r170/examples/models/gltf/LeePerrySmith/LeePerrySmith.glb).
- Original attribution: [LeePerrySmith_License.txt](app/ui/web/vendor/LeePerrySmith_License.txt).
- Original GLB SHA-256: `402b8a8ac9f03232e6d64b5962929703a069daf99d3c49ac8eb0e48bedc9c576`.
- Historical geometry-only adaptation SHA-256:
  `73279330cc63e6c20993cc38280aad6a03a45f9b1ac0c68a0ce61539816cf596`.
- Changes: removed shoulders, shortened the neck, normalized coordinates and welded UV seams.
  The renderer perturbs topology along its surface and adds custom blinking, jaw deformation,
  cyan particles and network lines. No original skin textures or photographic materials are used.
- This older conversion is retained only in local development artifacts. The current
  face converter is also archived locally; the current renderer uses procedural particles only.

The geometry retains its CC BY 3.0 terms; the project's MIT license applies to original application
code. No raster head image, audio recording or ML model weight is bundled.

