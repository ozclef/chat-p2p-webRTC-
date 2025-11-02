# Chat P2P Efímero — Proyecto base
Pequeña aplicación web para mensajería 1:1 P2P (WebRTC) efímera y local. No guarda mensajes en servidores por defecto.

## Contenido
- index.html — interfaz principal (chat, contactos, señal QR)
- config.html — explicación y ejemplo de config.json
- script.js — lógica WebRTC y almacenamiento local
- styles.css — estilos básicos
- config.json — ejemplo de configuración
- PRIVACY.md — aviso de privacidad (ver más abajo)

## Uso rápido
1. Abre `index.html` en un navegador (mejor Chrome/Edge/Firefox).
2. Acepta o rechaza guardar preferencias.
3. Para conectar: crea Oferta (A), comparte QR o archivo con B.
4. B aplica la señal, crea Respuesta y la devuelve a A.
5. Cuando el canal abra, envíen mensajes (se auto-borrarán según la configuración).

## Nota
Este proyecto es una base y no está pensado para producción sin revisar seguridad, HTTPS, y posible uso de TURN si se requiere relay.
