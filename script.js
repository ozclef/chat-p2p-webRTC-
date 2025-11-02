
// p2p-ephemeral script.js
// Very lightweight WebRTC P2P chat + local contacts + consent banner.
// NOTE: This is a demo foundation. Read comments and PRIVACY.md before deploying.

const APP_KEY = 'p2p_ephemeral_v1';
const KEY_PREFS = 'p2p_prefs_v1';
let USE_STORAGE = false;
let contacts = [];
let pc = null, dc = null;
const ICE_CONFIG = { iceServers: [{ urls: "stun:stun.l.google.com:19302" }] };

const nickEl = document.getElementById('nick');
const autoDeleteEl = document.getElementById('autoDelete');
const consentStoreEl = document.getElementById('consentStore');
const savePrefsBtn = document.getElementById('savePrefs');
const clearAppBtn = document.getElementById('clearApp');

const contactsListEl = document.getElementById('contactsList');
const contactNameEl = document.getElementById('contactName');
const contactSerialEl = document.getElementById('contactSerial');
const addContactBtn = document.getElementById('addContact');
const exportContactsBtn = document.getElementById('exportContacts');
const importContactsInput = document.getElementById('importContacts');
const importBtn = document.getElementById('importBtn');

const createOfferBtn = document.getElementById('createOffer');
const prepareAnswerBtn = document.getElementById('prepareAnswer');
const applySignalBtn = document.getElementById('applySignal');
const downloadSignalBtn = document.getElementById('downloadSignal');
const signalArea = document.getElementById('signalArea');
const qrcodeDiv = document.getElementById('qrcode');
const toQRBtn = document.getElementById('toQR');
const showSerialBtn = document.getElementById('showSerial');
const readerDiv = document.getElementById('reader');
const manualSerialEl = document.getElementById('manualSerial');
const applyManualBtn = document.getElementById('applyManual');

const logEl = document.getElementById('log');
const msgEl = document.getElementById('msg');
const sendBtn = document.getElementById('send');

const consentBanner = document.getElementById('consentBanner');
const acceptCookies = document.getElementById('acceptCookies');
const rejectCookies = document.getElementById('rejectCookies');

// load prefs if allowed
function loadPrefs(){
  try{
    const saved = JSON.parse(localStorage.getItem(KEY_PREFS) || 'null');
    if(saved){
      consentStoreEl.checked = !!saved.store;
      nickEl.value = saved.nick || '';
      autoDeleteEl.value = saved.auto || 10;
      USE_STORAGE = !!saved.store;
      if(USE_STORAGE) loadContactsFromStorage();
    } else {
      // show consent
      consentBanner.style.display = 'block';
    }
  }catch(e){ consentBanner.style.display = 'block'; }
}
loadPrefs();

acceptCookies && (acceptCookies.onclick = ()=>{ consentStoreEl.checked = true; USE_STORAGE = true; persistPrefs(); consentBanner.style.display='none'; appendSystem('Consent accepted. Preferences will be stored locally.'); });
rejectCookies && (rejectCookies.onclick = ()=>{ consentStoreEl.checked = false; USE_STORAGE = false; localStorage.removeItem(KEY_PREFS); consentBanner.style.display='none'; appendSystem('Consent rejected. Nothing will be stored.'); });

function appendSystem(text){ const d = document.createElement('div'); d.className='meta'; d.textContent = text; logEl.appendChild(d); logEl.scrollTop = logEl.scrollHeight; }
function appendMsg(text, mine=false){ const d = document.createElement('div'); d.className='msg'; d.textContent = text; if(mine) d.style.borderColor = '#bde0ff'; logEl.appendChild(d); logEl.scrollTop = logEl.scrollHeight; return d; }

function makeSerial(){ return (Date.now().toString(36) + '-' + Math.random().toString(36).slice(2,8)).toUpperCase(); }

/* Contacts */
function renderContacts(){ contactsListEl.innerHTML=''; if(contacts.length===0){ contactsListEl.textContent='No hay contactos.'; return; } contacts.forEach((c,idx)=>{ const el=document.createElement('div'); el.className='row'; el.style.justifyContent='space-between'; el.innerHTML = `<div><strong>${c.name}</strong> <span class="meta kbd">${c.serial}</span></div><div><button data-idx="${idx}" class="useContact">Conectar</button> <button data-idx="${idx}" class="delContact">Eliminar</button></div>`; contactsListEl.appendChild(el); }); contactsListEl.querySelectorAll('.delContact').forEach(b=>{ b.onclick = ()=>{ contacts.splice(+b.dataset.idx,1); saveContactsIfAllowed(); renderContacts(); }; }); contactsListEl.querySelectorAll('.useContact').forEach(b=>{ b.onclick = ()=>{ manualSerialEl.value = contacts[+b.dataset.idx].serial; applyManualSignal(); }; }); }

addContactBtn.onclick = ()=>{ const n = contactNameEl.value.trim(); const s = contactSerialEl.value.trim(); if(!n||!s) return alert('Nombre y serial requeridos'); contacts.push({name:n, serial:s}); saveContactsIfAllowed(); renderContacts(); contactNameEl.value=''; contactSerialEl.value=''; };

exportContactsBtn && (exportContactsBtn.onclick = ()=>{ const blob = new Blob([JSON.stringify(contacts, null, 2)], {type:'application/json'}); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download='contacts.json'; a.click(); URL.revokeObjectURL(a.href); });

importBtn && (importBtn.onclick = ()=> importContactsInput.click());
importContactsInput && (importContactsInput.onchange = (e)=>{ const f=e.target.files[0]; if(!f) return; const r=new FileReader(); r.onload=ev=>{ try{ const arr=JSON.parse(ev.target.result); if(Array.isArray(arr)){ contacts=arr; saveContactsIfAllowed(); renderContacts(); alert('Importado'); } else alert('Formato inválido'); }catch(err){ alert('JSON inválido'); } }; r.readAsText(f); });

function saveContactsIfAllowed(){ if(USE_STORAGE){ const prefs={store:true,nick:nickEl.value,auto:autoDeleteEl.value}; localStorage.setItem(KEY_PREFS, JSON.stringify(prefs)); localStorage.setItem(APP_KEY + '_contacts', JSON.stringify(contacts)); } }
function loadContactsFromStorage(){ try{ contacts = JSON.parse(localStorage.getItem(APP_KEY + '_contacts') || '[]') || []; }catch(e){ contacts = []; } renderContacts(); }

document.getElementById('clearApp').onclick = ()=>{ if(confirm('Borrarás TODO lo del app (preferencias y contactos locales). ¿Continuar?')){ localStorage.removeItem(KEY_PREFS); localStorage.removeItem(APP_KEY + '_contacts'); contacts=[]; renderContacts(); USE_STORAGE=false; consentStoreEl.checked=false; nickEl.value=''; autoDeleteEl.value=10; appendSystem('App: datos borrados localmente.'); } };

document.getElementById('savePrefs').onclick = ()=>{ USE_STORAGE = !!consentStoreEl.checked; const prefs = {store: USE_STORAGE, nick: nickEl.value, auto: autoDeleteEl.value}; if(USE_STORAGE) localStorage.setItem(KEY_PREFS, JSON.stringify(prefs)); else localStorage.removeItem(KEY_PREFS); saveContactsIfAllowed(); appendSystem('Preferencias guardadas: ' + (USE_STORAGE ? 'activo' : 'no activo')); renderContacts(); };

/* WebRTC core */
let qr = null;
function createPeer(makeChannel=false){
  pc = new RTCPeerConnection(ICE_CONFIG);
  pc.onicecandidate = (e)=>{ if(e.candidate){ const cur = signalArea.value.trim(); const line = JSON.stringify({candidate: e.candidate}); signalArea.value = cur ? (cur + '\n' + line) : line; toQR(); } };
  pc.onconnectionstatechange = ()=> appendSystem('Estado: ' + pc.connectionState);
  pc.ondatachannel = e=>{ dc = e.channel; setupChannel(); };
  if(makeChannel){ dc = pc.createDataChannel('chat'); setupChannel(); }
}
function setupChannel(){
  dc.onopen = ()=> appendSystem('-- Canal abierto --');
  dc.onclose = ()=> appendSystem('-- Canal cerrado --');
  dc.onmessage = (ev)=>{ const txt = ev.data; const el = appendMsg(txt,false); const sec = parseInt(autoDeleteEl.value||0,10)||0; if(sec>0) setTimeout(()=>{ try{ el.remove(); }catch(e){} }, sec*1000); };
}

createOfferBtn.onclick = async ()=>{ createPeer(true); const offer = await pc.createOffer(); await pc.setLocalDescription(offer); const serial = makeSerial(); const obj = {meta:{serial}, sdp: pc.localDescription}; signalArea.value = JSON.stringify(obj); toQR(); appendSystem('Oferta creada. Serial: ' + serial); };
prepareAnswerBtn.onclick = ()=>{ createPeer(false); appendSystem('Preparado para recibir oferta. Pega señal y presiona Aplicar señal.'); };
applySignalBtn.onclick = async ()=>{ await applySignalFromText(signalArea.value); };

async function applySignalFromText(text){
  if(!text) return alert('Pega la señal (JSON) en el área antes de aplicar.');
  const lines = text.trim().split('\n').map(l=>l.trim()).filter(Boolean);
  for(const ln of lines){
    try{
      const obj = JSON.parse(ln);
      if(obj.sdp){
        if(!pc) createPeer(false);
        await pc.setRemoteDescription(new RTCSessionDescription(obj.sdp));
        if(obj.sdp.type === 'offer'){
          const answer = await pc.createAnswer();
          await pc.setLocalDescription(answer);
          const ans = JSON.stringify({meta:{serial: obj.meta ? obj.meta.serial : undefined}, sdp: pc.localDescription});
          signalArea.value = ans;
          toQR();
          appendSystem('Respuesta creada. Devuélvela al iniciador.');
        } else { appendSystem('Respuesta aplicada.'); }
      } else if(obj.candidate){
        if(!pc) createPeer(false);
        try{ await pc.addIceCandidate(obj.candidate); }catch(e){ console.warn('ICE add fail', e); }
      }
    }catch(err){ console.warn('no json',ln); }
  }
}

downloadSignalBtn.onclick = ()=>{ const data = signalArea.value; if(!data) return alert('Señal vacía: genera oferta o respuesta primero.'); const blob = new Blob([data], {type:'application/json'}); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download='signal.webrtc.json'; a.click(); URL.revokeObjectURL(a.href); };

function toQR(){ const txt = signalArea.value; qrcodeDiv.innerHTML=''; if(!txt) return; qr = new QRCode(qrcodeDiv, {text: txt, width: 220, height:220}); }

/* scanner (start camera) */
let html5QrcodeScanner = null;
function startScanner(){ if(html5QrcodeScanner) return; try{ html5QrcodeScanner = new Html5Qrcode("reader"); const config = { fps: 10, qrbox: 250 }; html5QrcodeScanner.start({ facingMode: "environment" }, config, (decodedText, decodedResult)=>{ html5QrcodeScanner.stop().then(()=>{ html5QrcodeScanner = null; }).catch(()=>{ html5QrcodeScanner = null; }); signalArea.value = decodedText; appendSystem('Señal escaneada y pegada.'); }, (errorMessage)=>{}).catch(err=> appendSystem('No se pudo iniciar cámara: ' + err)); }catch(e){ appendSystem('Scanner no disponible: ' + e); } }
startScanner();

applyManualBtn && (applyManualBtn.onclick = ()=> applyManualSignal());
async function applyManualSignal(){
  const txt = manualSerialEl.value.trim();
  if(!txt) return alert('Pega serial o JSON en el campo manual.');
  if(txt.startsWith('{')||txt.startsWith('[')){ signalArea.value = txt; await applySignalFromText(txt); return; }
  const found = contacts.find(c=>c.serial === txt);
  if(found){ manualSerialEl.value = found.serial; signalArea.value = found.serial; alert('Serial encontrado en contactos. Pide al contacto el JSON de señal o archivo.'); return; }
  alert('Serial no encontrado localmente. Si tienes el JSON, pégalo en lugar del serial.');
}

/* Chat send */
sendBtn.onclick = ()=>{ const text = (nickEl.value||'Anon') + ': ' + (msgEl.value||''); if(!dc || dc.readyState !== 'open') return alert('Canal no abierto aún.'); dc.send(text); const el = appendMsg('(yo) ' + text, true); const sec = parseInt(autoDeleteEl.value||0,10)||0; if(sec>0) setTimeout(()=>{ try{ el.remove(); }catch(e){} }, sec*1000); msgEl.value=''; };

/* init render */
renderContacts();
appendSystem('Interfaz lista. Flujo: generar oferta -> compartir QR/archivo -> aplicar -> chatear.');

/* helper */
function persistPrefs(){ const prefs = {store: USE_STORAGE, nick: nickEl.value, auto: autoDeleteEl.value}; if(USE_STORAGE) localStorage.setItem(KEY_PREFS, JSON.stringify(prefs)); else localStorage.removeItem(KEY_PREFS); }
