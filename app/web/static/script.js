async function fetchData(url, method = 'POST') {
    const response = await fetch(url, { method: method });
    return response.json();
}

async function updateUI(state) {
    // Render Player Cards
    renderHand('player-cards', state.player_hand.cards);
    document.getElementById('player-score').innerText = `(${state.player_hand.value})`;

    // Render Dealer Cards
    let dealerCards = state.dealer_hand.cards;
    if (!state.game_over && dealerCards.length > 1) {
        // Display Card Back for 2nd
        renderHandHidden('dealer-cards', dealerCards[0]);
    } else {
        renderHand('dealer-cards', dealerCards);
    }

    // Determine Dealer Score visual
    if (!state.game_over && dealerCards.length > 1) {
        document.getElementById('dealer-score').innerText = "(?)";
    } else {
        document.getElementById('dealer-score').innerText = `(${state.dealer_hand.value})`;
    }

    // Messages & Buttons
    if (state.game_over) {
        document.getElementById('message-area').innerText = state.message;
        document.getElementById('btn-hit').disabled = true;
        document.getElementById('btn-stand').disabled = true;
        document.getElementById('btn-new').disabled = false;
    } else {
        document.getElementById('message-area').innerText = "Choose your action...";
        document.getElementById('btn-hit').disabled = false;
        document.getElementById('btn-stand').disabled = false;
        document.getElementById('btn-new').disabled = true;

        // Fetch Probability/AI Advice
        updateAdvice();
    }

    // Count Info
    if (state.count !== undefined) {
        document.getElementById('count-value').innerText = state.count;
        document.getElementById('count-suggestion').innerText = state.suggestion;
    }
}

async function updateAdvice() {
    const data = await fetchData('/api/probability', 'GET');
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

    // First Card
    const c1 = document.createElement('div');
    c1.className = `card ${['Hearts', 'Diamonds'].includes(firstCard.suit) ? 'red' : 'black'}`;
    c1.innerText = getCardSymbol(firstCard);
    container.appendChild(c1);

    // Back Card
    const c2 = document.createElement('div');
    c2.className = 'card black';
    c2.style.backgroundColor = '#95a5a6'; // Back color
    c2.innerText = '?';
    container.appendChild(c2);
}

function getCardSymbol(card) {
    // Basic mapping
    const suitMaps = { 'Hearts': '♥', 'Diamonds': '♦', 'Spades': '♠', 'Clubs': '♣' };
    return `${card.rank}${suitMaps[card.suit]}`;
}

// Actions
async function startGame() {
    const state = await fetchData('/api/start');
    current_state = state;
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
