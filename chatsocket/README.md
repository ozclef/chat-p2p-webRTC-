


Perfecto.
Vamos a construir la base sólida, con lo mínimo indispensable pero funcional:
login por Google, chat en tiempo real y estructura lista para crecer.

---

### ⚙️ Estructura de carpetas

```
tu-proyecto/
│
├── public/
│   ├── index.html
│   └── main.js
│
├── server.js
├── package.json
└── .env
```

---

### 📦 1. `package.json`

```json
{
  "name": "bious-huachu-app",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "dotenv": "^16.4.0",
    "express": "^4.19.0",
    "express-session": "^1.17.3",
    "passport": "^0.7.0",
    "passport-google-oauth20": "^2.0.0",
    "socket.io": "^4.7.2"
  }
}
```

Instalas todo con:

```bash
npm install
```

---

### 🔐 2. `.env`

```env
GOOGLE_CLIENT_ID=TU_CLIENT_ID
GOOGLE_CLIENT_SECRET=TU_CLIENT_SECRET
SESSION_SECRET=algo_largo_y_unico
PORT=3000
```

(Tus credenciales las generas en [Google Cloud Console → APIs → OAuth 2.0 Credentials](https://console.cloud.google.com/apis/credentials))
En “Authorized redirect URI” pon:

```
http://localhost:3000/auth/google/callback
```

---

### 🧠 3. `server.js`

```js
import express from "express";
import session from "express-session";
import passport from "passport";
import { Strategy as GoogleStrategy } from "passport-google-oauth20";
import dotenv from "dotenv";
import { Server } from "socket.io";
import http from "http";

dotenv.config();
const app = express();
const server = http.createServer(app);
const io = new Server(server);

app.use(express.static("public"));
app.use(express.json());
app.use(session({
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false
}));
app.use(passport.initialize());
app.use(passport.session());

// --- Passport config ---
passport.serializeUser((user, done) => done(null, user));
passport.deserializeUser((obj, done) => done(null, obj));

passport.use(new GoogleStrategy({
  clientID: process.env.GOOGLE_CLIENT_ID,
  clientSecret: process.env.GOOGLE_CLIENT_SECRET,
  callbackURL: "/auth/google/callback"
}, (accessToken, refreshToken, profile, done) => {
  return done(null, profile);
}));

// --- Rutas de login ---
app.get("/auth/google",
  passport.authenticate("google", { scope: ["profile", "email"] })
);

app.get("/auth/google/callback",
  passport.authenticate("google", { failureRedirect: "/" }),
  (req, res) => {
    res.redirect("/"); // regresa al index ya logueado
  }
);

// --- API simple ---
app.get("/user", (req, res) => {
  if (req.user) res.json(req.user);
  else res.json({ user: null });
});

// --- WebSockets (chat) ---
io.on("connection", (socket) => {
  console.log("Nuevo usuario conectado");

  socket.on("message", (msg) => {
    io.emit("message", msg); // envía a todos
  });

  socket.on("disconnect", () => {
    console.log("Usuario desconectado");
  });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => console.log(`Servidor en http://localhost:${PORT}`));
```

---

### 🌐 4. `public/index.html`

```html

<!------->

<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Bious Chat</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <h2>Bious Chat</h2>

  <button id="login">Iniciar sesión con Google</button>
  <div id="user"></div>

  <div id="chat" style="display:none;">
    <div id="messages"></div>
    <input id="msg" placeholder="Escribe un mensaje..." />
    <button id="send">Enviar</button>
  </div>

  <script src="/socket.io/socket.io.js"></script>
  <script src="main.js"></script>
</body>
</html>

<!----


```

---

### 💬 5. `public/main.js`

```js
const socket = io();
const loginBtn = document.getElementById("login");
const userDiv = document.getElementById("user");
const chatDiv = document.getElementById("chat");
const sendBtn = document.getElementById("send");

loginBtn.onclick = () => {
  window.location.href = "/auth/google";
};

async function checkUser() {
  const res = await fetch("/user");
  const data = await res.json();

  if (data.user) {
    loginBtn.style.display = "none";
    userDiv.textContent = `Hola, ${data.user.displayName}`;
    chatDiv.style.display = "block";
  }
}

sendBtn.onclick = () => {
  const msg = document.getElementById("msg").value.trim();
  if (msg) {
    socket.emit("message", msg);
    document.getElementById("msg").value = "";
  }
};

socket.on("message", (msg) => {
  const messagesDiv = document.getElementById("messages");
  const p = document.createElement("p");
  p.textContent = msg;
  messagesDiv.appendChild(p);
});

checkUser();
```

---

### 🚀 Cómo probar

1. `npm install`
2. `npm start`
3. Abre [http://localhost:3000](http://localhost:3000)
4. Da clic en “Iniciar sesión con Google”.
5. Una vez logueado, podrás chatear con cualquiera conectado.

---

Cuando lo tengas corriendo y funcione el login, seguimos con:

* Guardar mensajes y usuarios en base de datos (SQLite o Supabase).
* Conectar esto a tus proyectos **Huachu Pets** y **Bious Market**.
* Después armamos el README técnico y el diagrama del sistema.

¿Quieres que el siguiente paso sea agregar base de datos (SQLite o Supabase)?
