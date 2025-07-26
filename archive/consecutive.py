from datetime import datetime
import json

# Constants
# FILENAME = 'chess_data.json'
FILENAME ='data\Kalel1130_2024-11-10.json'
USERNAME = 'Kalel1130'


def load_games(filename):
    """Load game data from JSON file."""
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading data: {e}")
        return []


def get_game_result(game, username):
    """Determine if the user won or lost the game."""
    result = None
    if game.get('white', {}).get('username') == username:
        result = game.get('white', {}).get('result')
    elif game.get('black', {}).get('username') == username:
        result = game.get('black', {}).get('result')

    if result == 'win':
        return 'win'
    elif result in ['checkmated', 'timeout', 'resigned', 'lose', 'abandoned']:
        return 'loss'
    return None


def calculate_probability(numerator, denominator):
    """Calculate percentage probability."""
    return (numerator / denominator * 100) if denominator else 0


def analyze_streaks(games_sorted, username):
    """Analyze win/loss streaks within the same hour."""
    win_after_win_same_hour = 0
    loss_after_loss_same_hour = 0
    total_win_streaks_same_hour = 0
    total_loss_streaks_same_hour = 0

    previous_result = None
    previous_hour = None

    for game in games_sorted:
        end_time = game.get('end_time')
        if not end_time:
            continue

        hour_of_day = datetime.fromtimestamp(end_time).hour
        current_result = get_game_result(game, username)

        if not current_result:
            continue

        if previous_result and previous_hour == hour_of_day:
            if previous_result == 'win':
                total_win_streaks_same_hour += 1
                if current_result == 'win':
                    win_after_win_same_hour += 1
            elif previous_result == 'loss':
                total_loss_streaks_same_hour += 1
                if current_result == 'loss':
                    loss_after_loss_same_hour += 1

        previous_result = current_result
        previous_hour = hour_of_day

    win_probability = calculate_probability(win_after_win_same_hour, total_win_streaks_same_hour)
    loss_probability = calculate_probability(loss_after_loss_same_hour, total_loss_streaks_same_hour)

    return win_probability, loss_probability


def analyze_sequences(games_sorted, username):
    """Analyze 'win-loss' and 'loss-win' sequences within the same hour."""
    win_after_win_loss_same_hour = 0
    win_after_loss_win_same_hour = 0
    total_win_loss_sequences_same_hour = 0
    total_loss_win_sequences_same_hour = 0

    previous_result = None
    previous_hour = None

    for i, game in enumerate(games_sorted):
        end_time = game.get('end_time')
        if not end_time:
            continue

        hour_of_day = datetime.fromtimestamp(end_time).hour
        current_result = get_game_result(game, username)

        if not current_result:
            continue

        if previous_result and previous_hour == hour_of_day:
            if previous_result == 'win' and current_result == 'loss':
                total_win_loss_sequences_same_hour += 1
                next_game_result = get_game_result(games_sorted[i + 1], username) if i + 1 < len(games_sorted) else None
                if next_game_result == 'win':
                    win_after_win_loss_same_hour += 1
            elif previous_result == 'loss' and current_result == 'win':
                total_loss_win_sequences_same_hour += 1
                next_game_result = get_game_result(games_sorted[i + 1], username) if i + 1 < len(games_sorted) else None
                if next_game_result == 'win':
                    win_after_loss_win_same_hour += 1

        previous_result = current_result
        previous_hour = hour_of_day

    win_after_win_loss_probability = calculate_probability(win_after_win_loss_same_hour, total_win_loss_sequences_same_hour)
    win_after_loss_win_probability = calculate_probability(win_after_loss_win_same_hour, total_loss_win_sequences_same_hour)

    return win_after_win_loss_probability, win_after_loss_win_probability


def main():
    games = load_games(FILENAME)
    if not games:
        return

    games_sorted = sorted(games, key=lambda x: x.get('end_time'))

    win_prob, loss_prob = analyze_streaks(games_sorted, USERNAME)
    print(f"Probability of winning the next game after a win in the same hour: {win_prob:.2f}%")
    print(f"Probability of losing the next game after a loss in the same hour: {loss_prob:.2f}%")

    win_after_wl_prob, win_after_lw_prob = analyze_sequences(games_sorted, USERNAME)
    print(f"Probability of winning the next game after a 'win-loss' sequence in the same hour: {win_after_wl_prob:.2f}%")
    print(f"Probability of winning the next game after a 'loss-win' sequence in the same hour: {win_after_lw_prob:.2f}%")


if __name__ == "__main__":
    main()
