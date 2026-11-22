import * as THREE from './vendor/three.module.js';
import { createOrb } from './orb.js';
import { enhanceHologram } from './hologram.js';

let bridge, failure;
function fail(reason) {
  failure = reason;
  if (bridge) bridge.rendererFailed(reason);
}
function reportGlobalError() {
  fail('The 3D renderer encountered an error. Check local assets.');
}
function reportUnhandledRejection() {
  fail('The 3D renderer could not initialize.');
}
window.addEventListener('error', reportGlobalError);
window.addEventListener('unhandledrejection', reportUnhandledRejection);

new QWebChannel(qt.webChannelTransport, channel => {
  bridge = channel.objects.bridge;
  if (failure) bridge.rendererFailed(failure);
  else {
    try { start(); }
    catch (_) { fail('WebGL could not start. Try launching with --software-rendering.'); }
  }
});

function start() {
  const canvas = document.getElementById('head');
  const brand = document.getElementById('brand');
  const brandWord = brand.querySelector('.brand-word');
  let brandEnergy = 0;
  function updateBrand(energy) {
    brandEnergy = energy;
    brand.style.setProperty('--brand-energy', energy.toFixed(3));
  }
  const renderer = new THREE.WebGLRenderer({
    canvas, antialias: true, alpha: false, powerPreference: 'low-power',
  });
  renderer.setClearColor(0x000000, 1);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;
  renderer.debug.onShaderError = () => fail('A WebGL shader failed to compile. Try software rendering.');
  const context = renderer.getContext();
  canvas.addEventListener('webglcontextlost', event => {
    event.preventDefault(); fail('The graphics context was lost. Restart MANEXA.');
  });
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 40);
  camera.position.set(0, 0, 7.7);
  camera.lookAt(0, 0, 0);
  const rig = createOrb();
  scene.add(rig.root);
  const hologram = enhanceHologram(rig);
  scene.add(hologram.root);

  // Lightweight nine-tap cyan bloom, without external postprocessing assets or textures.
  let target = new THREE.WebGLRenderTarget(1, 1, { depthBuffer: true });
  const composite = new THREE.ShaderMaterial({
    depthTest: false, depthWrite: false, toneMapped: false,
    uniforms: { source: { value: target.texture }, pixel: { value: new THREE.Vector2(1, 1) },
      strength: { value: 0.30 }, aspect: { value: 1 } },
    vertexShader: `varying vec2 vUv;
      void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`,
    fragmentShader: `uniform sampler2D source; uniform vec2 pixel; uniform float strength,aspect;
      varying vec2 vUv;
      vec3 bright(vec2 offset) {
        vec3 c = texture2D(source, vUv + offset * pixel * 3.5).rgb;
        return max(c - vec3(0.10), vec3(0.0));
      }
      void main() {
        vec3 c = texture2D(source, vUv).rgb;
        vec3 halo = bright(vec2(1.,0.)) + bright(vec2(-1.,0.)) + bright(vec2(0.,1.))
          + bright(vec2(0.,-1.)) + bright(vec2(1.,1.)) + bright(vec2(-1.,1.))
          + bright(vec2(1.,-1.)) + bright(vec2(-1.,-1.));
        vec2 p=(vUv-vec2(0.5,0.55))*vec2(aspect,1.0);
        vec3 background=vec3(0.,0.0002,0.001)*exp(-dot(p,p)*8.);
        gl_FragColor = vec4(c + halo * strength * 0.125 + background, 1.0);
        #include <colorspace_fragment>
      }`,
  });
  const post = new THREE.Scene();
  post.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), composite));
  const postCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

  let settings = { quality: 'balanced', motion: true, glow: 1,
    particleDensity: 1, animationSpeed: 1, advancedEffects: true };
  let state = 'idle', requestedLevel = 0, levelTime = -1;
  let pose = { yaw: 0, pitch: 0 };
  let frameCount = 0, runningTime = 0, visualTime = 0, previous = performance.now(), lastFrame = 0;
  let readySent = false, triangles = 0, drawCalls = 0, raf;
  const quality = { performance: [30, 1], balanced: [45, 1.5], high: [60, 2] };

  function resize() {
    const width = window.innerWidth, height = window.innerHeight;
    const ratio = Math.min(window.devicePixelRatio || 1, quality[settings.quality][1]);
    renderer.setPixelRatio(ratio);
    renderer.setSize(width, height, false);
    target.setSize(Math.round(width * ratio), Math.round(height * ratio));
    composite.uniforms.pixel.value.set(1 / target.width, 1 / target.height);
    composite.uniforms.aspect.value=width/height;
    camera.aspect = width / height;
    // Keep the entire particle cloud visible in portrait windows, including speech expansion.
    camera.position.z = camera.aspect < 0.72 ? 7.7 * 0.72 / camera.aspect : 7.7;
    camera.updateProjectionMatrix();
  }
  window.addEventListener('resize', resize);
  resize();

  function diagnostics() {
    const adapterInfo = context.getExtension('WEBGL_debug_renderer_info');
    let nonBackgroundPixels = 0;
    let warmPixels = 0;
    if (frameCount) {
      // Sparse particles can legitimately leave the exact center pixel empty.
      const side = 96;
      const data = new Uint8Array(side * side * 4);
      renderer.readRenderTargetPixels(target, Math.floor(target.width / 2) - side / 2,
        Math.floor(target.height / 2) - side / 2, side, side, data);
      for (let i = 0; i < data.length; i += 4) {
        if (Math.max(data[i], data[i + 1], data[i + 2]) > 20) nonBackgroundPixels++;
        if (data[i] > 40 && data[i] > data[i+1]*1.3 && data[i] > data[i+2]*1.3) warmPixels++;
      }
    }
    const brandBounds = brandWord.getBoundingClientRect();
    const brandStyle = getComputedStyle(brandWord);
    return {
      ready: frameCount > 0 && !failure, threeRevision: THREE.REVISION,
      animationTime: runningTime,
      webgl: context.getParameter(context.VERSION), frameCount, triangles, drawCalls,
      adapter: adapterInfo ? context.getParameter(adapterInfo.UNMASKED_RENDERER_WEBGL) : 'unavailable',
      nonBackgroundPixels, warmPixels, state, quality: settings.quality, motion: settings.motion,
      glow: settings.glow, targetFPS: quality[settings.quality][0],
      bloomStrength: composite.uniforms.strength.value,
      pixelRatio: renderer.getPixelRatio(), yaw: rig.root.rotation.y, pitch: rig.root.rotation.x,
      ...rig.diagnostics(),
      ...hologram.diagnostics(),
      advancedEffects: settings.advancedEffects, animationSpeed: settings.animationSpeed,
      canvasCount: document.querySelectorAll('canvas').length,
      visibleText: document.body.innerText.replace(/\s+/g, ''),
      branding: { text: brand.textContent.replace(/\s+/g, ''),
        letterCount: brandWord.children.length, letterGap: parseFloat(brandStyle.columnGap),
        centered: Math.abs((brandBounds.left+brandBounds.right)/2-window.innerWidth/2)<1
          &&Math.abs((brandBounds.top+brandBounds.bottom)/2-window.innerHeight/2)<1,
        opacity: parseFloat(brandStyle.opacity), motion: brand.dataset.motion==='on',
        speechEnergy: brandEnergy, filter: brandStyle.filter,
        animationDuration: brandStyle.animationDuration },
    };
  }

  window.manexa = {
    configure(value) {
      if (!value || !quality[value.quality] || typeof value.motion !== 'boolean' ||
          !Number.isFinite(value.glow) || value.glow < 0.3 || value.glow > 1.8) {
        throw new TypeError('Invalid renderer configuration');
      }
      const density = value.particleDensity ?? 1, speed = value.animationSpeed ?? 1;
      const advanced = value.advancedEffects ?? true;
      if (!Number.isFinite(density) || density < 0.25 || density > 2 ||
          !Number.isFinite(speed) || speed < 0.25 || speed > 2 || typeof advanced !== 'boolean') {
        throw new TypeError('Invalid holographic effects configuration');
      }
      settings = { quality: value.quality, motion: value.motion, glow: value.glow,
        particleDensity: density, animationSpeed: speed, advancedEffects: advanced };
      composite.uniforms.strength.value = value.glow * 0.30;
      brand.dataset.motion = value.motion ? 'on' : 'off';
      brand.style.setProperty('--brand-glow', String(value.glow));
      brand.style.setProperty('--brand-breathe', `${4/speed}s`);
      brand.style.setProperty('--brand-shimmer', `${6/speed}s`);
      resize();
    },
    setState(value) {
      if (!['idle', 'listening', 'thinking', 'speaking', 'error'].includes(value)) {
        throw new TypeError('Invalid assistant state');
      }
      state = value;
      if (state !== 'speaking') {
        requestedLevel = 0; rig.resetSpeech(); hologram.resetSpeech();
        updateBrand(0);
      }
      // Interrupts reset speech response immediately, independently of frame smoothing.
      if (state === 'listening') rig.update({ time: visualTime, delta: 1,
        state, level: 0, motion: settings.motion, glow: settings.glow });
    },
    setPose(value) {
      if (!value || !Number.isFinite(value.yaw) || !Number.isFinite(value.pitch)) {
        throw new TypeError('Invalid head pose');
      }
      pose = { yaw: THREE.MathUtils.clamp(value.yaw, -0.6, 0.6),
        pitch: THREE.MathUtils.clamp(value.pitch, -0.4, 0.4) };
    },
    setSpeechLevel(value) {
      if (!Number.isFinite(value) || value < 0 || value > 1) {
        throw new TypeError('Invalid speech amplitude');
      }
      requestedLevel = value;
      levelTime = performance.now();
    },
    diagnostics,
    reconstruct() { hologram.trigger(visualTime); },
  };

  let disposed = false;
  function disposeRenderer() {
    if (disposed) return;
    disposed = true;
    cancelAnimationFrame(raf);
    window.removeEventListener('resize', resize);
    window.removeEventListener('error', reportGlobalError);
    window.removeEventListener('unhandledrejection', reportUnhandledRejection);
    canvas.removeEventListener('webglcontextlost', handleContextLost);
    canvas.removeEventListener('webglcontextrestored', handleContextRestored);
    target.dispose();
    composite.dispose();
    post.traverse(object => {
      if (object.geometry) object.geometry.dispose();
      if (object.material && !Array.isArray(object.material)) object.material.dispose();
    });
    scene.traverse(object => {
      if (object.geometry) object.geometry.dispose();
      if (object.material && !Array.isArray(object.material)) object.material.dispose();
    });
    renderer.dispose();
  }
  function handleContextLost(event) {
    event.preventEvent;
  }
  function handleContextRestored() {
    // Implemented with context restoration recovery in the Phase 2 context stage.
  }

  function animate(now) {
    raf = requestAnimationFrame(animate);
    if (document.hidden || failure || now - lastFrame < 1000 / quality[settings.quality][0]) {
      return;
    }
    const delta = Math.min((now - previous) / 1000, 0.1);
    previous = now;
    const frameInterval = 1000 / quality[settings.quality][0];
    lastFrame = now - ((now - lastFrame) % frameInterval);
    runningTime += delta;
    visualTime += delta * settings.animationSpeed;
    const time = visualTime;
    const amplitude = now - levelTime < 220 ? requestedLevel : 0;
    rig.update({ time, delta, state, level: amplitude, motion: settings.motion, glow: settings.glow });
    hologram.update({ time, delta, state, level: amplitude, settings });
    updateBrand(state==='speaking'?hologram.diagnostics().speechEnergy:0);
    const ambientYaw = settings.motion ? Math.sin(time * 0.32) * 0.025 : 0;
    const ambientPitch = settings.motion ? Math.sin(time * 0.47) * 0.018 : 0;
    rig.root.rotation.y = THREE.MathUtils.damp(rig.root.rotation.y, pose.yaw + ambientYaw, 4.5, delta);
    rig.root.rotation.x = THREE.MathUtils.damp(rig.root.rotation.x, pose.pitch + ambientPitch, 4.5, delta);
    rig.root.position.y = settings.motion ? Math.sin(time * 1.35) * 0.017 : 0;
    renderer.setRenderTarget(target);
    renderer.render(scene, camera);
    triangles = renderer.info.render.triangles;
    drawCalls = renderer.info.render.calls;
    renderer.setRenderTarget(null);
    renderer.render(post, postCamera);
    frameCount++;
    if (!readySent && !failure) {
      readySent = true;
      bridge.rendererReady(JSON.stringify(diagnostics()));
    }
  }
  raf = requestAnimationFrame(animate);
  window.addEventListener('pagehide', () => {
    disposeRenderer();
  }, { once: true });
}
