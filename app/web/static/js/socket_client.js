import { updateUI, showToast, enterMultiplayer } from './ui.js';

export const socket = io();

export function initSockets() {
    socket.on('connect', () => {
        console.log('[Socket] Connected!');
        // socket.emit('join_game', {}); // Removed auto-join global, wait for Lobby
    });

    socket.on('disconnect', () => {
        console.log('[Socket] Disconnected');
    });

    socket.on('game_update', (state) => {
        console.log('[Socket] Game Update Rule:', state);
        updateUI(state);
    });

    // Lobby Events
    socket.on('room_created', (data) => {
        console.log("Room Created:", data);
        enterMultiplayer(data.room_id, data.game_state);
        showToast(`Sala Creada: ${data.room_id}`);
        alert(`COMPARTE ESTE CÓDIGO CON TUS AMIGOS: ${data.room_id}`);
    });

    socket.on('game_joined', (data) => {
        console.log("Joined Room:", data);
        enterMultiplayer(data.room_id, data.game_state);
        showToast(`Unido a la sala ${data.room_id}`);
    });

    socket.on('error', (data) => {
        showToast(`Error: ${data.message}`);
    });
}
