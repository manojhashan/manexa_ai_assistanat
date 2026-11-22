# Phase 2 visual integration audit

## Audit status

**Read-only baseline audit:** completed on branch `phase2/visual-integration` at the
`phase1-0.2.4-verified` baseline.

This audit documents integration findings only. It does not change application code and does not
start voice recognition, wake-word, camera, PC automation or cloud-generation implementation.
The approved Phase 1 visual remains the blue particle orb, luminous spaced MANEXA branding,
black background and lower-right native settings gear.

## Audit scope

The following integration boundaries were reviewed:

- Application startup and command-line lifecycle
- Native Qt window, fullscreen and settings lifecycle
- Qt WebEngine profile, navigation policy and WebChannel boundary
- Three.js/WebGL startup, resize, animation and diagnostics
- Particle orb and particle dissolution/reconstruction implementation
- Settings validation, persistence and live renderer updates
- Credential and provider-save ordering
- Speech, microphone and worker cancellation boundaries
- Smoke-test and renderer verification scripts
- Bundled/packaged renderer asset checks
- Existing pytest, native-widget and renderer evidence

## Baseline verification

The verified Phase 1 baseline contains:

- 56 passing pytest/native tests
- Passing Ruff lint and format checks
- Passing bundled asset/vendor integrity checks
- Passing software-WebGL fullscreen smoke launch
- Passing 39-assertion renderer/settings integration check
- A clean working tree
- Backup branch `backup/phase1-0.2.4`
- Annotated tag `phase1-0.2.4-verified`

## Preserved contracts

The following behavior must remain unchanged during Phase 2 implementation:

1. The main scene remains a blue particle orb with a moving inner nucleus.
2. The DOM branding remains only the spaced luminous word `MANEXA`.
3. No face, neck, shoulders, humanoid body, robotic head or avatar is added.
4. No chatbot panel, conversation history, dashboard or response text is added.
5. The settings gear remains native and in the lower-right area.
6. Settings remain native Qt controls, with Save applying immediately and Cancel discarding.
7. Startup does not open the microphone or camera and does not perform public-network calls.
8. The WebEngine profile remains off the record and the renderer receives no credentials or
   operating-system command API.
9. Advanced voice and recognition behavior stays outside Phase 2 scope.

## Findings

### P1. Add a deliberate WebGL context-loss recovery path

**Evidence**

- `ScenePage.renderProcessTerminated` reports a graphics-process failure.
- `scene.js` listens to `webglcontextlost`, prevents the default action and reports a failure.
- The same renderer reports that MANEXA should be restarted.
- The JavaScript scene does not attach a `webglcontextrestored` handler.
- No automatic context recreation or recovery state is represented in `AssistantState`.

**Risk**

A GPU driver reset, remote-desktop graphics change or graphics process interruption leaves the
window in a failed state until the application is restarted. The startup/graphics warning may
also duplicate if several events report the same failure.

**Recommended fix**

- Add a bounded context-lifecycle state: healthy, lost, restoring or failed.
- On context loss, stop future frame work and surface one clear native warning.
- On `webglcontextrestored`, recreate or rebind affected Three.js resources and restore the
  latest typed renderer configuration.
- If the browser process terminates, preserve the existing explicit restart guidance.
- Add timeout and no-recovery behavior so the app cannot remain indefinitely silent.
- Do not change the orb geometry or visual contract during recovery.

**Verification**

- Real WebGL context loss and restored-context tests.
- Unit test for duplicate/late failure callbacks.
- Confirmation that the latest settings and assistant state are reapplied after recovery.

### P1. Make settings-save ordering atomic across credentials and SQLite

**Evidence**

- `SettingsDialog._save()` writes a credential to Credential Manager first.
- It writes non-secret settings to SQLite second.
- A key-ring write can succeed and the later SQLite write can fail.

**Risk**

The settings dialog may report failure or leave a credential associated with saved UI state even
though the non-secret settings did not commit. This is a partial-write state that is difficult
for users to diagnose.

**Recommended fix**

- Validate the complete draft before any external write.
- Add a small settings-save service that commits preference and credential changes with a defined
  compensation rule.
- When an API key is entered, save preferences and credentials in an explicit order and roll back
  only the credential change made by this dialog if preference persistence fails.
- If rollback itself fails, report both failures explicitly.
- Preserve existing behavior for blank keys and provider/endpoint key scoping.

**Verification**

- Simulated credential success plus SQLite failure
- Simulated Credential Manager failure plus unchanged settings
- Real Windows vault round trip
- Save, reopen and Cancel behavior

### P1. Strengthen smoke-test readiness and timeout behavior

**Evidence**

- `app.main` waits a fixed 1.5 seconds after `renderer_ready` before reading diagnostics.
- A fixed 20-second startup timeout covers all smoke launches.
- `scripts.check_renderer` uses a fixed 35-second integration timeout.
- Smoke success requires `frameCount > 1`, rendered pixels, centered branding and optional geometry.

**Risk**

The fixed waits can pass on fast machines and fail or produce incomplete evidence on loaded,
remote-desktop or software-rendering machines. The software/WARP path may be slower.

**Recommended fix**

- Introduce bounded readiness polling based on stable diagnostic frame conditions.
- Require two consecutive valid frames or a short valid-frame window instead of one timer delay.
- Separate asset-load timeout, WebGL-init timeout and diagnostics timeout.
- Preserve the fixed upper bound to prevent hung CI/processes.
- Keep software rendering as an explicit fallback rather than a successful GPU substitution.

**Verification**

- Repeat smoke launches in hardware and WARP modes
- Deliberately slow/delayed first frame test
- Startup asset/load and WebGL initialization timeout tests
- Confirmation that no screenshot/report is false-positive

### P1. Add explicit renderer-resource ownership and disposal

**Evidence**

- `scene.js` disposes geometries and materials on `pagehide`.
- It does not separately document or dispose the bloom render target.
- The full-screen quad and post-processing scene are traversed only as part of disposal indirectly;
  the target, shader material and orthographic camera share no explicit lifecycle helper.
- `window.addEventListener('pagehide', ...)` cancels the animation loop once, but does not
  detach the resize listener or global error handlers.
- `webglcontextlost` keeps the failure state while resources are still registered.

**Risk**

Repeated window/page recreation or context loss may retain GPU resources or callback references.
This can affect repeated integration tests and may grow memory in long sessions.

**Recommended fix**

- Add a single `disposeRenderer()` path owning:
  - animation frame cancellation
  - resize listener removal
  - render-target disposal
  - post-process material geometry disposal
  - orb/hologram geometries and materials
  - renderer/Three.js context disposal
  - listener cleanup
- Make it idempotent and call it from both `pagehide` and explicit context failure.
- Keep the existing visual contract and quality settings unchanged.

**Verification**

- Repeated create/destroy smoke cycles
- Repeated renderer settings/reconstruction cycles
- Process-memory or GPU-resource trend measurement
- No double-disposal or JavaScript exceptions

### P2. Add stale and canceled settings-task protection

**Evidence**

- Provider/model connection tests, hardware detection and voice enumeration run through
  `QThreadPool`.
- Dialogs track a bounded `_task` or `_voice_task`.
- `MainWindow.open_settings()` retains dialogs that have active tasks and deletes idle dialogs.
- Dialog close/reopen or main-window shutdown can leave an old task result queued.

**Risk**

An old task can update a reused dialog, stale task objects can survive UI teardown, or a result
can arrive after the user changed the draft.

**Recommended fix**

- Give every settings task a generation token or dialog-specific task identity.
- Stop or invalidate task callbacks in dialog close/shutdown.
- Avoid retaining closed dialogs merely for active tasks unless cancellation is already complete.
- Surface only the latest task result for the currently open dialog.

**Verification**

- Close/reopen during provider probe
- Close/reopen during hardware detection
- Voice refresh while dialog closes
- Shutdown with pending QRunnable tasks

### P2. Improve window and WebEngine shutdown ordering

**Evidence**

- `closeEvent()` stops voice playback before Qt closes the native window.
- Application teardown detaches the page and deletes it after `application.exec()`.
- Smoke and normal application paths share these cleanup operations.
- Settings dialogs and their `deleteLater()` objects are retained separately.
- Pending application/Qt timers are not globally identified or disabled in one owner.

**Risk**

Startup timers, settings tasks, voice jobs or WebEngine callbacks can outlive a closing window,
produce late signals or race WebEngine teardown.

**Recommended fix**

- Add an explicit application/window shutdown state.
- Centralize shutdown in `closeEvent()`/a window-owned cleanup method:
  - stop startup timer
  - stop voice/capture/playback
  - invalidate settings tasks
  - stop renderer frame loop
  - detach/delete page
  - delete dialogs/tasks safely
- Prevent `finish()` smoke callbacks from invoking cleanup twice.

**Verification**

- Normal close
- Smoke close
- Close during settings task
- Close during voice playback/capture
- Repeated launch/close cycles

### P2. Add smoke diagnostics for startup-stage failures

**Evidence**

- The startup timer reports a generic renderer initialization timeout.
- Missing local assets report a missing-asset failure.
- WebEngine load failures and graphics termination have separate user-facing paths.
- Smoke JSON currently reports only a generic error or renderer diagnostics.

**Risk**

When CI or a packaged build fails, the report does not always identify whether failure occurred
in asset validation, navigation/load, WebChannel, JavaScript initialization or WebGL.

**Recommended fix**

- Add a typed renderer/startup stage:
  - assets
  - page load
  - WebChannel
  - JavaScript/WebGL initialization
  - first stable frame
  - diagnostics
- Preserve the current public smoke result shape and add optional stage details.
- Keep reports free of credentials, URLs, key material and personal paths.

**Verification**

- Missing asset
- Invalid packaged asset
- Local navigation failure
- WebChannel failure
- WebGL unavailable/context failure

### P2. Tighten test synchronization and eliminate timing-only assumptions

**Evidence**

- Existing renderer checks combine fixed 160-1,700 ms QTimers with frame diagnostics.
- Damped pose and speech levels depend on actual frame intervals.
- The integration script separately forces occluded-window and timer/background behavior.

**Risk**

The test may pass from a favorable frame sample or wait for a state after too few real frames.
Timing-based checks can differ between hardware and WARP and are more likely to become flaky.

**Recommended fix**

- Replace fixed post-state delays with bounded polling for the requested diagnostic condition.
- Keep a global deadline for each integration phase.
- Separate frame-count checks from wall-clock duration.
- Preserve explicit test stimuli and label them as test-only.
- Add process-level result collection rather than deriving pass/fail only from a single JSON object.

**Verification**

- Repeat NVIDIA and WARP suites multiple times
- CI-like Windows runner and loaded host repetition
- Forced slow frame schedule
- No microphone, camera or network is opened

### P2. Document and harden settings migration/partial-state behavior

**Evidence**

- Settings have a versioned SQLite row and strict validation.
- Corrupt or unsupported settings raise before returning defaults.
- Unknown fields are ignored by `json.loads(..., **Settings)` through the dataclass constructor.
- Credential data is separate and endpoint-scoped.

**Risk**

Unknown-field handling and unsupported/corrupt migrations may become ambiguous as settings expand.
Partial preferences plus credentials could diverge during future Phase 11 settings work.

**Recommended fix**

- Define an explicit settings migration function and schema version policy.
- Report backups/migration failures before destructive changes.
- Keep unknown fields out of serialized state or migrate them deliberately.
- Add a settings-and-credential consistency report without exposing secret values.

**Verification**

- Existing corrupt/unsupported settings tests
- Legacy settings compatibility
- Unknown-field migration
- Credential scoping and mode/provider validation

### P3 or later. Keep device and recognition work outside this integration phase

**Evidence**

- Microphone capture is opt-in and already bounded to memory.
- Recognition and local reply code exist but were not required by the Phase 1 acceptance gate.
- Wake word and camera features are explicitly disabled.
- Roadmap phases 3 and later remain separate from visual integration.

**Risk**

Adding device lifecycle fixes to the visual audit could change already-working voice behavior or
accidentally start devices.

**Proposed boundary**

- Phase 2 may fix only common worker/window shutdown behavior required for safe visual integration.
- It must not enable capture, ASR, wake word or camera.
- It must not introduce real recognition or inference acceptance gates.
- It must not modify recognized text, voice language or provider behavior.

## Proposed implementation order

No application code should change until these findings are reviewed. If approved, implement in
small, reversible commits:

1. **Test harness synchronization**
   - Add bounded polling helpers and typed smoke stages.
   - Add regression tests that fail without the synchronization fixes.

2. **Renderer lifecycle ownership**
   - Add one idempotent renderer cleanup path.
   - Add context-loss state, restore guidance and resource cleanup.

3. **Window/task shutdown**
   - Centralize shutdown and stale-task invalidation.
   - Keep existing voice stop behavior intact.

4. **Settings save reliability**
   - Add validated preflight and credential compensation.
   - Keep provider and endpoint credential scoping unchanged.

5. **Migration and diagnostics**
   - Add migration policy only if required by tests or future settings changes.
   - Avoid unrelated schema expansion.

Each implementation commit must preserve the 56-test baseline and the existing 39-assertion
renderer behavior unless a check is intentionally replaced with a stronger equivalent.

## Phase 2 acceptance plan

Phase 2 remains complete only when:

- Both the backup branch/tag and current audit branch remain separate and identifiable.
- The blue particle orb, brand and native settings UI are visually unchanged.
- Unit/native/renderer verification passes on NVIDIA and WARP hardware paths.
- Repeated startup/close cycles do not expose resource growth or stale callbacks.
- WebGL loss and renderer-process failure have deterministic, tested behavior.
- Settings save failure cannot silently leave partial state.
- Smoke reports identify the failing startup stage.
- No face, humanoid, chatbot, dashboard, camera, wake word or recognition behavior is introduced.
- All fixes have focused Windows tests and no unrelated Phase 1 behavior changes.
