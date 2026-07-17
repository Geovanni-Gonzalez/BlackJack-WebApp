# Blackjack Pro Simulator - Technical Documentation (IC-3002)

## 🎯 Project Overview

This application is an advanced Blackjack simulator developed for the **IC-3002 Análisis de Algoritmos** course at Tecnológico de Costa Rica. It combines classic game logic with modern AI strategies and a high-performance "Pro" web interface.

---

## 🧠 AI & Algorithms

The simulator implements three distinct layers of intelligence:

### 1. Monte Carlo Simulations

- **Purpose**: Calculates the mathematical win probability for any given hand.
- **Implementation**: When requested, the system simulates 500+ random round completions (stochastically) from the current state to determine the "Hit Win %" vs "Stand Win %".
- **Usage**: Used to train the Q-Learning agent and provide real-time advice to the player.

### 2. Q-Learning (Reinforcement Learning)

- **Purpose**: A persistent AI that learns from experience.
- **State Space**: (Current Total, Dealer Upcard, Is Soft Hand).
- **Rewards**: +1 for Win, 0 for Push, -1 for Loss.
- **Persistence**: The Q-Table is saved to `q_table.json` and loads automatically on startup, retaining its "expertise" across sessions.

### 3. Card Counting (Hi-Lo System)

- **Purpose**: Tracks the "richness" of the remaining deck.
- **Values**: Cards 2-6 (+1), 7-9 (0), 10-A (-1).
- **Impact**: The "Expert" AI adjusts its aggression based on the current True Count.

---

## 📊 Evaluation Metrics

To meet the university requirements, the system tracks and displays:

- **Rounds Played**: Total volume of data collected.
- **AI Decision Accuracy**: % of times the AI chose the action with the highest Monte Carlo win rate.
- **Player Strategic Accuracy**: % of times the human player followed the optimal probabilistic strategy.
- **Balance Evolution**: Real-time Chart.js graph showing financial performance.

---

## 🛠 Execution Instructions

1. **Prerequisites**: Python 3.10+ installed.
2. **Setup**: Run `pip install -r requirements.txt`.
3. **Run**: Execute `python app.py`.
4. **Access**: Navigate to `http://127.0.0.1:5000` in your browser.
5. **Gameplay**:
   - Enter the Casino via the cinematic overlay.
   - Adjust the AI Intelligence to "Experta" for full algorithmic tracking.
   - Place bets using the chip rack and observe the "Elite Log" for decision traceability.

---

## 💎 Design Philosophy

The "Pro Edition" focuses on **Cinematic Immersion**:

- **3D Perspective**: The table is rendered with a 15-degree tilt for depth.
- **Physical Shoe**: Cards animate from a 3D dispenser.
- **AI Reactions**: Players and Dealer express emotions via dynamic emojis.
- **Premium Palette**: Midnight Blue and Gold theme for a high-class casino feel.
