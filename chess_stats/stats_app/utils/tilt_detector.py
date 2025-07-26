from datetime import datetime
from .game_analysis import get_game_result  # Import the function

def detect_tilt_streaks(games, username, tilt_streak_count=6, tilt_time_gap=10800):
    """Detect tilt streaks based on consecutive losses."""
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

        if result in ['checkmated', 'timeout', 'resigned', 'lose', 'abandoned']:
            if current_streak == 0:
                streak_start_time = end_datetime
            current_streak += 1

            if current_streak >= tilt_streak_count:
                tilt_occurrences.append({
                    "start_time": streak_start_time,
                    "end_time": end_datetime,
                    "streak_length": current_streak
                })
                current_streak = 0
        else:
            current_streak = 0

    return tilt_occurrences
