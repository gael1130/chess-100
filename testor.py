from chess_analyzer import ChessGameAnalyzer
from datetime import datetime, timedelta
import re

# Initialize the analyzer
analyzer = ChessGameAnalyzer()

# Diagnostic info about TCNs
print(f"Total games: {len(analyzer.games)}")
games_with_tcn = [game for game in analyzer.games if 'tcn' in game]
print(f"Games with TCN: {len(games_with_tcn)}")
print(f"\nSample TCN: {games_with_tcn[0].get('tcn')}")
print(f"Length of TCN: {len(games_with_tcn[0].get('tcn', ''))}")

# Get lost games
today = datetime.now()
one_month_ago = (today - timedelta(days=30)).strftime('%Y.%m.%d')
today = today.strftime('%Y.%m.%d')

# Filter the games
lost_games = analyzer.filter_games(
    result='timeout',
    max_accuracy=75,
    min_date=one_month_ago,
    max_date=today
)

# Sort and take most recent 20
recent_losses = sorted(lost_games, 
                      key=lambda x: x['end_time'], 
                      reverse=True)[:20]

print(f"\nFound {len(recent_losses)} recent losses")

def find_games_by_opening(game):
    """Find games with the same opening."""
    opening = game.get('eco', '')
    similar_opening_games = [g for g in analyzer.games 
                           if g.get('eco') == opening 
                           and g['url'] != game['url']]
    return similar_opening_games

def find_games_by_early_moves(game, num_moves=4):
    """Find games that share the same first few moves."""
    if 'tcn' not in game:
        return []
    early_pattern = game['tcn'][:num_moves*2]  # First n moves (2 characters per move)
    similar_games = []
    
    for g in analyzer.games:
        if 'tcn' in g and g['url'] != game['url']:
            if len(g['tcn']) >= len(early_pattern) and g['tcn'].startswith(early_pattern):
                g['similarity'] = len(early_pattern) / len(g['tcn'])  # Add similarity score
                similar_games.append(g)
    
    return similar_games


"""
##### Analyze each recent loss
for game in recent_losses:
    print("\n" + "="*50)
    date = datetime.fromtimestamp(game['end_time']).strftime('%Y-%m-%d')
    opening = game['eco'].split('/')[-1] if 'eco' in game else 'Unknown Opening'
    
    print(f"\nAnalyzing game from {date}")
    print(f"Opening: {opening}")
    print(f"URL: {game['url']}")
    print(f"TCN: {game.get('tcn', 'No TCN available')[:20]}...")  # Show first 20 chars
    
    # Find similar games by opening
    same_opening_games = find_games_by_opening(game)
    print(f"\nFound {len(same_opening_games)} games with same opening")
    if same_opening_games:
        print("Top 3 most recent games with same opening:")
        for g in sorted(same_opening_games, key=lambda x: x['end_time'], reverse=True)[:3]:
            g_date = datetime.fromtimestamp(g['end_time']).strftime('%Y-%m-%d')
            print(f"- {g_date}: {g['url']}")
    
    # Find games with similar early moves
    early_similar_games = find_games_by_early_moves(game)
    print(f"\nFound {len(early_similar_games)} games with same first 4 moves")
    if early_similar_games:
        print("Top 3 most recent games with same early moves:")
        for g in sorted(early_similar_games, key=lambda x: x['end_time'], reverse=True)[:3]:
            g_date = datetime.fromtimestamp(g['end_time']).strftime('%Y-%m-%d')
            print(f"- {g_date}: {g['url']}")
    
    # Try extremely loose similarity matching
    very_similar = analyzer.find_similar_games(game['url'], min_similarity=0.2)  # Only 20% similarity required
    print(f"\nFound {len(very_similar)} games with 20%+ similar moves")
    if very_similar:
        print("Top 3 most similar games:")
        for g in very_similar[:3]:
            g_date = datetime.fromtimestamp(g['end_time']).strftime('%Y-%m-%d')
            similarity = g['similarity'] * 100
            print(f"- {g_date}: {g['url']} (Similarity: {similarity:.1f}%)")

"""

print("+++ Latest Losses +++")


def get_recent_ranked_losses(total_losses: int = 50):
    # Initialize the analyzer
    analyzer = ChessGameAnalyzer()
    
    # Get all lost games
    lost_games = analyzer.filter_games(result='timeout')  # Include timeouts
    lost_games.extend(analyzer.filter_games(result='checkmated'))  # Include checkmates
    lost_games.extend(analyzer.filter_games(result='resigned'))  # Include resignations
    
    # Remove duplicates and sort by date (most recent first)
    lost_games = list({game['url']: game for game in lost_games}.values())
    lost_games.sort(key=lambda x: x['end_time'], reverse=True)
    
    # Take only the most recent losses
    recent_losses = lost_games[:total_losses]
    
    # Filter out games without accuracy data and add accuracy
    losses_with_accuracy = []
    for game in recent_losses:
        accuracy = analyzer.get_player_accuracy(game)
        if accuracy is not None:
            game['player_accuracy'] = accuracy
            losses_with_accuracy.append(game)
    
    # Sort by accuracy (lower accuracy first)
    sorted_games = sorted(losses_with_accuracy, key=lambda x: x['player_accuracy'])
    
    # Print the results
    print(f"\nYour {len(sorted_games)} most recent losses, ranked by accuracy:")
    print("-" * 50)
    
    for i, game in enumerate(sorted_games, 1):
        date = datetime.fromtimestamp(game['end_time']).strftime('%Y-%m-%d')
        is_white = game['white']['username'].lower() == 'kalel1130'
        color = "White" if is_white else "Black"
        opponent = game['black']['username'] if is_white else game['white']['username']
        opening = game['eco'].split('/')[-1] if 'eco' in game else 'Unknown Opening'
        
        print(f"\n{i}. Game from {date}")
        print(f"Accuracy: {game['player_accuracy']:.1f}%")
        print(f"Color: {color}")
        print(f"Opponent: {opponent} (Rating: {game['white' if is_white else 'black']['rating']})")
        print(f"Opening: {opening}")
        print(f"URL: {game['url']}")

# Get the 50 most recent losses, ranked by accuracy
# get_recent_ranked_losses(50)



print("+++ Time Management +++")

# Add this to your testor.py or create a new script
analyzer = ChessGameAnalyzer()
timing_analysis = analyzer.analyze_recent_game_timing()
"""
print("\n=== Recent Games Move Timing Analysis ===")
for game in timing_analysis:
    print(f"\nGame from {game['date']}")
    print(f"Opening: {game['opening']}")
    print(f"Result: {game['result']}")
    print(f"URL: {game['url']}")
    print("\nLongest thinking times:")
    
    for move in game['longest_moves']:
        minutes = int(move['time_spent'] // 60)
        seconds = int(move['time_spent'] % 60)
        remaining_minutes = int(move['remaining_time'] // 60)
        remaining_seconds = int(move['remaining_time'] % 60)
        
        print(f"Move {move['move_number']} ({move['move']}): "
              f"{minutes}m {seconds}s "
              f"(Remaining time: {remaining_minutes}m {remaining_seconds}s)")


 """             
        
"""
# Add this debug code at the start of the timing analysis section
print("\n=== Debugging Time Management Analysis ===")
recent_games = sorted(analyzer.games, key=lambda x: x['end_time'], reverse=True)[:20]
print(f"Number of recent games found: {len(recent_games)}")

# Check for required fields
for game in recent_games[:3]:  # Check first 3 games as sample
    print(f"\nGame URL: {game['url']}")
    print(f"Has clocks: {'clocks' in game}")
    print(f"Has PGN: {'pgn' in game}")
    if 'clocks' in game:
        print(f"Number of clock entries: {len(game['clocks'])}")

"""
print("\n=== Move Timing Analysis ===")
analyzer = ChessGameAnalyzer()

# Get one recent game first as a test
recent_game = sorted(analyzer.games, key=lambda x: x['end_time'], reverse=True)[0]

print(f"\nDEBUG: Analyzing this PGN snippet:")
print(recent_game['pgn'][:500])

# Add a regex test
test_pattern = r'(\d+)\. ([^\{]+)\{?\[%clk (\d+:\d+\.\d+)\]\}(?:\s+([^\{]+)\{?\[%clk (\d+:\d+\.\d+)\]\})?'
test_matches = list(re.finditer(test_pattern, recent_game['pgn'].split('\n\n')[1]))
print(f"\nDEBUG: Test regex found {len(test_matches)} moves")
if test_matches:
    print("First match groups:", [test_matches[0].group(i) for i in range(6)])

move_times = analyzer.get_move_timing_analysis(recent_game)

if move_times:
    print(f"\nAnalyzing game: {recent_game['url']}")
    print("Top 3 longest moves:")
    for move in move_times[:3]:
        minutes = int(move['time_spent'] // 60)
        seconds = int(move['time_spent'] % 60)
        remaining_minutes = int(move['remaining_time'] // 60)
        remaining_seconds = int(move['remaining_time'] % 60)
        
        print(f"Move {move['move_number']} ({move['move']}) as {move['color']}: "
              f"{minutes}m {seconds}s "
              f"(Remaining time: {remaining_minutes}m {remaining_seconds}s)")
else:
    print("No timing data found for this game")