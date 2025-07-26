from datetime import datetime
import json

# Constants
FILENAME = 'chess_data.json'
USERNAME = 'Kalel1130'
TILT_STREAK_COUNT = 6  # Number of consecutive losses to consider a tilt
TILT_TIME_GAP = 3600 * 3  # 3-hour gap to reset streak

def load_games(filename):
    """Load game data from JSON file."""
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading data: {e}")
        return []

def get_game_result(game, username):
    """Determine the result of a game for the given username."""
    if game.get('white', {}).get('username') == username:
        return game.get('white', {}).get('result')
    elif game.get('black', {}).get('username') == username:
        return game.get('black', {}).get('result')
    return None

def detect_tilt_streaks(games, username, tilt_streak_count, tilt_time_gap):
    """Detect tilt streaks based on consecutive losses within a time gap."""
    games_sorted = sorted(games, key=lambda x: x.get('end_time'))
    tilt_occurrences = []
    current_streak = 0
    streak_start_time = None

    for game in games_sorted:
        end_time = game.get('end_time')
        if not end_time:
            continue

        end_datetime = datetime.fromtimestamp(end_time)
        result = get_game_result(game, username)

        # Check if the result is a loss
        if result in ['checkmated', 'timeout', 'resigned', 'lose', 'abandoned']:
            if current_streak == 0:
                # Start a new streak
                streak_start_time = end_datetime
                current_streak = 1
            elif (end_datetime - streak_start_time).total_seconds() <= tilt_time_gap:
                # Increment streak if within time gap
                current_streak += 1
            else:
                # Reset streak if time gap exceeded
                current_streak = 1
                streak_start_time = end_datetime

            # Record tilt occurrence if streak meets criteria
            if current_streak >= tilt_streak_count:
                tilt_occurrences.append({
                    "tilt_start_time": streak_start_time,
                    "tilt_end_time": end_datetime,
                    "streak_length": current_streak
                })
                current_streak = 0  # Reset streak after recording tilt
        else:
            current_streak = 0  # Reset streak on non-loss game

    return tilt_occurrences

def main():
    games = load_games(FILENAME)
    if not games:
        return

    tilt_occurrences = detect_tilt_streaks(games, USERNAME, TILT_STREAK_COUNT, TILT_TIME_GAP)

    if tilt_occurrences:
        for tilt in tilt_occurrences:
            print(f"Tilt detected from {tilt['tilt_start_time']} to {tilt['tilt_end_time']} "
                  f"with a streak of {tilt['streak_length']} losses.")
    else:
        print("No tilt occurrences detected.")

if __name__ == "__main__":
    main()
