import re
import json
import chess
import chess.svg
import chess.pgn
import io
import os
from datetime import datetime
from stockfish import Stockfish

def determine_player_color(game_data, player_name):
    """
    Determine player's color from game data with validation checks.
    
    Args:
        game_data (dict): The full game data including white/black player info
        player_name (str): The player's username to check
    
    Returns:
        bool: True if player is white, False if black
        str: Error message if there's an issue, None otherwise
    """
    # First check if we have both white and black player data
    if not game_data.get('white') or not game_data.get('black'):
        return None, "Missing player data in game"
        
    white_player = game_data['white'].get('username', '')
    black_player = game_data['black'].get('username', '')
    
    # Validate we have both usernames
    if not white_player or not black_player:
        return None, "Missing username in player data"
    
    # Double-check the player is actually in the game
    if player_name not in [white_player, black_player]:
        return None, f"Player {player_name} not found in game"
    
    # Determine color
    is_white = (white_player == player_name)
    
    # Log the determination for verification
    print(f"Color determination for game:")
    print(f"White player: {white_player}")
    print(f"Black player: {black_player}")
    print(f"Target player: {player_name}")
    print(f"Determined color: {'White' if is_white else 'Black'}")
    
    return is_white, None


class ErrorTracker:
    def __init__(self):
        self.error_count = 0
        self.errors = []
    
    def log_error(self, error_type, message, move_number=None, position=None):
        self.error_count += 1
        error_info = {
            'error_number': self.error_count,
            'error_type': error_type,
            'message': message,
            'move_number': move_number,
            'position': position
        }
        self.errors.append(error_info)
        print(f"Error #{self.error_count} at move {move_number}: {error_type} - {message}")
    
    def summary(self):
        print(f"\nError Summary:")
        print(f"Total errors: {self.error_count}")
        if self.errors:
            print("\nDetailed error list:")
            for error in self.errors:
                print(f"\nError #{error['error_number']}")
                print(f"Type: {error['error_type']}")
                print(f"Move: {error['move_number']}")
                print(f"Message: {error['message']}")
                if error['position']:
                    print(f"Position: {error['position']}")


def create_analysis_text(analysis_result, board):
    """Create analysis text showing evaluation and best moves."""
    # Create evaluation text
    eval_text = analysis_result['current_eval']
    if isinstance(eval_text, (int, float)):
        eval_text = f"{eval_text:+.2f}"
    
    analysis_text = f"Current evaluation: {eval_text}\n"
    analysis_text += "Top 3 moves:\n"
    
    # Add each best move with its score
    for i, move in enumerate(analysis_result['best_moves'], 1):
        # Handle centipawn or mate scores
        if 'Centipawn' in move:
            score = f"{move['Centipawn']/100:+.2f}"
        elif 'Mate' in move:
            score = f"M{move['Mate']}"
        else:
            score = "?"
            
        # Convert UCI move to SAN notation
        try:
            san_move = board.san(chess.Move.from_uci(move['Move']))
            analysis_text += f"{i}. {san_move} (Score: {score})\n"
        except:
            analysis_text += f"{i}. {move['Move']} (Score: {score})\n"
    
    return analysis_text


def eval_to_float(eval_dict):
    """
    Convert Stockfish evaluation to a consistent float representation.
    Handle None values gracefully.
    """
    # Handle None or invalid input
    if eval_dict is None or not isinstance(eval_dict, dict):
        print("Warning: Invalid evaluation dictionary")
        return 0.0
    
    try:
        # Check for mate evaluation
        if eval_dict.get('type') == 'mate':
            mate_score = eval_dict.get('value', 0)
            return f"M{mate_score}" if mate_score > 0 else f"-M{abs(mate_score)}"
        
        # Handle centipawn evaluation
        value = eval_dict.get('value')
        if value is None:
            print("Warning: No evaluation value found")
            return 0.0
            
        return float(value) / 100.0
        
    except Exception as e:
        print(f"Warning: Error in evaluation conversion: {e}")
        return 0.0


def initialize_stockfish():
    """Initialize Stockfish with optimal settings."""
    stockfish = Stockfish(path="/usr/games/stockfish")
    stockfish.set_depth(20)
    stockfish.set_skill_level(20)
    stockfish.update_engine_parameters({
        "Hash": 128,
        "Threads": 4,
        "Minimum Thinking Time": 100
    })
    return stockfish

def analyze_position(board, stockfish, player_is_white):
    """
    Analyze a position using Stockfish and return the best moves.
    Added null checking and error handling.
    """
    if board is None:
        print("Warning: Invalid board position")
        return {
            'current_eval': 0.0,
            'best_moves': [],
            'player_to_move': False
        }

    try:
        # Set position in Stockfish
        stockfish.set_position([m.uci() for m in board.move_stack])
        
        # Get evaluation with error handling
        try:
            current_eval = stockfish.get_evaluation()
            if current_eval is None:
                print("Warning: Stockfish returned None evaluation")
                current_eval = {'type': 'cp', 'value': 0}
        except Exception as e:
            print(f"Error getting evaluation: {e}")
            current_eval = {'type': 'cp', 'value': 0}
            
        # Convert evaluation safely
        current_eval_float = eval_to_float(current_eval)
        
        # Get best moves with error handling
        try:
            best_moves = stockfish.get_top_moves(3)
            if not best_moves:
                print("Warning: No best moves received")
                best_moves = []
        except Exception as e:
            print(f"Error getting best moves: {e}")
            best_moves = []
            
        return {
            'current_eval': current_eval_float,
            'best_moves': best_moves,
            'player_to_move': player_is_white == board.turn
        }
        
    except Exception as e:
        print(f"Unexpected error in analysis: {e}")
        return {
            'current_eval': 0.0,
            'best_moves': [],
            'player_to_move': player_is_white == board.turn
        }

def save_analyzed_position(board, filepath_base, is_white, analysis_result):
    """Save board position and best move visualization."""
    output_dir = 'chess_positions'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    current_pos_path = os.path.join(output_dir, filepath_base + "_current.svg")
    best_move_path = os.path.join(output_dir, filepath_base + "_best_move.svg")
    
    # Get best move
    if not analysis_result['best_moves']:
        print(f"No best moves found for position")
        return None, None, "No analysis available"
        
    best_move = chess.Move.from_uci(analysis_result['best_moves'][0]['Move'])
    
    # Save current position (no arrow)
    svg_content = chess.svg.board(
        board=board,
        size=400,
        coordinates=True,
        orientation=chess.WHITE if is_white else chess.BLACK
    )
    with open(current_pos_path, 'w') as f:
        f.write(svg_content)
    
    # Save position with best move arrow
    svg_content = chess.svg.board(
        board=board,
        size=400,
        coordinates=True,
        orientation=chess.WHITE if is_white else chess.BLACK,
        arrows=[chess.svg.Arrow(best_move.from_square, best_move.to_square, color="blue")]
    )
    with open(best_move_path, 'w') as f:
        f.write(svg_content)
    
    return current_pos_path, best_move_path, create_analysis_text(analysis_result, board)

# Global variables
PLAYER = "Kalel1130"
GAMES_JSON_PATH = "chess_stats/stats_app/data/Kalel1130.json"

def clock_to_seconds(clock):
    """Convert clock time format (H:MM:SS.s) to seconds with improved precision."""
    try:
        parts = clock.split(':')
        if len(parts) == 3:  # H:MM:SS
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:  # MM:SS
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        else:
            print(f"Warning: Invalid clock format: {clock}")
            return 0
    except Exception as e:
        print(f"Error converting clock time {clock}: {e}")
        return 0

def format_time_spent(seconds):
    """Convert seconds to human-readable time string."""
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
    if remaining_seconds > 0 and not days:
        parts.append(f"{remaining_seconds} {'second' if remaining_seconds == 1 else 'seconds'}")
    
    return " ".join(parts) if parts else "less than 1 second"

def convert_timestamp(unix_time):
    """Convert Unix timestamp to readable datetime string."""
    return datetime.fromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M:%S')

def convert_time_control(time_control_str):
    """Convert time control string to seconds."""
    try:
        return int(time_control_str)
    except ValueError:
        try:
            numerator, denominator = map(int, time_control_str.split('/'))
            return int(numerator * (86400 / denominator))
        except (ValueError, ZeroDivisionError):
            print(f"Warning: Invalid time control format: {time_control_str}")
            return 600

def get_position_from_pgn(pgn_str, move_number, player_is_white):
    """Get board position before the specified move."""
    try:
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        if not game:
            print("Warning: Could not read game from PGN")
            return None
        
        board = game.board()
        current_move = 0

        print("move_number: ", move_number)
        
        # For Black's moves, we need the position after White's move
        target_move = move_number * 2 - (2 if player_is_white else 1)
        
        for move in game.mainline_moves():
            if current_move >= target_move:
                break
            board.push(move)
            current_move += 1
                
        return board
    except Exception as e:
        print(f"Error processing move {move_number}: {e}")
        return None

def save_board_svg(board, filepath, is_white):
    """Save board position as SVG file."""
    output_dir = 'chess_positions'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    full_filepath = os.path.join(output_dir, filepath)
    
    svg_content = chess.svg.board(
        board=board,
        size=400,
        coordinates=True,
        orientation=chess.WHITE if is_white else chess.BLACK  # Set orientation based on player's color
    )
    
    with open(full_filepath, 'w') as f:
        f.write(svg_content)
    
    abs_path = os.path.abspath(full_filepath)
    print(f"Saved position to: {abs_path}")
    return abs_path

def find_top_thinks(moves, top_n=3):
    """Find moves where player spent the most time thinking."""
    thinks = []
    
    # print("\nDebug - All thinks:")
    for move_data in moves:
        move_str, move, clock, time_spent = move_data
        # Extract move number from move string (handles both white and black moves)
        move_number = move_str.split('.')[0]
        
        think = {
            'move_number': move_number,
            'move': move,
            'clock': clock,
            'time_spent': time_spent,
            'time_spent_formatted': format_time_spent(time_spent)
        }
        thinks.append(think)
        # print(f"Move {move_number} {move}: {format_time_spent(time_spent)}")
    
    sorted_thinks = sorted(thinks, key=lambda x: x['time_spent'], reverse=True)[:top_n]
    
    print("\nTop thinks selected:")
    for think in sorted_thinks:
        print(f"Move {think['move_number']} {think['move']}: {think['time_spent_formatted']}")
    
    return sorted_thinks

def process_moves(moves_str, player_is_white, time_control):
    """Process moves string to extract moves and calculate time spent."""
    # Updated pattern to handle all move types including castling
    move_pattern = re.compile(
        r'(\d+)\.\s+'                           # Move number
        r'([a-zA-Z0-9#+=O-]+)\s+'               # White's move (including O-O and O-O-O)
        r'\{[^}]*?clk\s+([0-9:\.]+)[^}]*?\}'   # White's clock
        r'(?:\s*(?:1-0|0-1|1/2-1/2))?'         # Optional result
        r'(?:\s*\d+\.\.\.)?\s*'                 # Optional black's move number
        r'([a-zA-Z0-9#+=O-]+)?\s*'              # Optional Black's move
        r'(?:\{[^}]*?clk\s+([0-9:\.]+)[^}]*?\})?'  # Optional Black's clock
    )
    
    player_moves = []
    prev_time = None
    
    # print("\nDebug clock times:")
    for match in move_pattern.finditer(moves_str):
        move_num = match.group(1)
        white_move = match.group(2)
        white_clock = match.group(3)
        black_move = match.group(4)
        black_clock = match.group(5)
        
        # Debug raw match data
        # print(f"\nRaw move {move_num}:")
        # print(f"  White: {white_move} {white_clock}")
        # print(f"  Black: {black_move} {black_clock}")
        
        # Convert clock times to seconds
        white_time = clock_to_seconds(white_clock)
        black_time = clock_to_seconds(black_clock) if black_clock else None
        
        # Debug converted times
        if black_clock:
            print(f"Move {move_num}: White clock: {white_clock} ({white_time}s), Black clock: {black_clock} ({black_time}s)")
        else:
            print(f"Move {move_num}: White clock: {white_clock} ({white_time}s), Black clock: N/A")
        
        if player_is_white:
            current_time = white_time
            move = white_move
            move_str = f"{move_num}. {move}"
        elif black_move and black_clock:
            current_time = black_time
            move = black_move
            move_str = f"{move_num}... {move}"
        else:
            continue
            
        # Calculate time spent
        if prev_time is not None:
            time_spent = prev_time - current_time
            if time_spent > 0:  # Only record positive time differences
                # print(f"Time spent on {move_str}: {time_spent:.1f}s")
                player_moves.append((move_str, move, current_time, time_spent))
        
        prev_time = current_time
    
    return player_moves


def process_chess_data(games_json, player_name, num_games=3):
    """Process chess games with improved analysis."""
    processed_games = []
    moves_pattern = re.compile(r'\n\n(1\..*)', re.DOTALL)
    error_tracker = ErrorTracker()
    
    stockfish = initialize_stockfish()

    for i, game in enumerate(games_json[:num_games]):
        print(f"\nProcessing game {i+1} of {num_games}...")
        
        # Determine player color with validation
        player_is_white, color_error = determine_player_color(game, player_name)
        if color_error:
            error_tracker.log_error("COLOR_DETERMINATION", color_error, None)
            continue
            
        pgn = game.get("pgn", "")
        if not pgn:
            error_tracker.log_error("PGN_MISSING", "No PGN found in game data", None)
            continue
            
        time_control = convert_time_control(game.get("time_control", "600"))
        end_time_utc = game.get("end_time", 0)
        readable_time_utc = convert_timestamp(end_time_utc)
        game_url = game.get("url", "No URL available")
        
        print(f"Game URL: {game_url}")
        print(f"Date: {readable_time_utc}")
        print(f"Playing as: {'White' if player_is_white else 'Black'}")
        
        moves_match = moves_pattern.search(pgn)
        if not moves_match:
            error_tracker.log_error("MOVES_PARSING", "Could not parse moves from PGN", None)
            continue
            
        moves = moves_match.group(1).strip()
        
        # print("\nAnalyzing longest thinks:")
        player_moves = process_moves(moves, player_is_white, time_control)
        player_top_thinks = find_top_thinks(player_moves)
        
        analyzed_thinks = []
        for think in player_top_thinks:
            try:
                move_number = int(think['move_number'])
                # print(f"  Analyzing think: Move {move_number} {think['move']} ({think['time_spent_formatted']})")
                
                board = get_position_from_pgn(pgn, move_number, player_is_white)
                if board:
                    analysis = analyze_position(board, stockfish, player_is_white)
                    
                    svg_filename = f"game_{i+1}_move_{move_number}"
                    current_pos, best_move_pos, analysis_text = save_analyzed_position(
                        board,
                        svg_filename,
                        player_is_white,
                        analysis
                    )
                    
                    think['position_file'] = current_pos
                    think['best_move_file'] = best_move_pos
                    think['analysis'] = analysis_text
                    think['evaluation'] = analysis['current_eval']
                    think['best_moves'] = analysis['best_moves']
                    analyzed_thinks.append(think)
                    
            except Exception as e:
                error_tracker.log_error("ANALYSIS_ERROR", str(e), move_number)
        
        processed_games.append({
            "pgn": pgn,
            "time_control": time_control,
            "end_time_utc": readable_time_utc,
            "url": game_url,
            "player_color": "White" if player_is_white else "Black",
            "player_top_thinks": analyzed_thinks,
        })

    error_tracker.summary()
    return processed_games


def print_game_analysis(analyzed_games, player_name):
    """Print analysis results with improved formatting."""
    for i, game in enumerate(analyzed_games, start=1):
        print(f"\nGame {i}:")
        print(f"Link: {game['url']}")
        print(f"Played on: {game['end_time_utc']}")
        print(f"{player_name}'s color: {game['player_color']}")
        
        print(f"\n{player_name}'s longest thinks:")
        if game["player_top_thinks"]:
            for j, think in enumerate(game["player_top_thinks"], 1):
                print(f"\n{j}. Move {think['move_number']} {think['move']} "
                      f"({think['time_spent_formatted']})")
                
                if 'analysis' in think:
                    print("\nStockfish Analysis:")
                    print(think['analysis'])
                    print(f"Current position: {think['position_file']}")
                    print(f"Best move visualization: {think['best_move_file']}")
                
        else:
            print("No moves recorded")
        
        print("-" * 50)


# Add this function near the end of chess_visu.py, before main()
def save_analyzed_games(analyzed_games, output_file='analyzed_games.json'):
    """Save analyzed games data to JSON with proper serialization."""
    try:
        # Convert analyzed games to serializable format
        serializable_games = []
        for game in analyzed_games:
            game_data = {
                "pgn": game["pgn"],
                "time_control": game["time_control"],
                "end_time_utc": game["end_time_utc"],
                "url": game["url"],
                "player_color": game["player_color"],
                "player_top_thinks": []
            }
            
            for think in game["player_top_thinks"]:
                think_data = {
                    "move_number": think["move_number"],
                    "move": think["move"],
                    "time_spent": think["time_spent"],
                    "time_spent_formatted": think["time_spent_formatted"],
                    "position_file": think["position_file"],
                    "best_move_file": think["best_move_file"],
                    "analysis": think["analysis"],
                    "evaluation": think["evaluation"],
                    "best_moves": think["best_moves"]
                }
                game_data["player_top_thinks"].append(think_data)
            
            serializable_games.append(game_data)
            
        # Save to file with proper encoding
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_games, f, indent=2, ensure_ascii=False)
        print(f"\nAnalyzed games data saved to {output_file}")
        
    except Exception as e:
        print(f"Error saving analyzed games data: {e}")
        raise


# Modify the main() function to save the analyzed games
def main():
    # Load games data
    try:
        with open(GAMES_JSON_PATH, 'r') as f:
            games_data = json.load(f)
    except Exception as e:
        print(f"Error loading games data: {e}")
        return

    # Process games from 15 to 50
    start_game = 16  # 0-based index for game 15
    end_game = 50
    analyzed_games = process_chess_data(games_data[start_game:end_game], PLAYER, num_games=end_game-start_game)
    print_game_analysis(analyzed_games, PLAYER)
    
    # Save analyzed games data
    save_analyzed_games(analyzed_games)

if __name__ == "__main__":
    main()