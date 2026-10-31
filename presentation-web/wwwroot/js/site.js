(() => {
"use strict";
const $=(s,root=document)=>root.querySelector(s);
const $$=(s,root=document)=>[...root.querySelectorAll(s)];
const modelImages={
 closeup:{src:"/images/leaf-photo.jpg",alt:"A young tomato plant photographed close up, with water droplets on its leaves",caption:"A CLOSER LOOK AT THE CROP"},
 far:{src:"/images/field-photo.jpg",alt:"A real aerial photograph of parallel crop rows",caption:"A WIDER VIEW OF THE FIELD"},
 fire:{src:"/images/fire-photo.jpg",alt:"Visible smoke and a wildfire burning across a hillside",caption:"RECOGNIZING VISIBLE HAZARDS"}
};
function chooseModel(key){
 const selected=modelImages[key];if(!selected)return;
 $$("[data-model]").forEach(b=>{const on=b.dataset.model===key;b.setAttribute("aria-expanded",String(on));$("#"+b.getAttribute("aria-controls")).hidden=!on;b.closest(".model-item").classList.toggle("is-open",on);});
 const img=$("#intelligence-image");img.src=selected.src;img.alt=selected.alt;$("#intelligence-caption").textContent=selected.caption;
}
$$("[data-model]").forEach(b=>b.addEventListener("click",()=>chooseModel(b.dataset.model)));
const flow={
 capture:{title:"Different sources. One starting point.",description:"Capture a plant photo on a mobile phone, connect an accessible fixed or USB camera feed, or use imagery from a drone or rover. Photos, video frames and recordings enter the shared analysis pipeline.",tags:["Fixed / IP cameras","Mobile phones","USB cameras","Drone & rover feeds","Recorded video"]},
 analyze:{title:"The right model for the perspective.",description:"The selected AI model processes the image to identify supported plant conditions or visible fire and smoke. Each model serves a specific image type and monitoring purpose.",tags:["Close-up plant imagery","Distant imagery","Fire & smoke","Python inference"]},
 confirm:{title:"A meaningful event, with evidence.",description:"For continuous monitoring, sustained detections pass through a confirmation step. The event brings together the evidence image, condition, confidence and capture time.",tags:["Temporal confirmation","Image evidence","Capture time","Event history"]},
 review:{title:"A clearer picture on the phone.",description:"The Flutter application brings detection images and event information together for review. The farmer can follow the observation from the original image to the recorded result.",tags:["Flutter application","Detection images","Event details","Monitoring history"]}
};
function chooseStep(key,focus=false){
 const step=flow[key];if(!step)return;
 $$(".flow-step").forEach(b=>{const on=b.dataset.step===key;b.classList.toggle("active",on);b.setAttribute("aria-selected",String(on));b.tabIndex=on?0:-1;if(on&&focus)b.focus();});
 $("#flow-panel").setAttribute("aria-labelledby","flow-"+key);$("#flow-title").textContent=step.title;$("#flow-description").textContent=step.description;
 $("#flow-tags").replaceChildren(...step.tags.map(text=>{const el=document.createElement("span");el.textContent=text;return el;}));
}
$$(".flow-step").forEach(b=>b.addEventListener("click",()=>chooseStep(b.dataset.step)));
const films={drone:{src:"/media/drone.mp4",poster:"/images/drone-photo.jpg",caption:"AgroSentinel / The aerial perspective"},rover:{src:"/media/rover-web.mp4",poster:"/images/rover-photo.jpg",caption:"AgroSentinel / The ground perspective"}};
const video=$("#project-video");let currentFilm="drone";
function chooseFilm(key,focus=false){
 const film=films[key];if(!film)return;
 if(currentFilm!==key){video.pause();video.poster=film.poster;video.querySelector("source").src=film.src;video.load();currentFilm=key;}
 $$("[data-film]").forEach(b=>{const on=b.dataset.film===key;b.setAttribute("aria-selected",String(on));b.tabIndex=on?0:-1;if(on&&focus)b.focus();});
 $("#film-panel").setAttribute("aria-labelledby","film-tab-"+key);$("#film-caption").textContent=film.caption;video.setAttribute("aria-label","AgroSentinel "+key+" project film");
}
$$("[data-film]").forEach(b=>b.addEventListener("click",()=>chooseFilm(b.dataset.film)));
$$("[data-play]").forEach(b=>b.addEventListener("click",()=>{chooseFilm(b.dataset.play);$("#films").scrollIntoView({behavior:matchMedia("(prefers-reduced-motion: reduce)").matches?"instant":"smooth"});video.play().catch(()=>video.focus({preventScroll:true}));}));
function enableTabKeys(selector,attribute,select){
 const buttons=$$(selector);buttons.forEach((b,i)=>b.addEventListener("keydown",e=>{
 let next;
 if(e.key==="ArrowRight"||e.key==="ArrowDown")next=(i+1)%buttons.length;
 else if(e.key==="ArrowLeft"||e.key==="ArrowUp")next=(i-1+buttons.length)%buttons.length;
 else if(e.key==="Home")next=0;else if(e.key==="End")next=buttons.length-1;else return;
 e.preventDefault();select(buttons[next].dataset[attribute],true);
 }));
}
enableTabKeys(".flow-step","step",chooseStep);enableTabKeys("[data-film]","film",chooseFilm);
const menu=$(".menu-toggle"),nav=$("#navigation");
function closeMenu(){menu.setAttribute("aria-expanded","false");menu.setAttribute("aria-label","Open navigation");nav.classList.remove("open");}
menu.addEventListener("click",()=>{const open=menu.getAttribute("aria-expanded")!=="true";menu.setAttribute("aria-expanded",String(open));menu.setAttribute("aria-label",open?"Close navigation":"Open navigation");nav.classList.toggle("open",open);});
$$(".navigation a").forEach(a=>a.addEventListener("click",closeMenu));
document.addEventListener("keydown",e=>{if(e.key==="Escape")closeMenu();});
document.addEventListener("click",e=>{if(!e.target.closest(".header"))closeMenu();});
if("IntersectionObserver" in window){const observer=new IntersectionObserver(entries=>{for(const entry of entries)if(entry.isIntersecting)$$(".navigation a").forEach(a=>{const on=a.hash==="#"+entry.target.id;a.classList.toggle("current",on);if(on)a.setAttribute("aria-current","location");else a.removeAttribute("aria-current");});},{rootMargin:"-20% 0px -60% 0px"});$$("main section[id]").forEach(s=>observer.observe(s));}
})();
