# Creating repository files and zipping them for the user.
import os, json, textwrap, shutil, zipfile, pathlib

root = '/mnt/data/chat-app-supabase'
if os.path.exists(root):
    shutil.rmtree(root)
os.makedirs(root, exist_ok=True)
os.makedirs(os.path.join(root, 'sql'), exist_ok=True)
os.makedirs(os.path.join(root, 'src'), exist_ok=True)
os.makedirs(os.path.join(root, 'utils'), exist_ok=True)
os.makedirs(os.path.join(root, 'docs'), exist_ok=True)

# Files content (trimmed and completed where needed)
readme = textwrap.dedent("""
# Chat App - Supabase (plantilla)
Esta plantilla te ayuda a desplegar un chat en Vercel usando Supabase Realtime y Postgres.

## Pasos rápidos
1. Crea un proyecto en Supabase.
2. En SQL Editor, pega `sql/init.sql`.
3. Copia `src/*` al root público de tu sitio y reemplaza `SUPABASE_URL` y `SUPABASE_ANON_KEY` en `src/app.js`.
4. Despliega en Vercel apuntando a la carpeta `src` (o haz build que copie archivos a `/`).

## Notas
- Para recibir mensajes en tiempo real usamos Supabase Realtime; no necesitas servidor WebSocket propio.
- Activa RLS y políticas si vas a producción.
- Revisa `docs/instructores_usuario.md` para manual de usuario.
""")

sql_init = textwrap.dedent("""
-- Init SQL para Supabase
create extension if not exists pgcrypto;

create table profiles (
  id uuid primary key default gen_random_uuid(),
  supabase_user_id text,
  device_id text unique,
  public_id text unique,
  username text,
  avatar_url text,
  meta jsonb,
  created_at timestamptz default now()
);

create table rooms (
  id uuid primary key default gen_random_uuid(),
  slug text unique,
  title text,
  is_public boolean default true,
  created_at timestamptz default now()
);

create table messages (
  id bigserial primary key,
  room_id uuid references rooms(id) on delete cascade,
  sender_profile_id uuid references profiles(id),
  sender_device_id text,
  sender_display text,
  content text,
  metadata jsonb,
  created_at timestamptz default now()
);

create table contacts (
  id bigserial primary key,
  owner_profile_id uuid references profiles(id) on delete cascade,
  contact_profile_id uuid references profiles(id),
  alias text,
  created_at timestamptz default now(),
  unique(owner_profile_id, contact_profile_id)
);

create index on messages (room_id, created_at);
create index on profiles (public_id);
""")

index_html = textwrap.dedent("""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Chat App - Supabase</title>
  <link rel="stylesheet" href="./styles.css">
</head>
<body>
  <header>
    <div class="brand">ChatApp</div>
    <div id="topControls">
      <button id="themeToggle">Tema</button>
      <button id="exportBtn">Exportar chats</button>
      <input id="importFile" type="file" accept="application/json" style="display:none" />
    </div>
  </header>

  <div class="app">
    <aside class="sidebar">
      <section class="profileBox">
        <h3>Perfil</h3>
        <input id="username" placeholder="elige un nombre" />
        <button id="saveUser">Guardar</button>
        <div id="publicId"></div>
      </section>

      <section class="searchBox">
        <input id="searchUser" placeholder="buscar user o id" />
        <ul id="results"></ul>
      </section>

      <section class="roomsBox">
        <h4>Salas</h4>
        <ul id="roomsList"><li><button data-slug="global">#global</button></li></ul>
      </section>

      <section class="contactsBox">
        <h4>Contactos</h4>
        <ul id="contactsList"></ul>
      </section>
    </aside>

    <main class="main">
      <div id="userInfoShort">Cargando...</div>
      <div id="messages" class="messages"></div>
      <form id="sendForm">
        <input id="msgInput" placeholder="Escribe un mensaje..." autocomplete="off" />
        <button>Enviar</button>
      </form>
    </main>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js/dist/supabase.min.js"></script>
  <script src="./app.js"></script>
</body>
</html>
""")

styles_css = textwrap.dedent("""
:root{ --bg:#0f1724; --card:#0b1220; --text:#e6eef8; --accent:#8a2be2 }
[data-theme="light"]{ --bg:#f5f7fb; --card:#ffffff; --text:#111827; --accent:#3b82f6 }
*{box-sizing:border-box}
body{margin:0;font-family:Inter,system-ui;background:var(--bg);color:var(--text)}
header{height:56px;display:flex;align-items:center;justify-content:space-between;padding:8px 12px;background:var(--card)}
.app{display:grid;grid-template-columns:300px 1fr;gap:12px;padding:12px}
.sidebar{background:var(--card);padding:12px;border-radius:10px}
.main{background:var(--card);padding:12px;border-radius:10px;display:flex;flex-direction:column}
.messages{flex:1;overflow:auto;margin-bottom:12px;display:flex;flex-direction:column;gap:6px;padding:8px}
.msg{padding:8px;border-radius:8px;margin:6px 0;max-width:75%;display:flex;flex-direction:column}
.msgRow{display:flex;gap:8px;align-items:flex-start}
.mine{align-self:flex-end;background:rgba(255,255,255,0.06);}
.other{align-self:flex-start;background:rgba(255,255,255,0.03);}
.msg .meta{font-size:12px;opacity:0.8;margin-bottom:6px;display:flex;justify-content:space-between}
.avatar{width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#444,#222);display:inline-block;flex-shrink:0;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:600}
input,button{padding:8px;border-radius:8px;border:1px solid rgba(255,255,255,0.06)}
@media (max-width:720px){.app{grid-template-columns:1fr}.sidebar{order:2}}
""")

app_js = textwrap.dedent("""
/* CONFIG - cambia por tus valores */
const SUPABASE_URL = 'https://TU-PROYECTO.supabase.co';
const SUPABASE_ANON_KEY = 'TU-ANON-KEY';
const supabase = supabaseLib.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// helpers
function genDeviceId(){ return 'd_' + Math.random().toString(36).slice(2,10); }
function shortPublicId(base, num){ return `${base}-${('00'+num).slice(-3)}` }

// estado
const state = {
  device_id: localStorage.getItem('device_id') || null,
  profile_id: localStorage.getItem('profile_id') || null,
  username: localStorage.getItem('username') || null,
  public_id: localStorage.getItem('public_id') || null,
  room_slug: 'global'
};

if(!state.device_id){ state.device_id = genDeviceId(); localStorage.setItem('device_id', state.device_id); }

// init app
(async function init(){
  try{ await supabase.auth.signInAnonymously(); }catch(e){console.warn(e)}

  const { data: existing } = await supabase.from('profiles').select('*').eq('device_id', state.device_id).limit(1);
  if(existing && existing.length){
    const p = existing[0];
    state.profile_id = p.id; state.username = p.username || state.username; state.public_id = p.public_id || state.public_id;
    localStorage.setItem('profile_id', state.profile_id);
  } else {
    const { data } = await supabase.from('profiles').insert({ device_id: state.device_id, username: state.username || null }).select().single();
    if(data){ state.profile_id = data.id; localStorage.setItem('profile_id', state.profile_id); }
  }

  document.getElementById('username').value = state.username || '';
  document.getElementById('userInfoShort').innerText = (state.username || 'Desconocido') + ' · ' + state.device_id;

  await loadRooms(); await loadMessages(); await loadContacts();
  subscribeRoom(state.room_slug);

  document.getElementById('saveUser').addEventListener('click', saveUser);
  document.getElementById('sendForm').addEventListener('submit', sendMessage);
  document.getElementById('searchUser').addEventListener('input', searchUsers);
  document.getElementById('exportBtn').addEventListener('click', exportAll);
  document.getElementById('importFile').addEventListener('change', importFile);
  document.getElementById('themeToggle').addEventListener('click', toggleTheme);

  if(Notification && Notification.permission !== 'granted'){
    setTimeout(()=>{
      if(confirm('¿Quieres activar notificaciones del navegador?')) Notification.requestPermission();
    },2000);
  }
})();

async function saveUser(){
  const val = document.getElementById('username').value.trim(); if(!val) return alert('Pon un nombre');
  const base = val.toLowerCase().replace(/[^a-z0-9]+/g,'').slice(0,12) || 'user';
  const { data: coll } = await supabase.from('profiles').select('public_id').ilike('public_id', base + '%').limit(100);
  let num = 1; if(coll) num = (coll.length||0) + 1;
  const public_id = shortPublicId(base, num);

  const { error } = await supabase.from('profiles').upsert({ id: state.profile_id, device_id: state.device_id, username: val, public_id }).select();
  if(error){ console.warn(error); alert('Error guardando'); return; }
  state.username = val; state.public_id = public_id; localStorage.setItem('username', val); localStorage.setItem('public_id', public_id);
  document.getElementById('userInfoShort').innerText = val + ' · ' + state.device_id;
  document.getElementById('publicId').innerText = 'ID público: ' + public_id;
}

async function loadRooms(){
  const { data } = await supabase.from('rooms').select('*').order('created_at', {ascending:true}).limit(50);
  const list = document.getElementById('roomsList');
  if(data) data.forEach(r=>{
    const li = document.createElement('li');
    const btn = document.createElement('button'); btn.textContent = '#' + (r.slug||r.title||'room'); btn.dataset.slug = r.slug;
    btn.addEventListener('click', ()=> changeRoom(r.slug));
    li.appendChild(btn); list.appendChild(li);
  })
}

async function loadMessages(){
  const { data: room } = await supabase.from('rooms').select('*').eq('slug', state.room_slug).limit(1);
  let roomId = room && room[0] ? room[0].id : null;
  if(!roomId){
    const res = await supabase.from('rooms').insert({ slug: state.room_slug, title: 'Global'}).select().single();
    if(res.data) roomId = res.data.id;
  }
  const { data } = await supabase.from('messages').select('*').eq('room_id', roomId).order('created_at', {ascending:true}).limit(200);
  const container = document.getElementById('messages'); container.innerHTML = '';
  if(data) data.forEach(renderMsg);
  container.scrollTop = container.scrollHeight;
}

// Completed renderMsg function (full rendering + timestamp + avatar + click to add contact)
function renderMsg(m){
  const container = document.getElementById('messages');
  const wrapper = document.createElement('div');
  wrapper.className = 'msg ' + (m.sender_device_id === state.device_id ? 'mine' : 'other');

  const row = document.createElement('div');
  row.className = 'msgRow';

  // avatar (if avatar_url exists show initials fallback)
  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  if(m.avatar_url){
    avatar.style.backgroundImage = `url(${m.avatar_url})`;
    avatar.style.backgroundSize = 'cover';
    avatar.textContent = '';
  } else {
    const name = m.sender_display || m.sender_device_id || 'U';
    const initials = name.split(' ').map(s=>s[0]).join('').slice(0,2).toUpperCase();
    avatar.textContent = initials;
  }

  // content container
  const content = document.createElement('div');
  content.style.flex = '1';

  // meta (name + timestamp + add contact button)
  const meta = document.createElement('div');
  meta.className = 'meta';
  const nameSpan = document.createElement('span');
  nameSpan.textContent = m.sender_display || (m.sender_device_id || 'Anónimo');
  const timeSpan = document.createElement('span');
  // format timestamp safely
  try{
    const dt = new Date(m.created_at || m.createdAt || Date.now());
    timeSpan.textContent = dt.toLocaleString();
  }catch(e){
    timeSpan.textContent = '';
  }
  meta.appendChild(nameSpan);
  meta.appendChild(timeSpan);

  // message body
  const body = document.createElement('div');
  body.textContent = m.content || '';

  // small controls (add contact if not mine)
  const controls = document.createElement('div');
  controls.style.marginTop = '6px';
  if(m.sender_device_id !== state.device_id){
    const addBtn = document.createElement('button');
    addBtn.textContent = 'Agregar contacto';
    addBtn.style.padding = '6px 8px';
    addBtn.addEventListener('click', async ()=>{
      // try to find profile by device_id or sender_profile_id
      let profileId = m.sender_profile_id || null;
      if(!profileId){
        const { data } = await supabase.from('profiles').select('id').eq('device_id', m.sender_device_id).limit(1);
        if(data && data.length) profileId = data[0].id;
      }
      if(profileId){
        await supabase.from('contacts').insert({ owner_profile_id: state.profile_id, contact_profile_id: profileId });
        await loadContacts();
        alert('Contacto agregado');
      } else {
        alert('No se encontró perfil para agregar');
      }
    });
    controls.appendChild(addBtn);
  }

  content.appendChild(meta);
  content.appendChild(body);
  content.appendChild(controls);

  row.appendChild(avatar);
  row.appendChild(content);
  wrapper.appendChild(row);
  container.appendChild(wrapper);
  container.scrollTop = container.scrollHeight;
}

document.getElementById('sendForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = document.getElementById('msgInput').value.trim();
  if(!text) return;
  // obtener room id
  const { data: room } = await supabase.from('rooms').select('*').eq('slug', state.room_slug).limit(1);
  let roomId = room && room[0] ? room[0].id : null;
  if(!roomId){ const r = await supabase.from('rooms').insert({ slug: state.room_slug, title: state.room_slug }).select().single(); roomId = r.data.id }
  const payload = {
    room_id: roomId,
    sender_profile_id: state.profile_id,
    sender_device_id: state.device_id,
    sender_display: state.username || ('user-'+state.device_id.slice(-4)),
    content: text
  };
  const { error } = await supabase.from('messages').insert(payload);
  if(error) console.warn(error); else document.getElementById('msgInput').value = '';
});

function subscribeRoom(slug){
  supabase.from('messages').on('INSERT', payload=>{
    renderMsg(payload.new);
    if(Notification && Notification.permission === 'granted') new Notification('Nuevo mensaje', { body: payload.new.content.slice(0,80) });
    const container = document.getElementById('messages'); container.scrollTop = container.scrollHeight;
  }).subscribe();
}

async function searchUsers(ev){
  const q = ev.target.value.trim(); const out = document.getElementById('results'); out.innerHTML = '';
  if(!q) return;
  const { data } = await supabase.from('profiles').select('id,username,public_id,device_id').or(`username.ilike.%${q}%,public_id.ilike.%${q}%`).limit(50);
  if(data) data.forEach(u=>{
    const li = document.createElement('li'); li.textContent = (u.username || 'sin nombre') + ' · ' + (u.public_id||u.device_id);
    const btn = document.createElement('button'); btn.textContent='Agregar'; btn.addEventListener('click', ()=> addContact(u.id));
    li.appendChild(btn); out.appendChild(li);
  })
}

async function addContact(contactProfileId){
  const { error } = await supabase.from('contacts').insert({ owner_profile_id: state.profile_id, contact_profile_id: contactProfileId });
  if(error){ console.warn(error); alert('Error agregando'); } else loadContacts();
}

async function loadContacts(){
  const { data } = await supabase.from('contacts').select('contact_profile_id,alias,created_at,contact:profiles(id,username,public_id,device_id)').eq('owner_profile_id', state.profile_id);
  const list = document.getElementById('contactsList'); list.innerHTML = '';
  if(data) data.forEach(c=>{
    const li = document.createElement('li'); li.textContent = (c.contact.username || c.contact.device_id) + ' · ' + (c.contact.public_id||'');
    list.appendChild(li);
  })
}

// IMPORT / EXPORT
async function exportAll(){
  const profiles = await supabase.from('profiles').select('*');
  const rooms = await supabase.from('rooms').select('*');
  const messages = await supabase.from('messages').select('*');
  const contacts = await supabase.from('contacts').select('*');
  const payload = {
    meta: { exported_at: new Date().toISOString() },
    profiles, rooms, messages, contacts
  };
  const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' });
  const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = 'chat-export-'+Date.now()+'.json'; a.click(); URL.revokeObjectURL(url);
}

function importFile(e){
  const f = e.target.files[0]; if(!f) return; const reader = new FileReader();
  reader.onload = async ()=>{
    try{ const json = JSON.parse(reader.result);
      if(json.profiles && json.profiles.data){
        for(const p of json.profiles.data) await supabase.from('profiles').upsert(p);
      }
      if(json.rooms && json.rooms.data){
        for(const r of json.rooms.data) await supabase.from('rooms').upsert(r);
      }
      if(json.messages && json.messages.data){
        for(const m of json.messages.data) await supabase.from('messages').insert(m);
      }
      alert('Import terminado (revisa consola)');
    }catch(err){ console.warn(err); alert('Error importando') }
  }
  reader.readAsText(f);
}

function toggleTheme(){
  const cur = document.documentElement.getAttribute('data-theme');
  document.documentElement.setAttribute('data-theme', cur === 'light' ? 'dark' : 'light');
}

async function changeRoom(slug){ state.room_slug = slug; await loadMessages(); }
""")

utils_js = textwrap.dedent("""
export async function exportToJson(supabase){
  const profiles = await supabase.from('profiles').select('*');
  const messages = await supabase.from('messages').select('*');
  return { profiles, messages };
}
""")

docs_user = textwrap.dedent("""
# Instrucciones rápidas para usuarios
- Crear cuenta: escribe un nombre y presiona Guardar. Se generará tu ID público (ej. juan-001).
- LocalStorage: los datos (device_id, profile_id, username, public_id) se guardan localmente para login rápido.
- Import/Export: usa el botón Exportar para guardar un JSON con tus datos. Para importar, selecciona el archivo JSON.
- Contactos: busca por nombre o ID público y presiona Agregar.
- Privacidad: tu device_id es local y no se muestra públicamente. public_id es el identificador compartido.
- Notificaciones: el navegador preguntará si quieres recibir notifs.
""")

# Write files
files = {
    'README.md': readme,
    'sql/init.sql': sql_init,
    'src/index.html': index_html,
    'src/styles.css': styles_css,
    'src/app.js': app_js,
    'utils/export_import.js': utils_js,
    'docs/instructores_usuario.md': docs_user
}

for path, content in files.items():
    full = os.path.join(root, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)

# Create zip
zip_path = '/mnt/data/chat-app-supabase.zip'
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for folder, _, filenames in os.walk(root):
        for filename in filenames:
            file_path = os.path.join(folder, filename)
            arcname = os.path.relpath(file_path, root)
            zf.write(file_path, arcname)

# List created files for user visibility
created = []
for folder, _, filenames in os.walk(root):
    for filename in filenames:
        created.append(os.path.relpath(os.path.join(folder, filename), root))

print("ZIP creado en:", zip_path)
print("Archivos incluidos:\n" + "\\n".join(created))

# Provide a download hint path for user
zip_path
