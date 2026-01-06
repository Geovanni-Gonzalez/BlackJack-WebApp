import { fetchData } from './api.js';

let chart = null;
let balanceHistory = [];

export function showToast(message) {
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
    toast.style.zIndex = '9999';
    toast.innerText = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

export function playSound(type) {
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

export function initChart() {
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

export function updateUI(state) {
    if (!state) { console.error("[UI] Received null state"); return; }
    console.log(`[UI UPDATE] Phase: ${state.waiting_for_bets ? 'BETTING' : (state.game_over ? 'GAME_OVER' : 'PLAYING')}`, state);

    // Phase Visibility & Messaging
    const messageArea = document.getElementById('message-area');
    messageArea.innerText = state.message;

    // Update Header Stats
    updateHeaderStats(state);

    // Trigger Effects
    // Note: accessing global logic for 'lastRoundID' might be needed or passed in
    // For simplicity, we trigger effects based on message content
    if (state.game_over && state.message) {
        if (state.message.includes("WIN") || state.message.includes("Paga")) {
            triggerScreenEffects('win');
        } else if (state.message.includes("LOSS") || state.message.includes("Pierde")) {
            triggerScreenEffects('loss');
        }
    }

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
        updateChart(state.players[0].balance);
    }

    // Advice & AI Brains Update
    if (!state.game_over && !state.waiting_for_bets && state.current_player_idx === 0) {
        updateAdvice();
    } else {
        document.getElementById('ai-advice').innerHTML = "Esperando turno...";
        document.getElementById('prob-hit').innerText = "0%";
        document.getElementById('prob-stand').innerText = "0%";
    }
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
        const isHost = (idx === 0); // Player 0 is always Host
        const hostBadge = isHost ? '<span class="badge host">HOST</span>' : '';
        let statusTag = "";
        if (player.busted) statusTag = `<span class="badge bust">PASADO</span>`;
        if (player.standing) statusTag = `<span class="badge stand">PLANTADO</span>`;

        handWrapper.innerHTML = `
            <div class="section-title">${playerName} ${hostBadge} ${statusTag}</div>
            <div class="cards" id="${player.owner}-cards-${idx}"></div>
            <div class="score-pill">${player.value} | $${player.bet}</div>
        `;
        container.appendChild(handWrapper);
        renderHand(`${player.owner}-cards-${idx}`, player.cards, true);
    });

    updateInteractionControls(state);
}

function updateHeaderStats(state) {
    const balanceEl = document.getElementById('header-balance');
    const roundsEl = document.getElementById('header-rounds');

    if (balanceEl && state.players && state.players.length > 0) {
        const balance = state.players[0].balance;
        balanceEl.textContent = `$${balance}`;
        if (balance > 1000) balanceEl.style.color = 'var(--accent-green)';
        else if (balance < 1000) balanceEl.style.color = 'var(--accent-red)';
        else balanceEl.style.color = 'var(--gold-primary)';
    }

    if (roundsEl) {
        roundsEl.textContent = state.stats.rounds_played || 0;
    }
}

function updateInteractionControls(state) {
    if (state.waiting_for_bets) return;

    if (state.game_over) {
        document.getElementById('btn-hit').disabled = true;
        document.getElementById('btn-stand').disabled = true;
        document.getElementById('btn-double').disabled = true;
        document.getElementById('btn-withdraw').disabled = true;
        document.getElementById('btn-split').style.display = 'none';
        document.getElementById('btn-insurance').style.display = 'none';
        // Only show New Round button if it's the Host (or Single Player)
        // In multiplayer, players[0] is Host.
        // We need to check if we are the host. 
        // window.mySocketId must match players[0].player_id
        const isHost = (!window.isMultiplayer) || (state.players[0] && state.players[0].player_id === window.mySocketId);

        if (isHost) {
            document.getElementById('btn-new-round').style.display = 'block';
        } else {
            document.getElementById('btn-new-round').style.display = 'none';
            // Maybe show a waiting message instead?
            // document.getElementById('message-area').innerText += " (Esperando al anfitrión...)";
        }
        return;
    }

    document.getElementById('btn-new-round').style.display = 'none';

    const currentPlayer = state.players[state.current_player_idx];

    // Determine if it is THIS client's turn
    let isMyTurn = false;
    if (window.isMultiplayer) {
        // In Multiplayer, match socket ID
        // The state.players list usually has owner info. 
        // We need to match currentPlayer.player_id == window.mySocketId
        if (currentPlayer && currentPlayer.player_id === window.mySocketId) {
            isMyTurn = true;
        }
    } else {
        // In Offline, it's my turn if index is 0 (Human)
        isMyTurn = (state.current_player_idx === 0);
    }

    const hitBtn = document.getElementById('btn-hit');
    hitBtn.disabled = !isMyTurn;
    document.getElementById('btn-stand').disabled = !isMyTurn;
    document.getElementById('btn-double').disabled = !isMyTurn || currentPlayer.cards.length > 2;

    const btnSplit = document.getElementById('btn-split');
    const btnInsurance = document.getElementById('btn-insurance');

    // Logic for split/insurance needs to respect turn too
    btnSplit.style.display = (isMyTurn && currentPlayer.cards.length === 2 && currentPlayer.cards[0].rank === currentPlayer.cards[1].rank) ? 'inline-block' : 'none';

    // Dealer ace check
    const dealerHasAce = state.dealer_hand && state.dealer_hand.cards.length >= 2 && state.dealer_hand.cards[1].rank === 'A';
    btnInsurance.style.display = (isMyTurn && currentPlayer.cards.length === 2 && dealerHasAce && !currentPlayer.is_insurance) ? 'inline-block' : 'none';

    // Update Banner to show whose turn it is
    const banner = document.getElementById('phase-banner');
    if (banner && !state.game_over) {
        if (isMyTurn) {
            banner.innerText = "TU TURNO";
            banner.style.color = "var(--gold-primary)";
        } else {
            banner.innerText = `ESPERANDO A ${currentPlayer.owner}`;
            banner.style.color = "#888";
        }
    }
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
        // Removed complex animation ref for simplicity in module, or assume defaults
        cardCont.style.opacity = 1;
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
        cardCont.style.opacity = 1;
    });
}

function getCardSymbol(card) {
    const suitMaps = { 'Hearts': '♥', 'Diamonds': '♦', 'Spades': '♠', 'Clubs': '♣', '♥': '♥', '♦': '♦', '♠': '♠', '♣': '♣' };
    return `${card.rank}${suitMaps[card.suit] || card.suit}`;
}

async function updateAdvice() {
    try {
        const data = await fetchData('/api/probability', null, 'GET');
        if (!data || !data.recommendation) return;
        document.getElementById('ai-advice').innerHTML = `<strong>Sugerencia:</strong> ${data.recommendation}`;
        document.getElementById('prob-hit').innerText = (data.hit_win_rate * 100).toFixed(1) + "%";
        document.getElementById('prob-stand').innerText = (data.stand_win_rate * 100).toFixed(1) + "%";
        updateQValues();
    } catch (e) { console.warn(e); }
}

async function updateQValues() {
    try {
        const data = await fetchData('/api/qvalues', null, 'GET');
        if (!data || data.state === null) return;
        document.getElementById('q-optimal').innerText = data.optimal_action || 'N/A';
    } catch (e) { }
}

function triggerScreenEffects(type) {
    const main = document.querySelector('.game-board');
    if (main) {
        main.classList.remove('win-flash', 'shake');
        void main.offsetWidth;
        if (type === 'win') main.classList.add('win-flash');
        else if (type === 'loss') main.classList.add('shake');
    }
}

function renderEliteLog(history) {
    const logList = document.getElementById('log-list');
    logList.innerHTML = '';
    [...history].reverse().slice(0, 15).forEach(entry => {
        const li = document.createElement('li');
        li.innerHTML = `<span class="log-action">➔ ${entry.action}</span>`;
        logList.appendChild(li);
    });
}

function updatePhaseBanner(state) {
    const banner = document.getElementById('phase-banner');
    if (banner) banner.innerText = state.waiting_for_bets ? "APUESTAS" : "JUEGO";
}

export function enterMultiplayer(roomId, state) {
    document.getElementById('lobby-container').style.display = 'none';
    const container = document.getElementById('main-container');
    container.style.display = 'block';
    container.style.opacity = '1';
    container.style.pointerEvents = 'all';
    updateUI(state);

    // Set global flag on window if needed or manage via Game module
    window.isMultiplayer = true;
}
