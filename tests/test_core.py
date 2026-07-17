from app.core.game import BlackJackGame


def _new_game(num_ai=0):
    game = BlackJackGame()
    game.start_new_round(num_ai=num_ai)
    game.players[0].place_bet(100)
    game.confirm_bets()
    return game


def test_start_new_round_opens_table():
    game = BlackJackGame()
    assert game.game_over is True
    game.start_new_round(num_ai=0)
    assert game.game_over is False
    assert game.waiting_for_bets is True
    assert game.stats['rounds_played'] == 1


def test_confirm_bets_deals_two_cards():
    game = _new_game()
    assert len(game.players[0].cards) == 2
    assert len(game.dealer_hand.cards) == 2
    assert game.waiting_for_bets is False


def test_player_hit_adds_a_card():
    game = _new_game()
    player = game.players[0]
    before = len(player.cards)
    if player.value < 21:
        game.player_hit()
        assert len(player.cards) == before + 1


def test_full_round_reaches_completion():
    game = _new_game()
    game.player_stand()
    assert game.game_over is True
    assert len(game.dealer_hand.cards) >= 2
    assert game.dealer_hand.value >= 17 or game.dealer_hand.busted


def test_second_round_resets_hands():
    game = _new_game()
    game.player_stand()
    game.start_new_round()
    assert game.game_over is False
    for p in game.players:
        assert p.cards == []
        assert p.standing is False
        assert p.busted is False
    assert game.stats['rounds_played'] == 2


def test_turn_advances_through_ai_to_dealer():
    game = _new_game(num_ai=2)
    assert len(game.players) == 3
    game.player_stand()
    assert game.game_over is True
