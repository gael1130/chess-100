import re
import json
from datetime import datetime


player = "Kalel1130"

def format_time_spent(seconds):
    """
    Convert seconds to a human-readable string showing days, hours, minutes, and seconds as appropriate.
    
    Args:
        seconds (float): Time in seconds
        
    Returns:
        str: Formatted string like "2 days 3 hours 45 minutes" or "5 minutes 30 seconds"
    """
    days = int(seconds // (24 * 3600))
    remaining = seconds % (24 * 3600)
    hours = int(remaining // 3600)
    remaining = remaining % 3600
    minutes = int(remaining // 60)
    remaining_seconds = int(remaining % 60)
    
    parts = []
    
    if days > 0:
        parts.append(f"{days} {'day' if days == 1 else 'days'}")
    if hours > 0:
        parts.append(f"{hours} {'hour' if hours == 1 else 'hours'}")
    if minutes > 0:
        parts.append(f"{minutes} {'minute' if minutes == 1 else 'minutes'}")
    if remaining_seconds > 0 and not days:  # Only show seconds if less than a day
        parts.append(f"{remaining_seconds} {'second' if remaining_seconds == 1 else 'seconds'}")
    
    # Handle cases where time is less than 1 second
    if not parts:
        return "less than 1 second"
    
    return " ".join(parts)

def convert_timestamp(unix_time):
    """Convert Unix timestamp to readable datetime string"""
    return datetime.fromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M:%S')

def convert_time_control(time_control_str):
    """
    Convert time control string to seconds.
    Handles both integer formats and fraction formats like '1/86400'
    """
    try:
        # First try parsing as a simple integer
        return int(time_control_str)
    except ValueError:
        try:
            # If that fails, try parsing as a fraction
            numerator, denominator = map(int, time_control_str.split('/'))
            return int(numerator * (86400 / denominator))  # Convert to seconds
        except (ValueError, ZeroDivisionError):
            print(f"Warning: Invalid time control format: {time_control_str}")
            return 600  # Default to 10 minutes

def process_chess_data(games_json, player_name, num_games=3):
    """
    Process chess games to extract PGNs, time control, moves, clock times, and time spent for the specified player.
    """
    processed_games = []

    # Define regex patterns
    moves_pattern = re.compile(r'\n\n(1\..*)', re.DOTALL)
    move_clock_pattern = re.compile(r'(\d+\.\s([a-zA-Z0-9#+=]+)\s\{\[%clk\s(\d+:\d{2}:\d{2}(\.\d)?)\]\})\s(\d+\.\.\.\s([a-zA-Z0-9#+=]+)\s\{\[%clk\s(\d+:\d{2}:\d{2}(\.\d)?)\]\})?')

    def clock_to_seconds(clock):
        """Convert clock time format (H:MM:SS or H:MM:SS.ss) to seconds, ignoring microseconds."""
        try:
            parts = clock.split(':')
            hours, minutes, seconds = 0, 0, 0
            if len(parts) == 3:  # H:MM:SS(.ss)
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = float(parts[2])
            elif len(parts) == 2:  # MM:SS(.ss)
                minutes = int(parts[0])
                seconds = float(parts[1])
            else:
                raise ValueError("Invalid clock format")
            return hours * 3600 + minutes * 60 + int(seconds)
        except (ValueError, IndexError):
            print(f"Warning: Invalid clock format: {clock}")
            return 0

    for i, game in enumerate(games_json[:num_games]):
        pgn = game.get("pgn", "")
        time_control = convert_time_control(game.get("time_control", "600"))
        current_white_time = time_control
        current_black_time = time_control
        end_time_utc = game.get("end_time", 0)
        readable_time_utc = convert_timestamp(end_time_utc)
        game_url = game.get("url", "No URL available")
        
        # Determine if the player is playing as White or Black
        headers = game.get("headers", {})
        white_player = headers.get("White", "")
        black_player = headers.get("Black", "")
        player_is_white = (white_player == player_name)
        
        # Extract moves part
        moves_match = moves_pattern.search(pgn)
        moves = moves_match.group(1).strip() if moves_match else ""

        white_moves = []
        black_moves = []

        # Extract moves and clock times for White and Black
        for match in move_clock_pattern.finditer(moves):
            move_number = match.group(1)
            white_move = match.group(2)
            white_clock = match.group(3)
            black_move = match.group(6)
            black_clock = match.group(7)

            # Calculate White time spent
            if white_move and white_clock:
                white_time = clock_to_seconds(white_clock)
                time_spent = round(current_white_time - white_time, 2)
                current_white_time = white_time
                white_moves.append((move_number, white_move, white_clock, time_spent))

            # Calculate Black time spent
            if black_move and black_clock:
                black_time = clock_to_seconds(black_clock)
                time_spent = round(current_black_time - black_time, 2)
                current_black_time = black_time
                black_moves.append((move_number, black_move, black_clock, time_spent))

        # Get top thinks only for the player
        player_moves = white_moves if player_is_white else black_moves
        player_top_thinks = find_top_thinks(player_moves)

        # Append game details
        processed_games.append({
            "pgn": pgn,
            "time_control": time_control,
            "end_time_utc": readable_time_utc,
            "url": game_url,
            "player_color": "White" if player_is_white else "Black",
            "player_top_thinks": player_top_thinks,
        })

    return processed_games

def find_top_thinks(moves, top_n=3):
    """
    Find the top N moves where the player spent the most time thinking.
    """
    thinks = []
    
    for move_data in moves:
        full_move, move, clock, time_spent = move_data
        move_number = full_move.split('.')[0]
        think = {
            'move_number': move_number,
            'move': move,
            'clock': clock,
            'time_spent': time_spent,
            'time_spent_formatted': format_time_spent(time_spent)
        }
        thinks.append(think)
    
    # Sort by time spent and get top N
    return sorted(thinks, key=lambda x: x['time_spent'], reverse=True)[:top_n]

def print_game_analysis(analyzed_games, player_name):
    """
    Print analysis results showing only the specified player's moves.
    """
    for i, game in enumerate(analyzed_games, start=1):
        print(f"\nGame {i}:")
        print(f"Link: {game['url']}")
        print(f"Played on: {game['end_time_utc']}")
        print(f"{player_name}'s color: {game['player_color']}")
        
        print(f"\n{player_name}'s longest thinks:")
        if game["player_top_thinks"]:
            for j, think in enumerate(game["player_top_thinks"], 1):
                print(f"{j}. Move {think['move_number']} {think['move']} "
                      f"({think['time_spent_formatted']})")
        else:
            print("No moves recorded")
        
        print("-" * 50)



# Modified output format
def print_game_analysis(analyzed_games, player_name):
    """
    Print analysis results showing only the specified player's moves.
    """
    for i, game in enumerate(analyzed_games, start=1):
        print(f"\nGame {i}:")
        print(f"Link: {game['url']}")
        print(f"Played on: {game['end_time_utc']}")
        print(f"{player_name}'s color: {game['player_color']}")
        
        print(f"\n{player_name}'s longest thinks:")
        if game["player_top_thinks"]:
            for j, think in enumerate(game["player_top_thinks"], 1):
                print(f"{j}. Move {think['move_number']} {think['move']} "
                      f"({think['time_spent_formatted']})")
        else:
            print("No moves recorded")
        
        print("-" * 50)


# Load JSON file
games_json_path = "chess_stats/stats_app/data/Kalel1130.json"

with open(games_json_path, 'r') as f:
    games_data = json.load(f)  # Load JSON data into a Python list

# Process Games (change the number here to process more games)
num_games_to_process = 50  # or any number you want
analyzed_games = process_chess_data(games_data, player_name=player, num_games=num_games_to_process)

# Print the analysis with the new format
print_game_analysis(analyzed_games, player)