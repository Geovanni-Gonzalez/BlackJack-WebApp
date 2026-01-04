let currentBet = 10;
let current_state = null;
let balanceHistory = [];
let chart = null;

function initChart() {
    const ctx = document.getElementById('balanceChart').getContext('2d');
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Human Balance ($)',
                data: [],
                borderColor: '#f1c40f',
                backgroundColor: 'rgba(241, 196, 15, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: '#f1c40f'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false,
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#bdc3c7' }
                },
                x: {
                    grid: { display: false },
                    ticks: { display: false }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: { backgroundColor: '#16213e', titleColor: '#e94560', bodyColor: '#fff' }
            }
        }
    });
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
        oscillator.start();
        oscillator.stop(audioCtx.currentTime + 0.1);
    } else if (type === 'win') {
        oscillator.type = 'triangle';
        oscillator.frequency.setValueAtTime(523, audioCtx.currentTime);
        oscillator.frequency.exponentialRampToValueAtTime(659, audioCtx.currentTime + 0.2);
        gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.4);
        oscillator.start();
        oscillator.stop(audioCtx.currentTime + 0.4);
    } else if (type === 'loss') {
        oscillator.type = 'sawtooth';
        oscillator.frequency.setValueAtTime(220, audioCtx.currentTime);
        oscillator.frequency.exponentialRampToValueAtTime(110, audioCtx.currentTime + 0.3);
        gainNode.gain.setValueAtTime(0.05, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.4);
        oscillator.start();
        oscillator.stop(audioCtx.currentTime + 0.4);
    }
}

function updateChart(balance) {
    if (!chart) initChart();
    balanceHistory.push(balance);
    if (balanceHistory.length > 20) balanceHistory.shift();

    chart.data.labels = balanceHistory.map((_, i) => i + 1);
    chart.data.datasets[0].data = balanceHistory;
    chart.update('none');
}

async function fetchData(url, data = null, method = 'POST') {
    const options = { method: method };
    if (data) {
        options.headers = { 'Content-Type': 'application/json' };
        options.body = JSON.stringify(data);
    }
    const response = await fetch(url, options);
    return response.json();
}

async function updateUI(state) {
    const prevState = current_state;
    current_state = state;

    // Render Players
    const container = document.getElementById('players-container');
    container.innerHTML = '';

    state.players.forEach((player, idx) => {
        const handDiv = document.createElement('div');
        handDiv.className = 'hand-section';
        if (idx === state.current_player_idx && !state.game_over && !state.waiting_for_bets) {
            handDiv.classList.add('active-player');
        }

        let statusText = player.busted ? " <span style='color:#e74c3c'>(BUST)</span>" : (player.withdrawn ? " <span style='color:#7f8c8d'>(OUT)</span>" : "");
        let betText = (player.current_bet > 0) ? ` · Bet: $${player.current_bet}` : "";

        handDiv.innerHTML = `<h3>${player.owner} <span id="${player.owner}-score">(${player.value})</span>${statusText}</h3>
                             <p class="balance-display">Saldo: $${player.balance}${betText}</p>
                             <div class="cards" id="${player.owner}-cards-${idx}"></div>`;
        container.appendChild(handDiv);
        renderHand(`${player.owner}-cards-${idx}`, player.cards);
    });

    // Render Dealer Cards
    let dealerCards = state.dealer_hand.cards;
    if (!state.game_over && !state.waiting_for_bets && dealerCards.length > 1) {
        renderHandHidden('dealer-cards', dealerCards[0]);
        document.getElementById('dealer-score').innerText = "(?)";
    } else {
        renderHand('dealer-cards', dealerCards);
        document.getElementById('dealer-score').innerText = dealerCards.length > 0 ? `(${state.dealer_hand.value})` : "";
    }

    // Phase Visibility
    if (state.waiting_for_bets) {
        document.getElementById('betting-area').style.display = 'block';
        document.getElementById('game-actions').style.display = 'none';
        document.getElementById('btn-new').style.display = 'none';
        document.getElementById('message-area').innerText = state.message;
    } else if (state.game_over) {
        document.getElementById('betting-area').style.display = 'none';
        document.getElementById('game-actions').style.display = 'none';
        document.getElementById('btn-new').style.display = 'block';
        document.getElementById('message-area').innerText = state.message;

        if (state.players.length > 0) {
            updateChart(state.players[0].balance);
            if (state.message.includes("WIN") || state.message.includes("Paga")) playSound('win');
            else if (state.message.includes("LOSS") || state.message.includes("Pierde")) playSound('loss');
        }

        // Show Stats
        document.getElementById('stats-area').style.display = 'grid';
        document.getElementById('stat-rounds').innerText = state.stats.rounds_played;
        document.getElementById('stat-human-wins').innerText = "$" + (state.players[0] ? state.players[0].balance : "0");

        const accuracy = state.stats.ai_decisions_total > 0 ? (state.stats.ai_decisions_correct / state.stats.ai_decisions_total * 100).toFixed(1) : 0;
        document.getElementById('stat-accuracy').innerText = accuracy + "%";
        document.getElementById('count-value').innerText = state.count;

        // Render Decision History
        if (state.decision_history && state.decision_history.length > 0) {
            document.getElementById('decision-log').style.display = 'block';
            const logList = document.getElementById('log-list');
            logList.innerHTML = '';
            state.decision_history.slice().reverse().slice(0, 10).forEach(entry => {
                const li = document.createElement('li');
                li.innerHTML = `<strong>${entry.player}</strong>: ${entry.action} <span class="badge">${entry.reason}</span> <small>(P:${(entry.prob_hit * 100).toFixed(0)}%)</small>`;
                logList.appendChild(li);
            });
        }
    } else {
        document.getElementById('betting-area').style.display = 'none';
        document.getElementById('game-actions').style.display = 'flex';
        document.getElementById('btn-new').style.display = 'none';

        const currentPlayer = state.players[state.current_player_idx];
        document.getElementById('message-area').innerText = "Turno de: " + currentPlayer.owner;

        const isHumanTurn = currentPlayer.owner === "Human";
        document.getElementById('btn-hit').disabled = !isHumanTurn;
        document.getElementById('btn-stand').disabled = !isHumanTurn;
        document.getElementById('btn-double').disabled = !isHumanTurn || currentPlayer.cards.length > 2;
        document.getElementById('btn-withdraw').disabled = !isHumanTurn;

        const btnSplit = document.getElementById('btn-split');
        const btnInsurance = document.getElementById('btn-insurance');
        btnSplit.style.display = (isHumanTurn && currentPlayer.cards.length === 2 && currentPlayer.cards[0].rank === currentPlayer.cards[1].rank) ? 'inline-block' : 'none';
        btnInsurance.style.display = (isHumanTurn && currentPlayer.cards.length === 2 && state.dealer_hand.cards[1].rank === 'A' && !currentPlayer.is_insurance) ? 'inline-block' : 'none';

        if (isHumanTurn) updateAdvice();
    }
}

async function updateAdvice() {
    const data = await fetchData('/api/probability', null, 'GET');
    document.getElementById('ai-advice').innerText = data.recommendation;
    document.getElementById('prob-hit').innerText = (data.hit_win_rate * 100).toFixed(1) + "%";
    document.getElementById('prob-stand').innerText = (data.stand_win_rate * 100).toFixed(1) + "%";
}

function renderHand(elementId, cards) {
    const container = document.getElementById(elementId);
    if (!container) return;
    container.innerHTML = '';
    cards.forEach((card, i) => {
        const div = document.createElement('div');
        div.className = `card ${['Hearts', 'Diamonds'].includes(card.suit) ? 'red' : 'black'} animate-deal`;
        div.style.animationDelay = `${i * 0.1}s`;
        div.innerText = getCardSymbol(card);
        container.appendChild(div);
        if (i === cards.length - 1) playSound('deal');
    });
}

function renderHandHidden(elementId, firstCard) {
    const container = document.getElementById(elementId);
    if (!container) return;
    container.innerHTML = '';

    // First card revealed
    const c1 = document.createElement('div');
    c1.className = `card ${['Hearts', 'Diamonds'].includes(firstCard.suit) ? 'red' : 'black'} animate-deal`;
    c1.innerText = getCardSymbol(firstCard);
    container.appendChild(c1);

    // Second card hidden
    const c2 = document.createElement('div');
    c2.className = 'card back animate-deal';
    c2.innerText = '?';
    container.appendChild(c2);
}

function getCardSymbol(card) {
    const suitMaps = { 'Hearts': '♥', 'Diamonds': '♦', 'Spades': '♠', 'Clubs': '♣' };
    return `${card.rank}${suitMaps[card.suit]}`;
}

function addBet(amount) {
    currentBet += amount;
    document.getElementById('current-bet-display').innerText = currentBet;
    playSound('deal');
}

function resetBet() {
    currentBet = 10;
    document.getElementById('current-bet-display').innerText = currentBet;
}

async function placeBet() {
    const diff = document.getElementById('diff-select').value;
    const state = await fetchData('/api/bet', { amount: currentBet, difficulty: diff });
    updateUI(state);
}

async function startGame() {
    const diff = document.getElementById('diff-select').value;
    const state = await fetchData('/api/start', { num_ai: 2, difficulty: diff });
    updateUI(state);
}

async function hit() {
    const state = await fetchData('/api/hit');
    updateUI(state);
}

async function stand() {
    const state = await fetchData('/api/stand');
    updateUI(state);
}

async function doubleDown() {
    const state = await fetchData('/api/double');
    updateUI(state);
}

async function split() {
    const state = await fetchData('/api/split');
    updateUI(state);
}

async function insurance() {
    const state = await fetchData('/api/insurance');
    updateUI(state);
}

async function withdraw() {
    const state = await fetchData('/api/withdraw');
    updateUI(state);
}

window.onload = async () => {
    initChart();
    const state = await fetchData('/api/start', { num_ai: 2, difficulty: 'HARD' });
    updateUI(state);
};
