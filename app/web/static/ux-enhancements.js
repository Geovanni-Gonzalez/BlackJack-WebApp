// ========================================
// PHASE 9: UX & NAVIGATION ENHANCEMENTS
// ========================================

// Toast Notification System
function showToast(title, message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const icons = {
        success: '✓',
        error: '✕',
        info: 'ℹ',
        warning: '⚠'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-icon">${icons[type] || icons.info}</div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;

    container.appendChild(toast);

    // Auto-remove after duration
    setTimeout(() => {
        toast.classList.add('removing');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Keyboard Shortcuts Handler
function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ignore if typing in input
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        // Ignore if modal is open
        const modalOpen = document.getElementById('rule-modal').style.display !== 'none' ||
            document.getElementById('leaderboard-modal').style.display !== 'none';

        if (modalOpen) {
            if (e.key === 'Escape') {
                toggleManual();
                toggleLeaderboard();
            }
            return;
        }

        const key = e.key.toLowerCase();

        switch (key) {
            case 'h':
                if (!current_state?.game_over && !current_state?.waiting_for_bets) {
                    hit();
                    showToast('Acción', 'Pediste carta (H)', 'info', 2000);
                }
                break;
            case 's':
                if (!current_state?.game_over && !current_state?.waiting_for_bets) {
                    stand();
                    showToast('Acción', 'Te plantaste (S)', 'info', 2000);
                }
                break;
            case 'd':
                if (!current_state?.game_over && !current_state?.waiting_for_bets) {
                    doubleDown();
                    showToast('Acción', 'Doblaste la apuesta (D)', 'info', 2000);
                }
                break;
            case 'r':
                if (!current_state?.game_over && !current_state?.waiting_for_bets) {
                    withdraw();
                    showToast('Acción', 'Te retiraste (R)', 'info', 2000);
                }
                break;
            case ' ':
                e.preventDefault();
                if (current_state?.waiting_for_bets) {
                    placeBet();
                } else if (current_state?.game_over) {
                    startGame();
                }
                break;
            case 'l':
                toggleLeaderboard();
                break;
            case 'm':
                toggleManual();
                break;
            case 'escape':
                // Close any open modals
                document.getElementById('rule-modal').style.display = 'none';
                document.getElementById('leaderboard-modal').style.display = 'none';
                break;
        }
    });
}

// Enhanced Tooltip System
function initTooltips() {
    const tooltipData = {
        'btn-hit': { text: 'Pedir carta (H)', shortcut: 'H' },
        'btn-stand': { text: 'Plantarse (S)', shortcut: 'S' },
        'btn-double': { text: 'Doblar apuesta (D)', shortcut: 'D' },
        'btn-split': { text: 'Dividir mano', shortcut: '' },
        'btn-insurance': { text: 'Seguro contra Blackjack', shortcut: '' },
        'btn-withdraw': { text: 'Retirarse (R)', shortcut: 'R' },
        'btn-start': { text: 'Repartir cartas (Space)', shortcut: 'Space' }
    };

    Object.entries(tooltipData).forEach(([id, data]) => {
        const element = document.getElementById(id);
        if (!element) return;

        element.classList.add('tooltip');
        const tooltip = document.createElement('span');
        tooltip.className = 'tooltiptext';
        tooltip.textContent = data.text;
        element.appendChild(tooltip);
    });
}

// Auto-save to Leaderboard
async function autoSaveToLeaderboard() {
    if (!current_state || !current_state.players || current_state.players.length === 0) return;

    const player = current_state.players[0];
    const initialBalance = 1000; // Default starting balance

    // Only save if player made profit and played at least 3 rounds
    if (player.balance > initialBalance && current_state.stats.rounds_played >= 3) {
        try {
            const result = await fetchData('/api/leaderboard', {}, 'POST');
            if (result.success) {
                showToast('¡Hall of Fame!', 'Tu sesión ha sido guardada en el leaderboard', 'success', 5000);
            }
        } catch (error) {
            console.error('Auto-save to leaderboard failed:', error);
        }
    }
}

// Add Ripple Effect to Buttons
function addRippleEffect() {
    const buttons = document.querySelectorAll('.game-btn, .gold-btn, .ghost-btn, .chip');
    buttons.forEach(button => {
        if (!button.classList.contains('ripple')) {
            button.classList.add('ripple');
        }
    });
}

// Enhanced Card Deal Animation with Glow
function dealCardWithGlow(elementId, card) {
    const container = document.getElementById(elementId);
    if (!container) return;

    const cardCont = document.createElement('div');
    cardCont.className = 'card-container animate-deal card-glow';

    const cardDiv = document.createElement('div');
    cardDiv.className = `card ${card.suit}`;
    cardDiv.innerHTML = `
        <div class="card-value">${card.rank}</div>
        <div class="card-suit">${getSuitSymbol(card.suit)}</div>
    `;

    cardCont.appendChild(cardDiv);
    container.appendChild(cardCont);

    playSound('deal');
}

// Smooth Scroll to Decision Log
function scrollToLog() {
    const logSection = document.querySelector('.decision-tracker');
    if (logSection) {
        logSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

// Show Loading State
function showLoading(buttonId) {
    const button = document.getElementById(buttonId);
    if (!button) return;

    button.disabled = true;
    button.dataset.originalText = button.innerHTML;
    button.innerHTML = '<span class="loading-spinner"></span>';
}

function hideLoading(buttonId) {
    const button = document.getElementById(buttonId);
    if (!button || !button.dataset.originalText) return;

    button.disabled = false;
    button.innerHTML = button.dataset.originalText;
    delete button.dataset.originalText;
}

// Initialize all UX enhancements
function initUXEnhancements() {
    initKeyboardShortcuts();
    initTooltips();
    addRippleEffect();

    // Show welcome toast
    setTimeout(() => {
        showToast(
            '¡Bienvenido a BlackJack Pro!',
            'Usa atajos de teclado: H (Hit), S (Stand), D (Double), Space (Deal)',
            'info',
            6000
        );
    }, 1000);

    console.log('✨ UX Enhancements initialized');
}

// Helper function for suit symbols
function getSuitSymbol(suit) {
    const symbols = {
        'hearts': '♥',
        'diamonds': '♦',
        'clubs': '♣',
        'spades': '♠'
    };
    return symbols[suit] || suit;
}
