# BlackJack AI WebApp

Project consisting of a Blackjack game where players can face each other or an AI. The AI uses probabilistic algorithms (Monte Carlo) and Reinforcement Learning (Q-Learning) with Card Counting to make decisions.

## Features

- **Core Game**: Standard Blackjack rules (Hit, Stand, Dealer plays to 16).
- **AI Agent**:
  - **Q-Learning**: Learns optimal strategy over thousands of games.
  - **Monte Carlo**: Estimates win probability in real-time.
  - **Card Counting**: Hi-Lo system integrated into decision making.
- **Web Interface**:
  - Flask-based UI.
  - Real-time advice and probability Stats.
  - Dynamic game board.

## Installation

1. **Prerequisites**: Python 3.10+
1. **Instalar dependencias** (si aún no las tienes):

    ```bash
    pip install -r requirements.txt
    ```

2. **Iniciar el Servidor**:

    ```bash
    python app.py
    ```

3. **Jugar**:
    Abre tu navegador en `http://127.0.0.1:5000`

## Testing

- **Core Logic**: `python test_core.py`
- **Monte Carlo**: `python test_montecarlo.py`
- **Q-Learning**: `python test_qlearning.py`
- **Card Counter**: `python test_counter.py`

## Structure

- `app/core`: Game rules and engine.
- `app/ai`: AI algorithms (QLearning, Monte Carlo, Counter).
- `app/web`: Flask routes and templates.
