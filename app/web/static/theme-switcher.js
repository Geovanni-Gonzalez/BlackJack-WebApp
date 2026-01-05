// ========================================
// THEME SWITCHER SYSTEM
// ========================================

const themes = {
    'midnight-casino': 'Midnight Casino',
    'royal-gold': 'Royal Gold',
    'neon-nights': 'Neon Nights',
    'classic-green': 'Classic Green'
};

// Initialize theme from localStorage or default
function initTheme() {
    const savedTheme = localStorage.getItem('blackjack-theme') || 'midnight-casino';
    applyTheme(savedTheme, false);
}

// Apply theme to document
function applyTheme(themeName, showToast = true) {
    const html = document.documentElement;

    // Remove all theme attributes
    html.removeAttribute('data-theme');

    // Apply new theme (except for default midnight-casino)
    if (themeName !== 'midnight-casino') {
        html.setAttribute('data-theme', themeName);
    }

    // Update UI
    const themeNameDisplay = document.getElementById('current-theme-name');
    if (themeNameDisplay) {
        themeNameDisplay.textContent = themes[themeName] || themeName;
    }

    // Save to localStorage
    localStorage.setItem('blackjack-theme', themeName);

    // Show toast notification
    if (showToast && typeof showToast === 'function') {
        showToast('Tema Cambiado', `Ahora usando: ${themes[themeName]}`, 'success', 3000);
    }

    console.log(`🎨 Theme switched to: ${themes[themeName]}`);
}

// Switch theme (called from UI)
function switchTheme(themeName) {
    applyTheme(themeName, true);
    toggleThemeMenu(); // Close menu after selection
}

// Toggle theme menu visibility
function toggleThemeMenu() {
    const menu = document.getElementById('theme-menu');
    if (!menu) return;

    const isVisible = menu.style.display !== 'none';
    menu.style.display = isVisible ? 'none' : 'block';
}

// Close theme menu when clicking outside
document.addEventListener('click', (e) => {
    const themeSwitcher = document.querySelector('.theme-switcher');
    const themeMenu = document.getElementById('theme-menu');

    if (themeSwitcher && themeMenu && !themeSwitcher.contains(e.target)) {
        themeMenu.style.display = 'none';
    }
});

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
});
