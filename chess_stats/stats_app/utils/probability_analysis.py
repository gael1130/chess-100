from collections import defaultdict
from .game_analysis import get_game_result  # Import the function

def calculate_win_probability(games_sorted, username):
    """Calculate win probability based on game position in a day."""
    wins_by_position = defaultdict(int)
    games_by_position = defaultdict(int)
    current_day = None
    game_position = 1

    for game in games_sorted:
        end_time = game.get('end_time')
        if not end_time:
            continue

        result = get_game_result(game, username)

        if result == 'win':
            wins_by_position[game_position] += 1
        games_by_position[game_position] += 1

        game_position += 1

    probabilities = {pos: (wins / games_by_position[pos] * 100) for pos, wins in wins_by_position.items()}
    return probabilities
