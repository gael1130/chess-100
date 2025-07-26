from collections import defaultdict
from datetime import datetime
from statistics import median
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

__all__ = [
    'analyze_games',
    'generate_monthly_report',
    'analyze_time_stats',
    'get_game_result'
]

@dataclass
class GameStats:
    total_games: int
    wins: int
    losses: int
    timeouts: int
    win_rate: float
    loss_rate: float
    timeout_rate: float
    avg_games_per_day: float
    median_games_per_day: float

def get_game_result(game: Dict, username: str) -> Optional[str]:
    """Determine game result for the user."""
    result = None
    if game.get('white', {}).get('username') == username:
        result = game.get('white', {}).get('result')
    elif game.get('black', {}).get('username') == username:
        result = game.get('black', {}).get('result')
    
    print(f"Debug - username: {username}, result: {result}")  # Add this line

    if result == 'win':
        return 'win'
    elif result == 'timeout':
        return 'timeout'
    elif result in ['checkmated', 'resigned', 'lose', 'abandoned']:
        return 'loss'
    return None

def analyze_games(games: List[Dict], username: str) -> Dict:
    """Analyze games and return overall statistics."""
    total_games = len(games)
    wins = 0
    losses = 0
    timeouts = 0

    for game in games:
        result = get_game_result(game, username)
        if result == 'win':
            wins += 1
        elif result == 'timeout':
            timeouts += 1
            losses += 1  # Count timeouts as losses
        elif result == 'loss':
            losses += 1

    win_rate = (wins / total_games * 100) if total_games > 0 else 0
    timeout_rate = (timeouts / total_games * 100) if total_games > 0 else 0

    return {
        'total_games': total_games,
        'wins': wins,
        'losses': losses,
        'timeouts': timeouts,
        'win_rate': win_rate,
        'timeout_rate': timeout_rate
    }

def generate_monthly_report(games: List[Dict], username: str) -> pd.DataFrame:
    """Generate monthly statistics."""
    monthly_data = defaultdict(lambda: {'games': 0, 'wins': 0, 'losses': 0, 'timeouts': 0})
    
    sorted_games = sorted(games, key=lambda x: x.get('end_time', 0))
    for game in sorted_games:
        end_time = game.get('end_time')
        if not end_time:
            continue
            
        month = datetime.fromtimestamp(end_time).strftime('%Y-%m')
        result = get_game_result(game, username)
        
        if result:
            monthly_data[month]['games'] += 1
            # Fix the result mapping
            if result == 'win':
                monthly_data[month]['wins'] += 1
            elif result == 'timeout':
                monthly_data[month]['timeouts'] += 1
                monthly_data[month]['losses'] += 1  # Count timeouts as losses
            elif result == 'loss':
                monthly_data[month]['losses'] += 1
    
    return pd.DataFrame([
        {
            'Month': month,
            'Games_Played': data['games'],
            'Wins': data['wins'],
            'Losses': data['losses'],
            'Win_Rate_percent': round(data['wins'] / data['games'] * 100, 1) if data['games'] else 0,
            'Timeout_Rate_percent': round(data['timeouts'] / data['games'] * 100, 1) if data['games'] else 0
        }
        for month, data in monthly_data.items()
    ])

def analyze_time_stats(games: List[Dict], username: str) -> List[Dict]:
    """Analyze patterns by day and hour."""
    daily_data = defaultdict(lambda: defaultdict(int))
    
    sorted_games = sorted(games, key=lambda x: x.get('end_time', 0))
    for game in sorted_games:
        end_time = game.get('end_time')
        if not end_time:
            continue
            
        dt = datetime.fromtimestamp(end_time)
        day_name = dt.strftime('%A')
        hour = dt.hour
        result = get_game_result(game, username)
        
        if result:
            daily_data[f"{day_name}-{hour}"]["games_played"] += 1
            daily_data[f"{day_name}-{hour}"][f"{result}s"] += 1
    
    time_stats = []
    for day_hour, stats in daily_data.items():
        day, hour = day_hour.split('-')
        games_played = stats["games_played"]
        time_stats.append({
            'day_of_week': day,
            'hour': int(hour),
            'games_played': games_played,
            'wins': stats.get('wins', 0),
            'losses': stats.get('losses', 0),
            'timeouts': stats.get('timeouts', 0),
            'win_rate_percent': round(stats.get('wins', 0) / games_played * 100, 1),
            'loss_rate_percent': round(stats.get('losses', 0) / games_played * 100, 1),
            'timeout_rate_percent': round(stats.get('timeouts', 0) / games_played * 100, 1)
        })
    
    return sorted(time_stats, key=lambda x: (days_order.index(x['day_of_week']), x['hour']))

# Define order of days for sorting
days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']