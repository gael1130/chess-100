from datetime import datetime
import json
from collections import defaultdict
from statistics import median, mean

# Constants
FILENAME = 'chess_data.json'
USERNAME = 'Kalel1130'
X = 4  # Adjustable threshold for games per day


def load_games(filename):
    """Load game data from JSON file."""
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading data: {e}")
        return []


def get_game_result(game, username):
    """Determine the result of the game for the given username."""
    if game.get('white', {}).get('username') == username:
        return game.get('white', {}).get('result')
    elif game.get('black', {}).get('username') == username:
        return game.get('black', {}).get('result')
    return None


def calculate_win_probability_by_position(games_sorted, username):
    """Calculate win probability for each game position of the day."""
    wins_by_position = defaultdict(int)
    games_by_position = defaultdict(int)
    current_day = None
    game_position = 1

    for game in games_sorted:
        end_time = game.get('end_time')
        if not end_time:
            continue

        end_date = datetime.fromtimestamp(end_time).date()

        if end_date != current_day:
            current_day = end_date
            game_position = 1

        result = get_game_result(game, username)

        games_by_position[game_position] += 1
        if result == 'win':
            wins_by_position[game_position] += 1

        game_position += 1

    win_probabilities = {
        position: (wins / games_by_position[position] * 100)
        for position, wins in wins_by_position.items()
    }

    return win_probabilities


def calculate_average_and_median_games(games):
    """Calculate the average and median number of games played per day."""
    unique_days = set()
    games_per_day = defaultdict(int)

    for game in games:
        end_time = game.get('end_time')
        if end_time:
            end_date = datetime.fromtimestamp(end_time).date()
            unique_days.add(end_date)
            games_per_day[end_date] += 1

    average_games = len(games) / len(unique_days) if unique_days else 0
    median_games = median(games_per_day.values())

    return average_games, median_games


def calculate_loss_rate(games, username, threshold):
    """Calculate loss rates for days with games above and below the threshold."""
    games_per_day = defaultdict(int)
    losses_per_day = defaultdict(int)

    for game in games:
        end_time = game.get('end_time')
        if not end_time:
            continue

        end_date = datetime.fromtimestamp(end_time).date()
        result = get_game_result(game, username)

        games_per_day[end_date] += 1
        if result in ['checkmated', 'timeout', 'resigned', 'lose', 'abandoned']:
            losses_per_day[end_date] += 1

    more_than_threshold_days = [day for day in games_per_day if games_per_day[day] > threshold]
    less_than_threshold_days = [day for day in games_per_day if games_per_day[day] <= threshold]

    def loss_rate(days):
        total_games = sum(games_per_day[day] for day in days)
        total_losses = sum(losses_per_day[day] for day in days)
        return (total_losses / total_games * 100) if total_games else 0

    loss_rate_more = loss_rate(more_than_threshold_days)
    loss_rate_less = loss_rate(less_than_threshold_days)

    return loss_rate_more, loss_rate_less


def main():
    games = load_games(FILENAME)
    if not games:
        return

    # Sort games by end time
    games_sorted = sorted(games, key=lambda x: x.get('end_time'))

    # Calculate win probabilities by game position
    win_probabilities = calculate_win_probability_by_position(games_sorted, USERNAME)
    for position, probability in sorted(win_probabilities.items()):
        print(f"Probability of winning the {position} game of the day: {probability:.2f}%")

    # Calculate average and median games per day
    average_games, median_games = calculate_average_and_median_games(games)
    print(f"Average games played per day: {average_games:.2f}")
    print(f"Median games played per day: {median_games}")

    # Calculate loss rates based on the number of games played per day
    loss_rate_more, loss_rate_less = calculate_loss_rate(games, USERNAME, X)
    print(f"Loss rate for days with more than {X} games: {loss_rate_more:.2f}%")
    print(f"Loss rate for days with {X} or fewer games: {loss_rate_less:.2f}%")


if __name__ == "__main__":
    main()
