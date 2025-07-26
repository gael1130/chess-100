import re
import json
import chess
import chess.svg
import chess.pgn
import io
import os
from datetime import datetime

from stockfish import Stockfish

def eval_to_float(eval_dict):
    if eval_dict['type'] == 'mate':
        mate_score = eval_dict['value']
        # Convert mate scores to high numerical values
        if mate_score > 0:
            return f"M{mate_score}"
        else:
            return f"-M{abs(mate_score)}"
    return eval_dict['value'] / 100


def analyze_position(board, stockfish, player_is_white):
    """
    Analyze a position using Stockfish and return the best moves.
    
    Args:
        board (chess.Board): The board position to analyze
        stockfish (Stockfish): Initialized Stockfish instance
        player_is_white (bool): Whether the player is white
        
    Returns:
        dict: Analysis results including best moves and evaluations
    """
    stockfish.set_position([m.uci() for m in board.move_stack])
    current_eval = stockfish.get_evaluation()
    best_moves = stockfish.get_top_moves(3)  # Get top 3 moves
    
    return {
        'current_eval': eval_to_float(current_eval),
        'best_moves': best_moves,
        'player_to_move': player_is_white == board.turn
    }

def save_analyzed_position(board, filepath_base, is_white, analysis_result):
    """
    Save two SVG files: current position (no arrow) and position with best move arrow.
    
    Args:
        board (chess.Board): The current board position
        filepath_base (str): Base filepath for the SVG files
        is_white (bool): Whether to show board from white's perspective
        analysis_result (dict): Analysis results from Stockfish
    
    Returns:
        tuple: (current_pos_path, next_pos_path, analysis_text)
    """
    output_dir = 'chess_positions'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    current_pos_path = os.path.join(output_dir, filepath_base + "_current.svg")
    next_pos_path = os.path.join(output_dir, filepath_base + "_after_best.svg")
    
    # Get best move
    best_move = chess.Move.from_uci(analysis_result['best_moves'][0]['Move'])
    
    # Save current position without arrow
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
    with open(next_pos_path, 'w') as f:
        f.write(svg_content)
    
    # Create analysis text
    eval_text = analysis_result['current_eval']
    if isinstance(eval_text, (int, float)):
        eval_text = f"{eval_text:+.2f}"
    
    analysis_text = f"Current evaluation: {eval_text}\n"
    analysis_text += "Top 3 moves:\n"
    for i, move in enumerate(analysis_result['best_moves'], 1):
        analysis_text += f"{i}. {board.san(chess.Move.from_uci(move['Move']))} (Score: {move['Centipawn']/100 if 'Centipawn' in move else 'M'+str(move['Mate'])})\n"
    
    return current_pos_path, next_pos_path, analysis_text

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

def test_position_analysis():
    """Test the position analysis functions with a sample position."""
    # Create a test position
    board = chess.Board()
    moves = ["e2e4", "e7e5", "g1f3", "b8c6"]  # Sample opening moves
    for move in moves:
        board.push(chess.Move.from_uci(move))
    
    try:
        # Initialize Stockfish
        stockfish = initialize_stockfish()
        
        # Analyze position
        analysis = analyze_position(board, stockfish, True)  # Analyze from White's perspective
        
        # Save position with analysis
        current_pos, next_pos, analysis_text = save_analyzed_position(
            board,
            "test_position",
            True,
            analysis
        )
        
        print("Analysis complete!")
        print(f"Current position saved as: {current_pos}")
        print(f"Position after best move saved as: {next_pos}")
        print("\nAnalysis:")
        print(analysis_text)
        
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    test_position_analysis()