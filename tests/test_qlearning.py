import os
from app.ai.qlearning import QLearningAgent


def _agent(tmp_path):
    return QLearningAgent(alpha=0.1, gamma=0.9, epsilon=0.1,
                          model_path=str(tmp_path / 'q_table_test.json'))


def test_choose_action_returns_valid_action(tmp_path):
    assert _agent(tmp_path).choose_action((20, 6, 0)) in (0, 1)


def test_get_state_shape(tmp_path):
    from app.core.game import BlackJackGame
    agent = _agent(tmp_path)
    game = BlackJackGame()
    game.start_new_round(num_ai=0)
    game.players[0].place_bet(10)
    game.confirm_bets()
    state = agent.get_state(game, game.players[0])
    assert len(state) == 3
    assert all(isinstance(x, int) for x in state)


def test_training_populates_qtable_and_persists(tmp_path):
    agent = _agent(tmp_path)
    wins, losses, draws = agent.train(num_episodes=500)
    assert wins + losses + draws == 500
    assert len(agent.q_table) > 0
    assert os.path.exists(agent.model_path)


def test_learn_updates_q_value(tmp_path):
    agent = _agent(tmp_path)
    state = (18, 10, 0)
    before = list(agent.get_q_values(state))
    agent.learn(state, action=1, reward=-1, next_state=(21, 10, 0), done=True)
    assert agent.get_q_values(state)[1] != before[1]
