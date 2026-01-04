let currentBet = 10;
let current_state = null;

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

        let statusText = player.busted ? " - BUSTED" : (player.withdrawn ? " - WITHDRAWN" : "");
        let betText = player.bet > 0 ? ` [Bet: $${player.bet}]` : "";

        handDiv.innerHTML = `<h2>${player.owner} <span id="${player.owner}-score">(${player.value})${statusText}</span></h2>
                             <p class="balance-display">Balance: $${player.balance}${betText}</p>
                             <div class="cards" id="${player.owner}-cards"></div>`;
        container.appendChild(handDiv);
        renderHand(`${player.owner}-cards`, player.cards);
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

        // Show Stats
        document.getElementById('stats-area').style.display = 'block';
        document.getElementById('stat-rounds').innerText = state.stats.rounds_played;
        document.getElementById('stat-human').innerText = state.stats.player_wins;
        document.getElementById('stat-ai').innerText = state.stats.ai_wins;

        const accuracy = state.stats.ai_decisions_total > 0 ? (state.stats.ai_decisions_correct / state.stats.ai_decisions_total * 100).toFixed(1) : 0;
        document.getElementById('stat-accuracy').innerText = accuracy + "%";
        document.getElementById('stat-decisions').innerText = state.stats.ai_decisions_total;

        // Render Decision History Log
        if (state.decision_history && state.decision_history.length > 0) {
            document.getElementById('decision-log').style.display = 'block';
            const logList = document.getElementById('log-list');
            logList.innerHTML = '';
            state.decision_history.slice().reverse().forEach(entry => {
                const li = document.createElement('li');
                li.innerHTML = `<strong>${entry.player}</strong>: ${entry.action} 
                                <span class="badge">${entry.reason}</span> 
                                <small>(P_Hit: ${(entry.prob_hit * 100).toFixed(0)}%, Count: ${entry.count})</small>`;
                logList.appendChild(li);
            });
        }
    } else {
        document.getElementById('betting-area').style.display = 'none';
        document.getElementById('game-actions').style.display = 'block';
        document.getElementById('btn-new').style.display = 'none';

        document.getElementById('message-area').innerText = "Actions for " + state.players[state.current_player_idx].owner;
        const isHumanTurn = state.players[state.current_player_idx].owner === "Human";
        document.getElementById('btn-hit').disabled = !isHumanTurn;
        document.getElementById('btn-stand').disabled = !isHumanTurn;
        document.getElementById('btn-double').disabled = !isHumanTurn || state.players[0].cards.length > 2;
        document.getElementById('btn-withdraw').disabled = !isHumanTurn;

        if (isHumanTurn) updateAdvice();
    }

    // Count Info
    if (state.count !== undefined) {
        document.getElementById('count-value').innerText = state.count;
        document.getElementById('count-suggestion').innerText = state.suggestion;
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
    container.innerHTML = '';
    cards.forEach(card => {
        const div = document.createElement('div');
        div.className = `card ${['Hearts', 'Diamonds'].includes(card.suit) ? 'red' : 'black'}`;
        div.innerText = getCardSymbol(card);
        container.appendChild(div);
    });
}

function renderHandHidden(elementId, firstCard) {
    const container = document.getElementById(elementId);
    container.innerHTML = '';
    const c1 = document.createElement('div');
    c1.className = `card ${['Hearts', 'Diamonds'].includes(firstCard.suit) ? 'red' : 'black'}`;
    c1.innerText = getCardSymbol(firstCard);
    container.appendChild(c1);
    const c2 = document.createElement('div');
    c2.className = 'card black';
    c2.style.backgroundColor = '#95a5a6';
    c2.innerText = '?';
    container.appendChild(c2);
}

function getCardSymbol(card) {
    const suitMaps = { 'Hearts': '♥', 'Diamonds': '♦', 'Spades': '♠', 'Clubs': '♣' };
    return `${card.rank}${suitMaps[card.suit]}`;
}

// Betting Helpers
function addBet(amount) {
    currentBet += amount;
    document.getElementById('current-bet-display').innerText = currentBet;
}

function resetBet() {
    currentBet = 10;
    document.getElementById('current-bet-display').innerText = currentBet;
}

// Actions
async function placeBet() {
    const diff = document.getElementById('diff-select').value;
    const state = await fetchData('/api/bet', { amount: currentBet, difficulty: diff });
    updateUI(state);
}

async function startGame() {
    // This starts a new round/session
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

async function withdraw() {
    const state = await fetchData('/api/withdraw');
    updateUI(state);
}

// Initial load
window.onload = async () => {
    const state = await fetchData('/api/start', { num_ai: 2, difficulty: 'HARD' });
    updateUI(state);
};
