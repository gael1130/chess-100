from django.shortcuts import render
from .utils.data_loader import fetch_and_save_chess_data
from .utils.game_analysis import analyze_games, generate_monthly_report, analyze_time_stats
from datetime import datetime
import pandas as pd
import json
from django.core.serializers.json import DjangoJSONEncoder

def process_game(game, username):
    """Process a single game and extract relevant information."""
    end_time = game.get('end_time')
    game_data = {
        'end_time_converted': datetime.fromtimestamp(end_time) if end_time else None
    }
    
    # Process player information
    white_player = game.get('white', {})
    black_player = game.get('black', {})
    white_username = white_player.get('username', '').strip()
    black_username = black_player.get('username', '').strip()
    
    # Determine player's color and ratings
    if white_username.lower() == username.lower():
        game_data.update({
            'player_color': 'white',
            'opponent_color': 'black',
            'opponent_username': black_username,
            'player_rating': white_player.get('rating', 'N/A'),
            'opponent_rating': black_player.get('rating', 'N/A'),
            'white': white_player,
            'black': black_player
        })
    elif black_username.lower() == username.lower():
        game_data.update({
            'player_color': 'black',
            'opponent_color': 'white',
            'opponent_username': white_username,
            'player_rating': black_player.get('rating', 'N/A'),
            'opponent_rating': white_player.get('rating', 'N/A'),
            'white': white_player,
            'black': black_player
        })
    
    # Process accuracies
    accuracies = game.get('accuracies', {})
    normalized_accuracies = {k.strip().lower(): v for k, v in accuracies.items()}
    game_data['player_accuracy'] = f"{normalized_accuracies.get(game_data.get('player_color')):.2f}" if game_data.get('player_color') and normalized_accuracies.get(game_data.get('player_color')) is not None else 'N/A'
    game_data['opponent_accuracy'] = f"{normalized_accuracies.get(game_data.get('opponent_color')):.2f}" if game_data.get('opponent_color') and normalized_accuracies.get(game_data.get('opponent_color')) is not None else 'N/A'
    
    # Add URL and time class
    game_data['url'] = game.get('url', '#')
    game_data['time_class'] = game.get('time_class', 'Unknown')
    
    return game_data

def home(request):
    if request.method != 'POST':
        return render(request, 'stats_app/home.html')

    username = request.POST.get('username')
    try:
        # Fetch games data
        games = fetch_and_save_chess_data(username)
        if not games:
            return render(request, 'stats_app/home.html', 
                        {'error_message': f"No games found for user '{username}'."})

        # Process each game
        processed_games = [process_game(game, username) for game in games]

        # Analyze games
        stats = analyze_games(games, username)
        monthly_report = generate_monthly_report(games, username)
        time_stats = analyze_time_stats(games, username)

        # Prepare monthly report data for JavaScript
        monthly_report_json = json.dumps(
            monthly_report.to_dict('records') if isinstance(monthly_report, pd.DataFrame) 
            else monthly_report,
            cls=DjangoJSONEncoder
        )

        context = {
            'username': username,
            'games': processed_games,
            'total_games': stats['total_games'],
            'wins': stats['wins'],
            'losses': stats['losses'],
            'timeouts': stats['timeouts'],
            'win_rate': stats['win_rate'],
            'timeout_rate': stats['timeout_rate'],
            'monthly_report': monthly_report.to_dict('records') if isinstance(monthly_report, pd.DataFrame) else monthly_report,
            'monthly_report_json': monthly_report_json,
            'time_stats': time_stats
        }

        return render(request, 'stats_app/results.html', context)

    except Exception as e:
        import traceback
        print("Error occurred:", traceback.format_exc())  # This will print the full error trace
        return render(request, 'stats_app/home.html', 
                     {'error_message': f"An error occurred: {str(e)}"})