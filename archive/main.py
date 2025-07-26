import os
import json
import requests
import pandas as pd
from collections import defaultdict
from datetime import datetime

# Constants
USERNAME = 'Kalel1130'
FILENAME = 'chess_data.json'
EXCEL_FILENAME = 'chess_stats_by_day_hour_v2.xlsx'
HEADERS = {'User-Agent': 'My Python Application. Contact me at email@example.com'}

def fetch_and_save_chess_data(username, filename):
    """Fetch chess games data from Chess.com API and save to a JSON file."""
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            print(f"Loading data from {filename}")
            return json.load(file)

    archives_url = f"https://api.chess.com/pub/player/{username}/games/archives"
    response = requests.get(archives_url, headers=HEADERS)

    if response.status_code != 200:
        print(f"Error fetching archives: {response.status_code}")
        return []

    archives = response.json().get('archives', [])
    games = []

    for archive_url in archives:
        response = requests.get(archive_url, headers=HEADERS)
        if response.status_code == 200:
            games.extend(response.json().get('games', []))
        else:
            print(f"Failed to fetch games for {archive_url}")

    with open(filename, 'w') as file:
        json.dump(games, file, indent=4)
        print(f"Data saved to {filename}")

    return games

def get_game_result(game, username):
    """Determine the result of a game for the given username."""
    if game.get('white', {}).get('username') == username:
        return game.get('white', {}).get('result')
    elif game.get('black', {}).get('username') == username:
        return game.get('black', {}).get('result')
    return None

def calculate_rates(data, total_games):
    """Calculate win, loss, and timeout rates."""
    win_rate = round((data.get('wins', 0) / total_games) * 100, 1) if total_games else 0
    loss_rate = round((data.get('losses', 0) / total_games) * 100, 1) if total_games else 0
    timeout_rate = round((data.get('timeouts', 0) / total_games) * 100, 1) if total_games else 0
    return win_rate, loss_rate, timeout_rate

def analyze_games(games, username):
    """Analyze games by month, day, hour, and day-hour combination."""
    games_per_month = defaultdict(int)
    stats_per_month = defaultdict(lambda: defaultdict(int))

    games_per_day = defaultdict(int)
    stats_per_day = defaultdict(lambda: defaultdict(int))

    games_per_hour = defaultdict(int)
    stats_per_hour = defaultdict(lambda: defaultdict(int))

    games_per_day_hour = defaultdict(int)
    stats_per_day_hour = defaultdict(lambda: defaultdict(int))

    for game in games:
        end_time = game.get('end_time')
        if not end_time:
            continue

        end_datetime = datetime.fromtimestamp(end_time)
        month = end_datetime.strftime('%Y-%m')
        day_of_week = end_datetime.strftime('%A')
        hour_of_day = end_datetime.hour
        day_hour = (day_of_week, hour_of_day)

        result = get_game_result(game, username)
        if not result:
            continue

        # Monthly Analysis
        games_per_month[month] += 1
        if result == 'win':
            stats_per_month[month]['wins'] += 1
        elif result in ['checkmated', 'timeout', 'resigned', 'lose', 'abandoned']:
            stats_per_month[month]['losses'] += 1
            if result == 'timeout':
                stats_per_month[month]['timeouts'] += 1

        # Daily Analysis
        games_per_day[day_of_week] += 1
        if result == 'win':
            stats_per_day[day_of_week]['wins'] += 1
        elif result in ['checkmated', 'timeout', 'resigned', 'lose', 'abandoned']:
            stats_per_day[day_of_week]['losses'] += 1
            if result == 'timeout':
                stats_per_day[day_of_week]['timeouts'] += 1

        # Hourly Analysis
        games_per_hour[hour_of_day] += 1
        if result == 'win':
            stats_per_hour[hour_of_day]['wins'] += 1
        elif result in ['checkmated', 'timeout', 'resigned', 'lose', 'abandoned']:
            stats_per_hour[hour_of_day]['losses'] += 1
            if result == 'timeout':
                stats_per_hour[hour_of_day]['timeouts'] += 1

        # Day-Hour Analysis
        games_per_day_hour[day_hour] += 1
        if result == 'win':
            stats_per_day_hour[day_hour]['wins'] += 1
        elif result in ['checkmated', 'timeout', 'resigned', 'lose', 'abandoned']:
            stats_per_day_hour[day_hour]['losses'] += 1
            if result == 'timeout':
                stats_per_day_hour[day_hour]['timeouts'] += 1

    return games_per_month, stats_per_month, games_per_day, stats_per_day, games_per_hour, stats_per_hour, games_per_day_hour, stats_per_day_hour

def generate_report(games_per_category, stats_per_category, category_name):
    """Generate a Pandas DataFrame report for a given category."""
    data = []
    for key, total_games in games_per_category.items():
        win_rate, loss_rate, timeout_rate = calculate_rates(stats_per_category[key], total_games)
        data.append({
            category_name: key,
            'Games Played': total_games,
            'Wins': stats_per_category[key].get('wins', 0),
            'Losses': stats_per_category[key].get('losses', 0),
            'Timeouts': stats_per_category[key].get('timeouts', 0),
            'Win Rate (%)': win_rate,
            'Loss Rate (%)': loss_rate,
            'Timeout Rate (%)': timeout_rate
        })

    return pd.DataFrame(data)

def main():
    games = fetch_and_save_chess_data(USERNAME, FILENAME)
    if not games:
        return

    # Analyze games
    games_per_month, stats_per_month, games_per_day, stats_per_day, games_per_hour, stats_per_hour, games_per_day_hour, stats_per_day_hour = analyze_games(games, USERNAME)

    # Generate reports
    month_df = generate_report(games_per_month, stats_per_month, 'Month')
    day_df = generate_report(games_per_day, stats_per_day, 'Day')
    hour_df = generate_report(games_per_hour, stats_per_hour, 'Hour')
    day_hour_df = generate_report(games_per_day_hour, stats_per_day_hour, 'Day-Hour')

    # Save to Excel
    with pd.ExcelWriter(EXCEL_FILENAME) as writer:
        month_df.to_excel(writer, sheet_name='Monthly', index=False)
        day_df.to_excel(writer, sheet_name='Daily', index=False)
        hour_df.to_excel(writer, sheet_name='Hourly', index=False)
        day_hour_df.to_excel(writer, sheet_name='Day-Hour', index=False)

    print(f"Data saved to {EXCEL_FILENAME}")

if __name__ == "__main__":
    main()
