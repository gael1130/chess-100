import json
import chess.pgn
import io
from collections import Counter

def analyze_player_moves(games_json, username, max_games=100, moves_to_analyze=20, color='white', top_n=3):
   positions_by_move = [Counter() for _ in range(moves_to_analyze)]
   last_game_data = {}  # Store {move_number: {move: (url, pgn)}}
   games_analyzed = 0
   
   for game in games_json:
       # Check if player is playing the requested color
       if game[color]['username'].lower() != username.lower():
           continue
       
       pgn = io.StringIO(game['pgn'])
       chess_game = chess.pgn.read_game(pgn)
       if not chess_game:
           continue
           
       board = chess.Board()
       move_index = 0
       game_url = game['url']
       game_pgn = game['pgn']
       
       # Process moves one at a time
       for node in chess_game.mainline():
           if move_index >= moves_to_analyze:
               break
               
           if node.parent is None:
               continue
               
           # Record move if it's the player's turn based on color
           is_white_turn = board.turn == chess.WHITE
           if ((color == 'white' and is_white_turn) or 
               (color == 'black' and not is_white_turn)):
               san_move = board.san(node.move)
               positions_by_move[move_index][san_move] += 1
               
               if move_index not in last_game_data:
                   last_game_data[move_index] = {}
               last_game_data[move_index][san_move] = (game_url, game_pgn)
               
               move_index += 1
           
           # Update board state
           board.push(node.move)
               
       games_analyzed += 1
       if games_analyzed >= max_games:
           break
           
   print(f"\nAnalysis for {username} playing as {color.upper()}")
   print(f"Games analyzed: {games_analyzed}")
   
   for move_num, counter in enumerate(positions_by_move, 1):
       if not counter:
           break
       print("-" * 50)
       print(f"\nMove {move_num}:")
       total = sum(counter.values())
       if total > 0:
           for move, count in counter.most_common(top_n):
               percentage = (count / total) * 100
               url, pgn = last_game_data[move_num-1][move]
               print(f"{move}: {percentage:.1f}% - Last game: {url}")
            #    print("PGN:")
            #    print(pgn)
            #    print("-" * 50)

username = "Kalel1130"
with open('chess_stats/stats_app/data/Kalel1130.json', 'r') as f:
    games_data = json.load(f)


# Analyze white moves, showing top 3 most common moves
print("\n=== ANALYSIS AS WHITE ===")
analyze_player_moves(games_data, username, color='white', top_n=3)

print("\n=== ANALYSIS AS BLACK ===")
analyze_player_moves(games_data, username, color='black', top_n=3)