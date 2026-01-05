let currentBet = 10;
let current_state = null;
let lastRoundID = 0;
let balanceHistory = [];
let chart = null;

function initChart() {
    const canvas = document.getElementById('balanceChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Balance ($)',
                data: [],
                borderColor: '#c5a059',
                backgroundColor: 'rgba(197, 160, 89, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { display: false },
                x: { display: false }
            },
            plugins: {
                legend: { display: false },
                tooltip: { enabled: true }
            }
        }
    });
}

function updateChart(balance) {
    if (!chart) initChart();
    balanceHistory.push(balance);
    if (balanceHistory.length > 20) balanceHistory.shift();
    chart.data.labels = balanceHistory.map((_, i) => i);
    chart.data.datasets[0].data = balanceHistory;
    chart.update('none');
}

function playSound(type) {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();
    oscillator.connect(gainNode);
    gainNode.connect(audioCtx.destination);

    if (type === 'deal') {
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(440, audioCtx.currentTime);
        gainNode.gain.setValueAtTime(0.05, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.1);
        oscillator.start(); oscillator.stop(audioCtx.currentTime + 0.1);
    } else if (type === 'win') {
        oscillator.type = 'triangle';
        oscillator.frequency.setValueAtTime(523, audioCtx.currentTime);
        oscillator.frequency.exponentialRampToValueAtTime(659, audioCtx.currentTime + 0.2);
        gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.4);
        oscillator.start(); oscillator.stop(audioCtx.currentTime + 0.4);
    } else if (type === 'loss') {
        oscillator.type = 'sawtooth';
        oscillator.frequency.setValueAtTime(220, audioCtx.currentTime);
        oscillator.frequency.exponentialRampToValueAtTime(110, audioCtx.currentTime + 0.3);
        gainNode.gain.setValueAtTime(0.05, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.4);
        oscillator.start(); oscillator.stop(audioCtx.currentTime + 0.4);
    }
}

async function fetchData(url, data = null, method = 'POST') {
    console.log(`[API REQUEST] ${method} ${url}`, data);
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        const headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        };

        const config = {
            method: method,
            headers: headers
        };

        if (method !== 'GET' && data) {
            config.body = JSON.stringify(data);
        }

        const response = await fetch(url, config);
        const json = await response.json();
        console.log(`[API RESPONSE] ${url}:`, json);
        return json;
    } catch (e) {
        console.error(`[API ERROR] ${url}:`, e);
        return null;
    }
}


function enterCasino() {
    const overlay = document.getElementById('welcome-overlay');
    const container = document.getElementById('main-container');
    overlay.classList.add('hidden');
    container.style.opacity = '1';
    container.style.pointerEvents = 'all';
    playSound('win');
}

function toggleManual() {
    const modal = document.getElementById('rule-modal');
    modal.style.display = modal.style.display === 'none' ? 'flex' : 'none';
}

async function toggleLeaderboard() {
    const modal = document.getElementById('leaderboard-modal');
    const isOpening = modal.style.display === 'none';
    modal.style.display = isOpening ? 'flex' : 'none';

    if (isOpening) {
        await loadLeaderboard();
    }
}

async function loadLeaderboard() {
    try {
        const data = await fetchData('/api/leaderboard', null, 'GET');
        const tbody = document.getElementById('leaderboard-body');

        if (!data || data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">No hay entradas aún. ¡Sé el primero!</td></tr>';
            return;
        }

        tbody.innerHTML = data.map((entry, idx) => `
            <tr>
                <td>${idx + 1}</td>
                <td>${entry.player_name}</td>
                <td>$${entry.peak_balance}</td>
                <td>${entry.rounds_played}</td>
                <td>${entry.win_rate}%</td>
                <td>${entry.player_accuracy}%</td>
                <td>${entry.achieved_at}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading leaderboard:', error);
        document.getElementById('leaderboard-body').innerHTML =
            '<tr><td colspan="7" style="text-align:center;">Error al cargar el Hall of Fame</td></tr>';
    }
}

async function saveToLeaderboard() {
    try {
        const result = await fetchData('/api/leaderboard', {}, 'POST');
        if (result.success) {
            alert(result.message);
        }
    } catch (error) {
        console.error('Error saving to leaderboard:', error);
    }
}

// Update Header Stats Display
function updateHeaderStats(state) {
    const balanceEl = document.getElementById('header-balance');
    const roundsEl = document.getElementById('header-rounds');

    if (balanceEl && state.players && state.players.length > 0) {
        const balance = state.players[0].balance;
        balanceEl.textContent = `$${balance}`;

        // Add color coding based on profit/loss
        if (balance > 1000) {
            balanceEl.style.color = 'var(--accent-green)';
        } else if (balance < 1000) {
            balanceEl.style.color = 'var(--accent-red)';
        } else {
            balanceEl.style.color = 'var(--gold-primary)';
        }
    }

    if (roundsEl && state.stats) {
        roundsEl.textContent = state.stats.rounds_played || 0;
    }
}

async function updateUI(state) {
    if (!state) { console.error("[UI] Received null state"); return; }
    console.log(`[UI UPDATE] Phase: ${state.waiting_for_bets ? 'BETTING' : (state.game_over ? 'GAME_OVER' : 'PLAYING')}`, state);

    current_state = state;

    // Phase Visibility & Messaging
    const messageArea = document.getElementById('message-area');
    messageArea.innerText = state.message;

    // Update Header Stats
    updateHeaderStats(state);

    // Trigger Effects
    const currentRoundID = state.stats.rounds_played;
    if (state.game_over && state.message && currentRoundID > lastRoundID && !state.waiting_for_bets) {
        lastRoundID = currentRoundID;
        if (state.message.includes("WIN") || state.message.includes("Paga")) {
            triggerScreenEffects('win');
            if (state.players[0].bet >= 100) triggerChipRain();
        } else if (state.message.includes("LOSS") || state.message.includes("Pierde")) {
            triggerScreenEffects('loss');
        }
    }

    // updateAIEmotions(state); // Disabled for professional look

    // Sidebar & Betting
    document.getElementById('betting-area').style.display = state.waiting_for_bets ? 'block' : 'none';
    document.getElementById('game-actions').style.display = state.waiting_for_bets ? 'none' : 'grid';

    // Stats
    document.getElementById('stat-rounds').innerText = state.stats.rounds_played;
    document.getElementById('count-value').innerText = state.count;

    const aiAcc = state.stats.ai_decisions_total > 0 ? ((state.stats.ai_decisions_correct / state.stats.ai_decisions_total) * 100).toFixed(1) : 0;
    document.getElementById('stat-accuracy').innerText = aiAcc + "%";

    const pAcc = state.stats.player_decisions_total > 0 ? ((state.stats.player_decisions_correct / state.stats.player_decisions_total) * 100).toFixed(1) : 0;
    document.getElementById('stat-player-accuracy').innerText = pAcc + "%";

    if (state.players[0]) {
        document.getElementById('current-bet-display').innerText = `$${currentBet}`;
        updateChart(state.players[0].balance);
    }

    // Advice & AI Brains Update
    if (!state.game_over && !state.waiting_for_bets && state.players[state.current_player_idx].owner === "Human") {
        updateAdvice();
    } else {
        // Clear advice but keep Q-values updating for observation if needed or reset
        document.getElementById('ai-advice').innerText = "Esperando turno...";
        document.getElementById('prob-hit').innerText = "0%";
        document.getElementById('prob-stand').innerText = "0%";
    }
    // Always try to update Q-values to show current state analysis
    updateQValues();

    renderEliteLog(state.decision_history);
    updatePhaseBanner(state);

    // Dealer
    if (state.waiting_for_bets) {
        document.getElementById('dealer-cards').innerHTML = '';
        document.getElementById('dealer-score').innerText = '';
    } else {
        if (state.game_over) {
            renderHand('dealer-cards', state.dealer_hand.cards, true);
            document.getElementById('dealer-score').innerText = state.dealer_hand.value;
        } else {
            renderHandHidden('dealer-cards', state.dealer_hand.cards);
            document.getElementById('dealer-score').innerText = "?";
        }
    }

    // Players
    const container = document.getElementById('players-container');
    container.innerHTML = '';
    state.players.forEach((player, idx) => {
        const handWrapper = document.createElement('div');
        handWrapper.className = 'hand-section';
        if (idx === state.current_player_idx && !state.game_over && !state.waiting_for_bets) {
            handWrapper.classList.add('active-turn');
        }

        const playerName = player.owner === 'Human' ? 'Tú' : player.owner;
        let statusTag = "";
        if (player.busted) statusTag = `<span class="badge bust">PASADO</span>`;
        else if (player.standing) statusTag = `<span class="badge stand">PLANTADO</span>`;

        handWrapper.innerHTML = `
            <div class="section-title">${playerName} ${statusTag}</div>
            <div class="cards" id="${player.owner}-cards-${idx}"></div>
            <div class="score-pill">${player.value} | $${player.bet}</div>
        `;
        container.appendChild(handWrapper);
        renderHand(`${player.owner}-cards-${idx}`, player.cards, true);
    });

    updateInteractionControls(state);
}

function updateInteractionControls(state) {
    if (state.waiting_for_bets) return;

    // If game is over, disable all buttons
    // If game is over, disable all buttons and show New Round
    if (state.game_over) {
        document.getElementById('btn-hit').disabled = true;
        document.getElementById('btn-stand').disabled = true;
        document.getElementById('btn-double').disabled = true;
        document.getElementById('btn-withdraw').disabled = true;
        document.getElementById('btn-split').style.display = 'none';
        document.getElementById('btn-insurance').style.display = 'none';
        document.getElementById('btn-new-round').style.display = 'block';
        return;
    }

    document.getElementById('btn-new-round').style.display = 'none';

    const currentPlayer = state.players[state.current_player_idx];
    // Fix: Owner name might be username now, but Player 0 is always the local human in this architecture
    const isHuman = (state.current_player_idx === 0);

    console.log(`[UI CTRL] Round: ${state.stats.rounds_played}, Wait: ${state.waiting_for_bets}, Owner: ${currentPlayer.owner}, isHuman: ${isHuman}`);

    const hitBtn = document.getElementById('btn-hit');
    hitBtn.disabled = !isHuman;
    console.log(`[UI CTRL] Hit Button Disabled? ${hitBtn.disabled}`);

    document.getElementById('btn-stand').disabled = !isHuman;
    document.getElementById('btn-double').disabled = !isHuman || currentPlayer.cards.length > 2;
    document.getElementById('btn-withdraw').disabled = !isHuman;

    const btnSplit = document.getElementById('btn-split');
    const btnInsurance = document.getElementById('btn-insurance');
    btnSplit.style.display = (isHuman && currentPlayer.cards.length === 2 && currentPlayer.cards[0].rank === currentPlayer.cards[1].rank) ? 'inline-block' : 'none';

    // Safe check for dealer's second card (insurance only available if dealer shows Ace)
    const dealerHasAce = state.dealer_hand && state.dealer_hand.cards && state.dealer_hand.cards.length >= 2 && state.dealer_hand.cards[1] && state.dealer_hand.cards[1].rank === 'A';
    btnInsurance.style.display = (isHuman && currentPlayer.cards.length === 2 && dealerHasAce && !currentPlayer.is_insurance) ? 'inline-block' : 'none';
}

function renderEliteLog(history) {
    const logList = document.getElementById('log-list');
    logList.innerHTML = '';
    [...history].reverse().slice(0, 15).forEach(entry => {
        const li = document.createElement('li');
        const badgeType = entry.reason === 'Q-Learning' ? 'badge-rl' : (entry.reason === 'Monte Carlo' ? 'badge-mc' : 'badge-count');
        li.innerHTML = `
            <span class="log-badge ${badgeType}">${entry.reason}</span>
            <span class="log-player">${entry.player}</span>
            <span class="log-action">➔ ${entry.action} ${entry.prob_hit ? `(${(entry.prob_hit * 100).toFixed(0)}%)` : ''}</span>
            <span class="log-count">Hilo: ${entry.count}</span>
        `;
        logList.appendChild(li);
    });
}

async function updateAdvice() {
    try {
        const data = await fetchData('/api/probability', null, 'GET');

        if (!data || !data.recommendation) {
            document.getElementById('ai-advice').innerHTML = `<strong>Sugerencia:</strong> Esperando mano...`;
            document.getElementById('prob-hit').innerText = "-";
            document.getElementById('prob-stand').innerText = "-";
        } else {
            document.getElementById('ai-advice').innerHTML = `<strong>Sugerencia:</strong> ${data.recommendation}`;
            document.getElementById('prob-hit').innerText = (data.hit_win_rate * 100).toFixed(1) + "%";
            document.getElementById('prob-stand').innerText = (data.stand_win_rate * 100).toFixed(1) + "%";
        }

        updateQValues(); // Fetch Q-values alongside probability
    } catch (e) {
        console.warn("Could not fetch advice", e);
    }
}

async function updateQValues() {
    try {
        const data = await fetchData('/api/qvalues', null, 'GET');

        // Handle game over or waiting states
        if (!data || data.state === null || data.state === 'None') {
            document.getElementById('q-stand-value').innerText = '0.000';
            document.getElementById('q-hit-value').innerText = '0.000';
            document.getElementById('q-stand-fill').style.width = '50%';
            document.getElementById('q-hit-fill').style.width = '50%';
            document.getElementById('q-optimal').innerText = 'Esperando...';
            return;
        }

        // Normalize Q-values to 0-100% for gauge display
        const maxQ = Math.max(Math.abs(data.q_stand), Math.abs(data.q_hit), 1);
        const standPercent = ((data.q_stand + maxQ) / (2 * maxQ)) * 100;
        const hitPercent = ((data.q_hit + maxQ) / (2 * maxQ)) * 100;

        document.getElementById('q-stand-value').innerText = data.q_stand.toFixed(3);
        document.getElementById('q-hit-value').innerText = data.q_hit.toFixed(3);
        document.getElementById('q-stand-fill').style.width = standPercent + '%';
        document.getElementById('q-hit-fill').style.width = hitPercent + '%';
        document.getElementById('q-optimal').innerText = data.optimal_action || 'N/A';
    } catch (error) {
        console.error('Error fetching Q-values:', error);
        document.getElementById('q-optimal').innerText = 'Error';
    }
}

function triggerScreenEffects(type) {
    const main = document.querySelector('.game-board');
    if (!main) return;
    main.classList.remove('win-flash', 'shake');
    void main.offsetWidth;
    if (type === 'win') main.classList.add('win-flash');
    else if (type === 'loss') main.classList.add('shake');
}

function renderHand(elementId, cards, flipped = true) {
    const container = document.getElementById(elementId);
    if (!container) return;
    const existingCount = container.children.length;

    cards.slice(existingCount).forEach((card, i) => {
        const cardCont = document.createElement('div');
        cardCont.className = 'card-container';
        if (flipped) cardCont.classList.add('flipped');

        const isRed = ['Hearts', 'Diamonds', '♥', '♦'].includes(card.suit);
        cardCont.innerHTML = `
            <div class="card-face card-front ${isRed ? 'red' : 'black'}">${getCardSymbol(card)}</div>
            <div class="card-face card-back"></div>
        `;
        container.appendChild(cardCont);
        // Animate from shoe
        const shoe = document.getElementById('card-shoe');
        const shoeRect = shoe.getBoundingClientRect();
        const cardRect = cardCont.getBoundingClientRect();
        cardCont.animate([
            { transform: `translate(${shoeRect.left - cardRect.left}px, ${shoeRect.top - cardRect.top}px) rotateY(0deg) scale(0.1)`, opacity: 0 },
            { transform: 'translate(0, 0) rotateY(180deg) scale(1)', opacity: 1 }
        ], { duration: 600, easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)', fill: 'forwards' });
        playSound('deal');
    });
}

function renderHandHidden(elementId, cards) {
    const container = document.getElementById(elementId);
    if (!container) return;
    container.innerHTML = '';
    cards.forEach((card, i) => {
        const cardCont = document.createElement('div');
        cardCont.className = 'card-container';
        if (i === 1) cardCont.classList.add('flipped');
        const isRed = ['Hearts', 'Diamonds', '♥', '♦'].includes(card.suit);
        cardCont.innerHTML = `<div class="card-face card-front ${isRed ? 'red' : 'black'}">${i === 1 ? getCardSymbol(card) : '?'}</div><div class="card-face card-back"></div>`;
        container.appendChild(cardCont);
        const shoeRect = document.getElementById('card-shoe').getBoundingClientRect();
        const cardRect = cardCont.getBoundingClientRect();
        cardCont.animate([
            { transform: `translate(${shoeRect.left - cardRect.left}px, ${shoeRect.top - cardRect.top}px) rotate(-45deg) scale(0.1)`, opacity: 0 },
            { transform: 'translate(0, 0) scale(1)', opacity: 1 }
        ], { duration: 600, delay: i * 200, easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)', fill: 'forwards' });
        setTimeout(() => playSound('deal'), i * 200);
    });
}

function getCardSymbol(card) {
    const suitMaps = { 'Hearts': '♥', 'Diamonds': '♦', 'Spades': '♠', 'Clubs': '♣', '♥': '♥', '♦': '♦', '♠': '♠', '♣': '♣' };
    return `${card.rank}${suitMaps[card.suit] || card.suit}`;
}

function addBet(amount) {
    currentBet += amount;
    document.getElementById('current-bet-display').innerText = `$${currentBet}`;
    playSound('deal');
}

function resetBet() {
    currentBet = 10;
    document.getElementById('current-bet-display').innerText = `$${currentBet}`;
}

async function placeBet() {
    await cleanupTable();
    const diff = document.getElementById('diff-select').value;
    const state = await fetchData('/api/bet', { amount: currentBet, difficulty: diff });
    updateUI(state);
}

// Socket.IO Initialization
const socket = io();

socket.on('connect', () => {
    console.log('[Socket] Connected!');
    socket.emit('join_game', {}); // Join global room for now
});

socket.on('disconnect', () => {
    console.log('[Socket] Disconnected');
});

socket.on('game_update', (state) => {
    console.log('[Socket] Game Update Rule:', state);
    updateUI(state);
});

async function startGame() {
    await cleanupTable();
    const diff = document.getElementById('diff-select').value;
    const state = await fetchData('/api/start', { num_ai: 2, difficulty: diff });
    updateUI(state);
}

// Replaced HTTP calls with Socket Emits for speed
function hit() { socket.emit('hit'); }
function stand() { socket.emit('stand'); }
function doubleDown() { socket.emit('double'); }
// Split/Insurance/Withdraw can remain HTTP or move to Socket. 
// Keeping them HTTP for now as they are less freq or complex? 
// Actually, consistency is better. Let's redirect Split too if backend supports it.
// Backend sockets.py supports: hit, stand, double, split.
function split() { socket.emit('split'); }
async function insurance() { const state = await fetchData('/api/insurance'); updateUI(state); }
async function withdraw() { const state = await fetchData('/api/withdraw'); updateUI(state); }

async function updateAIEmotions(state) {
    // Removed emoji reactions for a more professional look
}

function triggerChipRain() {
    const board = document.getElementById('board-perspective');
    for (let i = 0; i < 30; i++) {
        const chip = document.createElement('div');
        chip.className = 'chip-rain';
        chip.style.left = Math.random() * 100 + "%";
        chip.style.top = "-20px";
        chip.style.backgroundColor = ['#f1c40f', '#c5a059', '#ecf0f1'][Math.floor(Math.random() * 3)];
        board.appendChild(chip);
        chip.animate([{ transform: 'translateY(0)', opacity: 1 }, { transform: 'translateY(600px)', opacity: 0 }], { duration: 2000 }).onfinish = () => chip.remove();
    }
}

async function cleanupTable() {
    const cards = document.querySelectorAll('.card-container');
    const promises = Array.from(cards).map((card, i) => {
        return card.animate([{ opacity: 1 }, { transform: 'translateX(-500px)', opacity: 0 }], { duration: 400, delay: i * 30 }).finished;
    });
    await Promise.all(promises);
}

window.onload = async () => {
    initChart();
    const diff = document.getElementById('diff-select') ? document.getElementById('diff-select').value : 'HARD';
    const state = await fetchData('/api/start', { num_ai: 2, difficulty: diff });
    updateUI(state);
    initParallax();
};

function initParallax() {
    const board = document.getElementById('board-perspective');
    if (!board) return;

    document.addEventListener('mousemove', (e) => {
        const x = (e.clientX / window.innerWidth - 0.5) * 10; // Max 5deg left/right
        const y = (e.clientY / window.innerHeight - 0.5) * 10; // Max 5deg up/down
        board.style.transform = `perspective(1200px) rotateX(${15 - y}deg) rotateY(${x}deg)`;
    });
}

async function resetToBetting() {
    console.log("[UI] Resetting for new round...");

    // Call backend to reset game state
    // Call backend to reset game state
    const diff = document.getElementById('diff-select').value;
    const state = await fetchData('/api/start', { num_ai: 2, difficulty: diff });

    if (state) {
        updateUI(state);
    }

    // Reset local state vars if needed
    document.getElementById('game-actions').style.display = 'none';
    document.getElementById('betting-area').style.display = 'block';
    document.getElementById('message-area').innerText = "";

    // Reset buttons for next game
    document.getElementById('btn-hit').disabled = false;
    document.getElementById('btn-stand').disabled = false;
    document.getElementById('btn-double').disabled = false;
    document.getElementById('btn-withdraw').disabled = false;
    document.getElementById('btn-new-round').style.display = 'none';

    // Reset visuals
    cleanupTable();
    const dealerScore = document.getElementById('dealer-score');
    if (dealerScore) dealerScore.innerText = "";

    // Update advice to waiting state
    document.getElementById('ai-advice').innerHTML = `<strong>Sugerencia:</strong> Esperando mano...`;
    document.getElementById('prob-hit').innerText = "-";
    document.getElementById('prob-stand').innerText = "-";
}

function updatePhaseBanner(state) {
    const banner = document.getElementById('phase-banner');
    if (!banner) return;

    banner.classList.remove('hidden');

    if (state.waiting_for_bets) {
        banner.innerText = "FASE DE APUESTAS";
        banner.style.color = "var(--gold-bright)";
        banner.style.borderColor = "var(--gold-primary)";
    } else if (state.game_over) {
        if (state.message && state.message.includes("WIN")) {
            banner.innerText = "¡VICTORIA!";
            banner.style.color = "#2ecc71";
            banner.style.borderColor = "#2ecc71";
        } else if (state.message && state.message.includes("LOSS")) {
            banner.innerText = "DERROTA";
            banner.style.color = "#e74c3c";
            banner.style.borderColor = "#e74c3c";
        } else {
            banner.innerText = "PARTIDA FINALIZADA";
            banner.style.color = "#fff";
            banner.style.borderColor = "#fff";
        }
    } else {
        // Playing
        const currentPlayer = state.players[state.current_player_idx];
        if (currentPlayer && currentPlayer.owner === "Human") {
            banner.innerText = "TU TURNO";
            banner.style.color = "#3498db";
            banner.style.borderColor = "#3498db";
        } else {
            const owner = currentPlayer ? currentPlayer.owner : "DEALER";
            banner.innerText = `TURNO DE ${owner}`;
            banner.style.color = "#f1c40f";
            banner.style.borderColor = "#f1c40f";
        }
    }

    // Check for Bankruptcy
    if (state.waiting_for_bets && state.players && state.players[0].balance <= 0) {
        document.getElementById('bankruptcy-modal').style.display = 'flex';
    }
}

async function refillBalance() {
    try {
        const state = await fetchData('/api/refill', {}, 'POST');
        if (state) {
            updateUI(state);
            document.getElementById('bankruptcy-modal').style.display = 'none';
            playSound('win');
            showToast("¡Recarga Exitosa! +$1000");
        }
    } catch (e) {
        console.error("Refill error:", e);
    }
}

playSound('win'); // Satisfying sound for new money

// Auto-Play Logic
// Auto-Play Logic
let autoPlayTimer = null;

function triggerAutoRestart() {
    const roundsInput = document.getElementById('auto-rounds-input');
    let roundsLeft = parseInt(roundsInput.value);

    if (roundsLeft <= 0) return;

    roundsInput.value = roundsLeft - 1; // Decrement visual counter
    showToast(`Iniciando nueva ronda... Quedan: ${roundsLeft - 1}`);

    autoPlayTimer = setTimeout(() => {
        resetToBetting();
        // Immediately place bet and deal if auto-playing to keep flow
        setTimeout(() => {
            placeBet();
        }, 1000);
    }, 3000);
}

// Hook into updateUI to catch Game Over
const originalUpdateUI = updateUI;
updateUI = async function (state) {
    await originalUpdateUI(state);

    const roundsInput = document.getElementById('auto-rounds-input');
    const stopLossInput = document.getElementById('stop-loss-input');
    const takeProfitInput = document.getElementById('take-profit-input');

    const roundsLeft = parseInt(roundsInput ? roundsInput.value : 0);
    const stopLoss = parseInt(stopLossInput ? stopLossInput.value : 0);
    const takeProfit = parseInt(takeProfitInput ? takeProfitInput.value : 0);
    const currentBalance = state.players[0] ? state.players[0].balance : 0;

    if (state.game_over && roundsLeft > 0 && !state.waiting_for_bets) {
        // Stop Logic
        if (stopLoss > 0 && currentBalance <= stopLoss) {
            showToast(`🛑 Auto-Stop: Saldo bajo límite (${currentBalance})`);
            roundsInput.value = 0;
            return;
        }
        if (takeProfit > 0 && currentBalance >= takeProfit) {
            showToast(`💰 Auto-Stop: Meta alcanzada (${currentBalance})`);
            roundsInput.value = 0;
            return;
        }

        if (autoPlayTimer) clearTimeout(autoPlayTimer);
        triggerAutoRestart();
    }
};

function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'message-center';
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.left = '50%';
    toast.style.transform = 'translateX(-50%)';
    toast.style.background = 'rgba(0,0,0,0.8)';
    toast.style.padding = '10px 30px';
    toast.style.border = '1px solid var(--gold-primary)';
    toast.style.borderRadius = '50px';
    toast.style.zIndex = '3000';
    toast.innerText = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 500);
    }, 2500);
}
