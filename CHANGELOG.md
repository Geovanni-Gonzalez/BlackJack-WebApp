# Changelog

## Roadmap execution — engine repair, tests, algorithmic fidelity, tooling

### P0 — Correctness (blocking)
- **Fixed non-playable engine:** `start_new_round` now fully resets each hand and
  sets `game_over = False` (it was permanently `True`, making `hit`/`stand` no-ops).
- Removed the duplicated `next_turn`; turn advancement unified on `is_ai` via
  `_advance_to_human_or_finish`.
- Added the missing `BlackJackGame.check_game_over` used by `/api/withdraw`.
- Win attribution now uses `is_ai` instead of a fragile `"Human" in name` check.
- `SECRET_KEY` and DB URI moved out of source into the environment / `config.py`.

### P1 — Tests + CI
- Rewrote `tests/` as real `pytest` suites with assertions (rules, counter, engine,
  Monte Carlo, Q-Learning) incl. a regression test that `player_hit` adds a card.
- CI now runs `pytest` (previously compile-only). **24 tests pass.**

### P2 — Algorithmic fidelity
- Monte Carlo now uses the player's real cards and the **actual remaining shoe**
  (so card composition / counting feeds the probability) and deals the dealer a
  hidden hole card played to 17.
- Added a distinct **MEDIUM** difficulty (Monte Carlo only).
- Shared AI singletons via `app/ai/factory.py` (no per-request/turn re-instantiation).
- `start_training` socket now runs **real** Q-Learning training and streams actual
  win-rate/epsilon (was hardcoded fake progress).

### P3 — Deployment & hygiene
- Added `Dockerfile`, `docker-compose.yml`, `.env.example`, `.gitattributes`
  (LF normalization), `pyproject.toml` (ruff + pytest config), `app/config.py`.
- `.gitignore` extended to exclude `instance/`, `flask_session/`, `*.db`.

### Pending (manual)
- Untrack already-committed artifacts (blocked here by a GitHub Desktop index lock):
  `git rm -r --cached instance flask_session` and any `__pycache__`.
