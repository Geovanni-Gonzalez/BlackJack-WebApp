import { fetchData } from './api.js';
import { socket } from './socket_client.js';
import { updateUI, showToast, playSound, enterMultiplayer } from './ui.js';

let currentBet = 10;

// Expose functions to window for HTML onClick handlers (since we are modules now)
window.showLobby = () => {
    document.getElementById('welcome-overlay').classList.add('hidden');
    document.getElementById('lobby-container').style.display = 'flex';
    document.getElementById('main-container').style.display = 'none';
};

// Ensure we start with clean state
window.currentRoomId = null;
window.isMultiplayer = false;

window.enterSinglePlayer = () => {
    document.getElementById('lobby-container').style.display = 'none';
    const container = document.getElementById('main-container');
    container.style.display = 'block';
    container.style.opacity = '1';
    container.style.pointerEvents = 'all';

    // Reset flags
    window.isMultiplayer = false;
    window.currentRoomId = null;

    playSound('win');
    startGame();
};

window.createRoom = () => {
    socket.emit('create_room', { difficulty: 'HARD' });
};

window.joinRoom = () => {
    const code = document.getElementById('room-code-input').value.toUpperCase();
    const user = document.getElementById('username-input').value || "Guest";
    if (!code) { showToast("Ingrese un código válido"); return; }
    socket.emit('join_room', { room_id: code, username: user });
};

window.addBet = (amount) => {
    currentBet += amount;
    document.getElementById('current-bet-display').innerText = `$${currentBet}`;
    playSound('deal');
};

window.resetBet = () => {
    currentBet = 10;
    document.getElementById('current-bet-display').innerText = `$${currentBet}`;
};

window.placeBet = async () => {
    if (currentBet <= 0) { showToast("⚠️ La apuesta mínima es $1"); return; }
    document.getElementById('btn-start').disabled = true;

    try {
        const diff = document.getElementById('diff-select').value;
        const state = await fetchData('/api/bet', { amount: currentBet, difficulty: diff });
        updateUI(state);
    } catch (e) {
        console.error(e);
        showToast("Error al apostar");
    } finally {
        document.getElementById('btn-start').disabled = false;
    }
};

window.startGame = async () => {
    const diff = document.getElementById('diff-select').value;
    if (window.isMultiplayer) {
        socket.emit('start_round', { difficulty: diff });
    } else {
        const state = await fetchData('/api/start', { num_ai: 2, difficulty: diff });
        updateUI(state);
    }
};

// Game Actions
// Game Actions (Hybrid: Socket for MP, API for Offline)
async function performAction(actionName, payload = {}) {
    if (window.isMultiplayer) {
        socket.emit(actionName, payload);
    } else {
        // Map common socket events to API endpoints where names differ
        let endpoint = `/api/${actionName}`;
        if (actionName === 'double') endpoint = '/api/double'; // Correct endpoint per api_routes.py

        // Actually, existing api_routes use: /hit, /stand, /double, /split, /insurance
        // So direct mapping works mostly. 
        try {
            const state = await fetchData(endpoint);
            updateUI(state);
        } catch (e) { console.error(e); }
    }
}

window.hit = () => performAction('hit');
window.stand = () => performAction('stand');
window.doubleDown = () => performAction('double');
window.split = () => performAction('split');
window.withdraw = () => performAction('withdraw');
window.insurance = () => performAction('insurance');

// Initialize
import { initSockets } from './socket_client.js';
import { initChart } from './ui.js';

document.addEventListener('DOMContentLoaded', () => {
    initChart();
    initSockets();
    // Pre-load logic if needed
});
