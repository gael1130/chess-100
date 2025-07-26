import chess
import chess.pgn
import chess.svg
import json
import io
import os
from datetime import datetime
from stockfish import Stockfish


def save_position_svg(board, move=None, filepath=None, is_white=True):
    """Save board position as SVG, optionally with a move arrow."""
    if not filepath:
        return None
        
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    arrows = []
    if move:
        try:
            move_obj = chess.Move.from_uci(move)
            arrows = [chess.svg.Arrow(move_obj.from_square, move_obj.to_square, color="green")]
        except:
            arrows = []
    
    svg_content = chess.svg.board(
        board=board,
        size=400,
        coordinates=True,
        orientation=chess.WHITE if is_white else chess.BLACK,
        arrows=arrows
    )
    
    with open(filepath, 'w') as f:
        f.write(svg_content)
    
    return filepath

# Import functions from your existing file
from chess_time_visu import (
    determine_player_color,
    convert_timestamp,
    PLAYER,
    GAMES_JSON_PATH
)

def analyze_mistake_with_visuals(mistake, game_data, player_is_white, game_number):
    """Analyze a mistake and generate visual aids."""
    game = chess.pgn.read_game(io.StringIO(game_data['pgn']))
    board = game.board()
    
    # Replay moves up to the mistake position
    for move in game.mainline_moves():
        if board.fen() == mistake['position_before']:
            break
        board.push(move)
    
    # Convert UCI to SAN for readability
    move_played = chess.Move.from_uci(mistake['move_played'])
    move_san = board.san(move_played)
    
    # Create base filename for this mistake
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_dir = "chess_mistakes"
    base_filename = f"{base_dir}/game_{game_number}_move_{mistake['move_number']}_{timestamp}"
    
    # Save position before mistake
    position_file = save_position_svg(
        board,
        filepath=f"{base_filename}_position.svg",
        is_white=player_is_white
    )
    
    # Save position with best move arrow
    best_move_file = None
    if mistake['best_moves']:
        best_move = mistake['best_moves'][0]['Move']
        best_move_file = save_position_svg(
            board,
            move=best_move,
            filepath=f"{base_filename}_best_move.svg",
            is_white=player_is_white
        )
    
    # Create analysis dictionary
    analysis = {
        'game_url': game_data['url'],
        'move_number': mistake['move_number'],
        'player_color': 'White' if player_is_white else 'Black',
        'move_played': move_san,  # The actual move played in the game
        'position_before': format_eval(mistake['eval_before']),
        'position_after': format_eval(mistake['eval_after']),
        'position_loss': f"{mistake['eval_diff']:.2f}",
        'position_svg': position_file,
        'better_moves': [],
        'best_move_svg': best_move_file
    }
    
    # Add better moves
    if mistake['best_moves']:
        for move in mistake['best_moves']:
            try:
                best_move = chess.Move.from_uci(move['Move'])
                best_move_san = board.san(best_move)
                score = move.get('Centipawn', 0)
                if score is not None:
                    score = score / 100
                analysis['better_moves'].append({
                    'move': best_move_san,
                    'score': format_eval(score)
                })
            except Exception as e:
                continue
    
    return analysis

def initialize_stockfish(quick_mode=True):
    """Initialize stockfish with configurable parameters."""
    stockfish = Stockfish()
    
    if quick_mode:
        # Faster analysis settings
        stockfish.set_depth(10)  # Lower depth for quicker analysis
        stockfish.set_skill_level(10)  # Lower skill level
        stockfish.update_engine_parameters({
            "Threads": 1,  # Use fewer threads
            "Minimum Thinking Time": 20,  # Minimum time in ms
            "Move Overhead": 20,  # Shorter move overhead
            "Slow Mover": 50  # Faster time management
        })
    else:
        # More thorough analysis settings
        stockfish.set_depth(15)
        stockfish.set_skill_level(20)
        stockfish.update_engine_parameters({
            "Threads": 2,
            "Minimum Thinking Time": 50,
            "Move Overhead": 30,
            "Slow Mover": 80
        })
    
    return stockfish

def get_eval_difference(eval_before, eval_after):
    """Calculate the difference between two evaluations."""
    def eval_to_float(eval_dict):
        if eval_dict['type'] == 'mate':
            mate_score = eval_dict['value']
            return 100000 if mate_score > 0 else -100000
        return eval_dict['value'] / 100.0
    
    score_before = eval_to_float(eval_before)
    score_after = eval_to_float(eval_after)
    
    return score_after - score_before

def format_eval(eval_data):
    """Format evaluation data into a readable string."""
    if isinstance(eval_data, dict):
        if eval_data['type'] == 'mate':
            if eval_data['value'] is not None:
                return f"M{eval_data['value']}"
            return "M?"
        elif eval_data['type'] == 'cp':
            if eval_data['value'] is not None:
                return f"{eval_data['value']/100:+.2f}"
            return "+0.00"
    return f"{eval_data:+.2f}" if eval_data is not None else "+0.00"

def find_mistakes(pgn_str, player_is_white, stockfish, num_mistakes=3, quick_mode=True):
    """Analyze a game to find the biggest mistakes."""
    game = chess.pgn.read_game(io.StringIO(pgn_str))
    if not game:
        return []
        
    board = game.board()
    mistakes = []
    current_move = 0
    move_history = []
    
    mistake_threshold = -0.8 if not quick_mode else -1.2
    top_moves_count = 2 if quick_mode else 3
    
    for move in game.mainline_moves():
        current_move += 1
        is_player_move = (board.turn == chess.WHITE) == player_is_white
        
        if is_player_move:
            current_position = board.fen()
            current_move_stack = [m.uci() for m in board.move_stack]
            
            stockfish.set_position(current_move_stack)
            eval_before = stockfish.get_evaluation()
            best_moves = stockfish.get_top_moves(top_moves_count)
            
            board.push(move)
            move_history.append(move.uci())
            
            stockfish.set_position([m.uci() for m in board.move_stack])
            eval_after = stockfish.get_evaluation()
            
            eval_diff = get_eval_difference(eval_before, eval_after)
            if not player_is_white:
                eval_diff = -eval_diff
            
            if eval_diff <= mistake_threshold:
                mistake_info = {
                    'move_number': (current_move + 1) // 2,
                    'position_before': current_position,
                    'move_played': move.uci(),
                    'eval_before': eval_before,
                    'eval_after': eval_after,
                    'eval_diff': eval_diff,
                    'best_moves': best_moves
                }
                mistakes.append(mistake_info)
        else:
            board.push(move)
            move_history.append(move.uci())
    
    return sorted(mistakes, key=lambda x: x['eval_diff'])[:num_mistakes]

def print_mistake_analysis(mistake, game):
    """Print detailed analysis of a single mistake."""
    board = game.board()
    
    # Replay moves up to the mistake position
    for move in game.mainline_moves():
        if board.fen() == mistake['position_before']:
            break
        board.push(move)
    
    move_played = chess.Move.from_uci(mistake['move_played'])
    move_san = board.san(move_played)
    
    print(f"\nMistake at move {mistake['move_number']}:")
    print(f"Played move: {move_san}")
    print(f"Position evaluation before: {format_eval(mistake['eval_before'])}")
    print(f"Position evaluation after: {format_eval(mistake['eval_after'])}")
    print(f"Position loss: {mistake['eval_diff']:.2f}")
    
    if mistake['best_moves']:
        print("\nBetter moves were:")
        for i, move in enumerate(mistake['best_moves'], 1):
            try:
                best_move = chess.Move.from_uci(move['Move'])
                best_move_san = board.san(best_move)
                score = move.get('Centipawn', 0)
                if score is not None:
                    score = score / 100
                print(f"{i}. {best_move_san} (Score: {format_eval(score)})")
            except Exception as e:
                continue

def main():
    quick_mode = True
    print(f"Running analysis in {'quick' if quick_mode else 'thorough'} mode...")
    
    stockfish = initialize_stockfish(quick_mode=quick_mode)
    
    with open(GAMES_JSON_PATH, 'r') as f:
        games_data = json.load(f)
    
    all_analyses = []
    
    for game_number, game_data in enumerate(games_data[:50], 1):  # Analyze games 1 to 50
        print("\n" + "="*50)
        print(f"Analyzing game: {game_data['url']}")
        
        player_is_white, _ = determine_player_color(game_data, PLAYER)
        color = "White" if player_is_white else "Black"
        print(f"Player played as: {color}")
        
        game = chess.pgn.read_game(io.StringIO(game_data['pgn']))
        if not game:
            continue
            
        mistakes = find_mistakes(game_data['pgn'], player_is_white, stockfish, 
                               quick_mode=quick_mode)
        
        if not mistakes:
            print("No significant mistakes found in this game!")
            continue
            
        print(f"\nFound {len(mistakes)} significant mistakes:")
        game_analyses = []
        
        for mistake in mistakes:
            # Print analysis to console
            print_mistake_analysis(mistake, game)
            print("-" * 30)
            
            # Generate visual analysis and save to file
            analysis = analyze_mistake_with_visuals(
                mistake, 
                game_data, 
                player_is_white,
                game_number
            )
            game_analyses.append(analysis)
        
        all_analyses.extend(game_analyses)
    
    # Save all analyses to JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"chess_mistakes/analyzed_mistakes_{timestamp}.json"
    os.makedirs(os.path.dirname(json_filename), exist_ok=True)
    
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(all_analyses, f, indent=2, ensure_ascii=False)
    
    print(f"\nAnalyses saved to {json_filename}")

if __name__ == "__main__":
    main()