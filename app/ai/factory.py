"""Process-wide singletons for the AI components.

Instantiating a ``QLearningAgent`` (which loads ``q_table.json`` from disk) or a
``MonteCarloSimulator`` on every request/turn is wasteful. These accessors keep
one shared instance per process. They are deliberately plain functions so that
``BlackJackGame`` can reference them without storing un-picklable objects on the
instance (the game is serialised into the Flask session).
"""

_agent = None
_simulators = {}


def get_agent():
    """Return the shared Q-Learning agent (lazy-loaded)."""
    global _agent
    if _agent is None:
        from .qlearning import QLearningAgent
        _agent = QLearningAgent()
    return _agent


def get_simulator(num_simulations=500):
    """Return a shared Monte Carlo simulator for the given sample size."""
    sim = _simulators.get(num_simulations)
    if sim is None:
        from .montecarlo import MonteCarloSimulator
        sim = MonteCarloSimulator(num_simulations=num_simulations)
        _simulators[num_simulations] = sim
    return sim


def reset():
    """Clear cached singletons (used by tests)."""
    global _agent, _simulators
    _agent = None
    _simulators = {}
