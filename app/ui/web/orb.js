// A living particle membrane and a softly moving inner nucleus, rendered in one draw call.
import * as THREE from './vendor/three.module.js';

export function createOrb(){
  const root=new THREE.Group(),maximum=20000;
  const uniforms={uTime:{value:0},uGlow:{value:1},uSpeech:{value:0},
    uDissolve:{value:0},uListening:{value:0},uThinking:{value:0},uPointScale:{value:1},uAdvanced:{value:1}};
  let seed=40291;
  const random=()=>{seed=(seed*16807)%2147483647;return seed/2147483647;};
  const points=[],layers=[],seeds=[];
  // Shuffle a spherical grid so every quality/density setting covers the complete orb.
  const order=Array.from({length:maximum},(_,i)=>i);
  for(let i=order.length-1;i>0;i--){
    const j=Math.floor(random()*(i+1));[order[i],order[j]]=[order[j],order[i]];
  }
  order.forEach(index=>{
    const latitude=(Math.floor(index/200)+0.5)/100*Math.PI;
    const longitude=(index%200)/200*Math.PI*2;
    const layer=random()<0.20?1:random()<0.08?2:0;
    const radius=layer===1?0.48+random()*0.35:layer===2?1.53+random()*0.16:1.45;
    points.push(Math.sin(latitude)*Math.cos(longitude)*radius,
      Math.cos(latitude)*radius,Math.sin(latitude)*Math.sin(longitude)*radius);
    layers.push(layer);seeds.push(random());
  });
  const geometry=new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.Float32BufferAttribute(points,3));
  geometry.setAttribute('aLayer',new THREE.Float32BufferAttribute(layers,1));
  geometry.setAttribute('aSeed',new THREE.Float32BufferAttribute(seeds,1));
  const material=new THREE.ShaderMaterial({
    uniforms,transparent:true,depthWrite:false,blending:THREE.AdditiveBlending,
    vertexShader:`
      uniform float uTime,uGlow,uSpeech,uDissolve,uListening,uThinking,uPointScale,uAdvanced;
      attribute float aLayer,aSeed;varying float vAlpha;varying vec3 vColor;
      mat3 rotateY(float a){float c=cos(a),s=sin(a);return mat3(c,0.,-s,0.,1.,0.,s,0.,c);}
      void main(){
        float t=uTime;vec3 n=normalize(position);
        float wave=sin(n.x*4.5+t*0.67)*sin(n.y*5.2-t*0.51)*sin(n.z*4.1+t*0.43);
        float ripple=sin(n.x*11.+n.y*8.-t*0.72)*sin(n.z*9.+n.y*5.+t*0.41);
        float breath=sin(t*1.1)*0.012;
        vec3 p=position;
        if(aLayer<0.5){
          p*=1.+breath+wave*(0.035+uAdvanced*0.03+uSpeech*0.16)
            +ripple*(0.018+uSpeech*0.035)*uAdvanced+uSpeech*0.085;
          p=rotateY(t*(0.065+uThinking*0.10))*p;
        }else if(aLayer<1.5){
          p*=1.+wave*0.20+uSpeech*0.22;
          p=rotateY(-t*0.23)*p;
          p.y+=sin(t*0.8+p.x*4.)*0.08;
        }else{
          p*=1.+wave*0.055+uSpeech*0.08;
          p=rotateY(t*0.035)*p;
        }
        p+=vec3(cos(aSeed*31.+t*0.2),sin(aSeed*43.),sin(aSeed*19.))*uDissolve*(1.4+aSeed);
        vec4 mv=modelViewMatrix*vec4(p,1.);
        vec3 normal=normalize(normalMatrix*normalize(p));
        float facing=dot(normal,normalize(-mv.xyz));
        float rim=pow(1.-abs(facing),3.);
        float glint=pow(aSeed,14.)*0.30;
        float brightness=0.09+rim+glint;
        if(facing<0.)brightness*=0.40;
        if(aLayer>0.5&&aLayer<1.5)brightness=0.20+glint*0.55;
        if(aLayer>1.5)brightness=(0.065+glint*0.60)*uAdvanced;
        float scan=pow(0.5+0.5*sin(p.y*6.-t*(1.+uThinking*2.)),12.);
        vAlpha=brightness*(1.+uSpeech*0.75+uListening*0.18+scan*uThinking*0.35)*uGlow*1.25;
        vColor=mix(vec3(0.015,0.25,0.85),vec3(0.015,0.62,1.10),rim*0.8);
        gl_PointSize=clamp((9.+aSeed*8.+rim*4.+uSpeech*3.)*uPointScale/max(1.,-mv.z),1.,4.);
        gl_Position=projectionMatrix*mv;
      }`,
    fragmentShader:`varying float vAlpha;varying vec3 vColor;void main(){
      float r=length(gl_PointCoord-0.5)*2.;if(r>1.)discard;
      gl_FragColor=vec4(vColor,vAlpha*exp(-r*r*3.5));}`,
  });
  const cloud=new THREE.Points(geometry,material);
  cloud.frustumCulled=false;root.add(cloud);
  let response=0,pointCount=7000;
  return{
    root,
    resetSpeech(){response=0;uniforms.uSpeech.value=0;},
    setEffects({dissolve,energy,count,pointScale,advanced}){
      uniforms.uDissolve.value=dissolve;uniforms.uSpeech.value=energy;
      uniforms.uPointScale.value=pointScale;
      uniforms.uAdvanced.value=advanced?1:0;
      pointCount=Math.min(maximum,count);geometry.setDrawRange(0,pointCount);
    },
    update({time,delta,state,level,motion,glow}){
      uniforms.uTime.value=motion?time:0;uniforms.uGlow.value=glow;
      uniforms.uListening.value=state==='listening'?1:0;
      uniforms.uThinking.value=state==='thinking'?1:0;
      const target=state==='speaking'?level:0;
      response=THREE.MathUtils.damp(response,target,target>response?24:20,delta);
    },
    diagnostics(){return{visualStyle:'blue-particle-orb',face:false,neck:false,shoulders:false,
      innerNucleus:true,particleCount:pointCount,orbResponse:response,
      radialExpansion:uniforms.uSpeech.value*0.085,
      scanSpeed:uniforms.uThinking.value?3:1,scanTime:uniforms.uTime.value,
      listeningEnergy:uniforms.uListening.value,sourceTriangles:0};},
  };
}
