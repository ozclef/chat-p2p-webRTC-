# Chat P2P Efímero — Proyecto base
Pequeña aplicación web para mensajería 1:1 P2P (WebRTC) efímera y local. No guarda mensajes en servidores por defecto.

```
este ya no 
https://oz-ice-p2p.vercel.app
```

https://chat-webrtc-osclef.netlify.app/


## Contenido
- index.html — interfaz principal (chat, contactos, señal QR)
- config.html — explicación y ejemplo de config.json
- script.js — lógica WebRTC y almacenamiento local
- styles.css — estilos básicos
- config.json — ejemplo de configuración
- PRIVACY.md — aviso de privacidad (ver más abajo)

- 


## 

<img width="921" height="1488" alt="image" src="https://github.com/user-attachments/assets/7f4bd8ce-98d7-4d55-bab3-8e31c457e5fb" />


## Uso rápido
1. Abre `index.html` en un navegador (mejor Chrome/Edge/Firefox).
2. Acepta o rechaza guardar preferencias.
3. Para conectar: crea Oferta (A), comparte QR o archivo con B.
4. B aplica la señal, crea Respuesta y la devuelve a A.
5. Cuando el canal abra, envíen mensajes (se auto-borrarán según la configuración).

## Nota
Este proyecto es una base y no está pensado para producción sin revisar seguridad, HTTPS, y posible uso de TURN si se requiere relay.
