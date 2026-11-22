// Shared assistant-state, measured-speech energy and particle reconstruction lifecycle.
import * as THREE from './vendor/three.module.js';

export function enhanceHologram(rig){
  const root=new THREE.Group();
  let dissolve=0,maximumDissolve=0,manualStart=-100,energy=0,scanTravel=0;
  return {
    root,
    resetSpeech(){energy=0;},
    trigger(time){manualStart=time;},
    update({time,delta,state,level,settings}){
      const advanced=settings.advancedEffects&&settings.motion;
      let cycle=(time%28)-15;
      if(time-manualStart<12)cycle=time-manualStart<6?time-manualStart:-1;
      const target=advanced&&state==='idle'&&cycle>=0&&cycle<6
        ?Math.sin(Math.PI*Math.min(cycle/6,1))**2:0;
      dissolve=THREE.MathUtils.damp(dissolve,target,7,delta);
      maximumDissolve=Math.max(maximumDissolve,dissolve);
      energy=THREE.MathUtils.damp(energy,state==='speaking'?level:0,state==='speaking'?24:80,delta);
      const cap=settings.quality==='performance'?2400:settings.quality==='high'?15000:7000;
      const count=Math.min(20000,Math.floor(cap*settings.particleDensity));
      const pixel=Math.min(window.devicePixelRatio||1,settings.quality==='performance'?1:1.5);
      rig.setEffects({dissolve,energy,count,advanced:settings.advancedEffects,
        pointScale:pixel*(settings.quality==='performance'?1.25:1)});
      scanTravel+=settings.motion?delta*(state==='thinking'?1.9:0.16)*settings.animationSpeed:0;
    },
    diagnostics(){return{dissolve,maximumDissolve,speechEnergy:energy,scanTravel,
      chestCore:false,shoulders:false,dottedShoulders:false,wireShoulders:false,
      solidBust:false,orbitalRings:false,warmFace:false};},
  };
}
