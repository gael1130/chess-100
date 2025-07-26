import chess
import chess.pgn
import io
import json
from stockfish import Stockfish


kalel_games_path="chess_stats/stats_app/data/Kalel1130.json"

def eval_to_float(eval_dict):
    if eval_dict['type'] == 'mate':
        mate_score = eval_dict['value']
        # Convert mate scores to high numerical values
        if mate_score > 0:
            return f"M{mate_score}"
        else:
            return f"-M{abs(mate_score)}"
    return eval_dict['value'] / 100


def analyze_game(pgn_str, stockfish_depth=20):
    stockfish = Stockfish(path="/usr/games/stockfish")
    stockfish.set_depth(stockfish_depth)
    stockfish.set_skill_level(20)  # Add this to match chess.com's strength
    stockfish.update_engine_parameters({
        "Hash": 128,  # MB for hash table
        "Threads": 4,  # Number of CPU threads to use
        "Minimum Thinking Time": 100  # ms
    })
    
    game = chess.pgn.read_game(io.StringIO(pgn_str))
    board = game.board()
    white_moves = []
    black_moves = []

    for move in game.mainline_moves():
        stockfish.set_position([m.uci() for m in board.move_stack])
        prev_eval = stockfish.get_evaluation()
        prev_score = eval_to_float(prev_eval)
        
        move_san = board.san(move)
        is_white = board.turn == chess.WHITE
        board.push(move)
        
        stockfish.set_position([m.uci() for m in board.move_stack])
        new_eval = stockfish.get_evaluation()
        new_score = eval_to_float(new_eval)
        
        eval_diff = calculate_eval_diff(prev_eval, new_eval, is_white)
            
        move_info = {
            'move': move_san,
            'eval_diff': eval_diff,
            'position': board.fen(),
            'move_number': len(board.move_stack) // 2 + 1,
            'prev_eval': prev_score,
            'new_eval': new_score
        }
        
        if is_white:
            white_moves.append(move_info)
        else:
            black_moves.append(move_info)
    
    # Get best and worst moves for each color
    white_best = sorted(white_moves, key=lambda x: float(x['eval_diff']) if isinstance(x['eval_diff'], (int, float)) else -10000, reverse=True)[:3]
    white_worst = sorted(white_moves, key=lambda x: float(x['eval_diff']) if isinstance(x['eval_diff'], (int, float)) else 10000)[:3]
    black_best = sorted(black_moves, key=lambda x: float(x['eval_diff']) if isinstance(x['eval_diff'], (int, float)) else -10000, reverse=True)[:3]
    black_worst = sorted(black_moves, key=lambda x: float(x['eval_diff']) if isinstance(x['eval_diff'], (int, float)) else 10000)[:3]
    
    return white_best, white_worst, black_best, black_worst

def calculate_eval_diff(prev_eval, new_eval, is_white):
    prev_score = eval_to_float(prev_eval)
    new_score = eval_to_float(new_eval)
    
    # If either score involves mate
    if isinstance(prev_score, str) or isinstance(new_score, str):
        return new_score
    
    # Regular evaluation difference
    diff = new_score - prev_score
    if not is_white:
        diff = -diff
    return diff

# Parse your JSON and analyze each game
with open(kalel_games_path, 'r') as f:
    games_data = json.load(f)


for game in games_data:
    print(f"\nAnalyzing game: {game['url']}")
    try:
        white_best, white_worst, black_best, black_worst = analyze_game(game['pgn'])
        
        print("\nWhite's best moves:")
        for i, move in enumerate(white_best, 1):
            eval_text = move['eval_diff']
            if isinstance(eval_text, (int, float)):
                eval_text = f"{eval_text:+.2f}"
            prev_eval = move['prev_eval'] if isinstance(move['prev_eval'], str) else f"{move['prev_eval']:+.2f}"
            new_eval = move['new_eval'] if isinstance(move['new_eval'], str) else f"{move['new_eval']:+.2f}"
            print(f"{i}. Move {move['move_number']}: {move['move']} "
                  f"(Before: {prev_eval}, After: {new_eval}, Change: {eval_text})")
        
        print("\nWhite's worst moves:")
        for i, move in enumerate(white_worst, 1):
            eval_text = move['eval_diff']
            if isinstance(eval_text, (int, float)):
                eval_text = f"{eval_text:+.2f}"
            prev_eval = move['prev_eval'] if isinstance(move['prev_eval'], str) else f"{move['prev_eval']:+.2f}"
            new_eval = move['new_eval'] if isinstance(move['new_eval'], str) else f"{move['new_eval']:+.2f}"
            print(f"{i}. Move {move['move_number']}: {move['move']} "
                  f"(Before: {prev_eval}, After: {new_eval}, Change: {eval_text})")
            
        print("\nBlack's best moves:")
        for i, move in enumerate(black_best, 1):
            eval_text = move['eval_diff']
            if isinstance(eval_text, (int, float)):
                eval_text = f"{eval_text:+.2f}"
            prev_eval = move['prev_eval'] if isinstance(move['prev_eval'], str) else f"{move['prev_eval']:+.2f}"
            new_eval = move['new_eval'] if isinstance(move['new_eval'], str) else f"{move['new_eval']:+.2f}"
            print(f"{i}. Move {move['move_number']}: {move['move']} "
                  f"(Before: {prev_eval}, After: {new_eval}, Change: {eval_text})")
            
        print("\nBlack's worst moves:")
        for i, move in enumerate(black_worst, 1):
            eval_text = move['eval_diff']
            if isinstance(eval_text, (int, float)):
                eval_text = f"{eval_text:+.2f}"
            prev_eval = move['prev_eval'] if isinstance(move['prev_eval'], str) else f"{move['prev_eval']:+.2f}"
            new_eval = move['new_eval'] if isinstance(move['new_eval'], str) else f"{move['new_eval']:+.2f}"
            print(f"{i}. Move {move['move_number']}: {move['move']} "
                  f"(Before: {prev_eval}, After: {new_eval}, Change: {eval_text})")
            
    except Exception as e:
        print(f"Error analyzing game: {str(e)}")