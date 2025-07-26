import json
import datetime
from typing import List, Dict, Any
import difflib
import re


filename = "chess_stats/stats_app/data/Kalel1130.json"


class ChessGameAnalyzer:
    def __init__(self, filename: str = filename):
        self.filename = filename
        self.games = self.load_games()

    def load_games(self) -> List[Dict[str, Any]]:
        """Load games from JSON file, create if doesn't exist."""
        try:
            with open(self.filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def save_games(self):
        """Save games to JSON file."""
        with open(self.filename, 'w') as f:
            json.dump(self.games, f, indent=2)

    def add_games(self, new_games: List[Dict[str, Any]]):
        """Add new games to the database, avoiding duplicates."""
        existing_urls = {game['url'] for game in self.games}
        for game in new_games:
            if game['url'] not in existing_urls:
                self.games.append(game)
        self.save_games()

    def get_player_accuracy(self, game: Dict[str, Any]) -> float:
        """Safely get player's accuracy from a game."""
        try:
            is_white = game['white']['username'].lower() == 'kalel1130'
            return game['accuracies']['white' if is_white else 'black']
        except (KeyError, TypeError):
            return None

    def get_player_result(self, game: Dict[str, Any]) -> str:
        """Safely get player's result from a game."""
        try:
            if game['white']['username'].lower() == 'kalel1130':
                return game['white'].get('result', '')
            else:
                return game['black'].get('result', '')
        except KeyError:
            return ''

    def get_player_elo(self, game: Dict[str, Any]) -> int:
        """Safely get player's ELO from a game."""
        try:
            if game['white']['username'].lower() == 'kalel1130':
                return game['white'].get('rating', 0)
            else:
                return game['black'].get('rating', 0)
        except KeyError:
            return 0

    def filter_games(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Filter games based on multiple criteria.
        
        Supported filters:
        - min_date, max_date (str): Date range in YYYY.MM.DD format
        - min_accuracy, max_accuracy (float): Accuracy range
        - result (str): 'win', 'loss', or 'draw'
        - min_elo, max_elo (int): Player's ELO range
        - min_opponent_elo, max_opponent_elo (int): Opponent's ELO range
        """
        filtered_games = self.games.copy()
        
        for game in filtered_games:
            # Convert date string to datetime object for comparison
            game['datetime'] = datetime.datetime.fromtimestamp(game['end_time'])

        if 'min_date' in kwargs:
            min_date = datetime.datetime.strptime(kwargs['min_date'], '%Y.%m.%d')
            filtered_games = [g for g in filtered_games if g['datetime'] >= min_date]
            
        if 'max_date' in kwargs:
            max_date = datetime.datetime.strptime(kwargs['max_date'], '%Y.%m.%d')
            filtered_games = [g for g in filtered_games if g['datetime'] <= max_date]

        if 'min_accuracy' in kwargs:
            filtered_games = [g for g in filtered_games 
                            if (accuracy := self.get_player_accuracy(g)) is not None 
                            and accuracy >= kwargs['min_accuracy']]

        if 'max_accuracy' in kwargs:
            filtered_games = [g for g in filtered_games 
                            if (accuracy := self.get_player_accuracy(g)) is not None 
                            and accuracy <= kwargs['max_accuracy']]

        if 'result' in kwargs:
            filtered_games = [g for g in filtered_games 
                            if self.get_player_result(g) == kwargs['result']]

        if 'min_elo' in kwargs:
            filtered_games = [g for g in filtered_games 
                            if self.get_player_elo(g) >= kwargs['min_elo']]

        if 'max_elo' in kwargs:
            filtered_games = [g for g in filtered_games 
                            if self.get_player_elo(g) <= kwargs['max_elo']]

        return filtered_games

    def find_similar_games(self, game_url: str, min_similarity: float = 0.6) -> List[Dict[str, Any]]:
        """
        Find games with similar move patterns using TCN (compressed move notation).
        Returns games with move similarity above the threshold.
        """
        target_game = next((g for g in self.games if g['url'] == game_url), None)
        if not target_game:
            return []

        similar_games = []
        target_tcn = target_game.get('tcn', '')
        if not target_tcn:
            return []

        for game in self.games:
            if game['url'] != game_url and 'tcn' in game:
                similarity = difflib.SequenceMatcher(None, target_tcn, game['tcn']).ratio()
                if similarity >= min_similarity:
                    game['similarity'] = similarity
                    similar_games.append(game)

        return sorted(similar_games, key=lambda x: x['similarity'], reverse=True)

    def get_statistics(self) -> Dict[str, Any]:
        """Calculate overall statistics for the player."""
        stats = {
            'total_games': len(self.games),
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'avg_accuracy': 0,
            'avg_game_length': 0,
            'favorite_openings': {},
            'elo_history': []
        }

        total_accuracy = 0
        games_with_accuracy = 0
        total_moves = 0

        for game in self.games:
            # Count results
            result = self.get_player_result(game)
            if result == 'win':
                stats['wins'] += 1
            elif result in ['timeout', 'checkmated', 'resigned']:
                stats['losses'] += 1
            else:
                stats['draws'] += 1

            # Add ELO to history
            elo = self.get_player_elo(game)
            if elo:
                stats['elo_history'].append((game['end_time'], elo))

            # Add accuracy if available
            accuracy = self.get_player_accuracy(game)
            if accuracy is not None:
                total_accuracy += accuracy
                games_with_accuracy += 1

            # Count openings
            if 'eco' in game:
                opening = game['eco'].split('/')[-1]
                stats['favorite_openings'][opening] = stats['favorite_openings'].get(opening, 0) + 1

            # Count moves from PGN if available
            if 'pgn' in game:
                moves = len(game['pgn'].split('\n\n')[1].split())
                total_moves += moves

        stats['avg_accuracy'] = total_accuracy / games_with_accuracy if games_with_accuracy else 0
        stats['avg_game_length'] = total_moves / len(self.games) if self.games else 0
        stats['favorite_openings'] = dict(sorted(stats['favorite_openings'].items(), 
                                               key=lambda x: x[1], 
                                               reverse=True)[:5])
        stats['elo_history'].sort()

        return stats
    
    def printo():
        print("hello")
        return "hello"
    
    def convert_clock_to_seconds(self, time_str: str) -> float:
        """Convert clock string (h:mm:ss.d) to seconds"""
        parts = time_str.split(':')
        minutes = int(parts[0])
        seconds = float(parts[1])
        return minutes * 60 + seconds

    def get_move_timing_analysis(self, game: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze the time spent on each move in a game by parsing PGN clock annotations.
        Returns list of moves with timing information, sorted by time spent.
        """
        try:
            is_white = game['white']['username'].lower() == 'kalel1130'
            move_times = []
            
            if 'pgn' not in game:
                return []
                
            # Extract the moves section from PGN
            pgn_parts = game['pgn'].split('\n\n')
            if len(pgn_parts) < 2:
                return []
            
            moves_text = pgn_parts[1]
            print("DEBUG: Found moves text:", moves_text[:200])
            
            # Updated regex pattern to exactly match the PGN format
            move_pattern = r'(\d+)\. ([^\{]+)\{?\[%clk (\d+:\d+\.\d+)\]\}(?:\s+([^\{]+)\{?\[%clk (\d+:\d+\.\d+)\]\})?'
            matches = list(re.finditer(move_pattern, moves_text))
            print(f"DEBUG: Found {len(matches)} moves matching pattern")
            
            # Process first move differently to establish initial time
            if matches:
                initial_white_time = self.convert_clock_to_seconds(matches[0].group(3))
                initial_black_time = self.convert_clock_to_seconds(matches[0].group(5)) if matches[0].group(5) else initial_white_time
                last_white_time = initial_white_time
                last_black_time = initial_black_time
                
                # Skip first move in the loop since we don't have a previous time to compare to
                for match in matches[1:]:
                    move_num = int(match.group(1))
                    white_move = match.group(2).strip()
                    white_clock = match.group(3)
                    
                    # Convert clock to seconds
                    white_time = self.convert_clock_to_seconds(white_clock)
                    
                    # Calculate time spent by White
                    white_spent = last_white_time - white_time
                    last_white_time = white_time
                    
                    if is_white and white_spent > 0:
                        move_times.append({
                            'move_number': move_num,
                            'time_spent': white_spent,
                            'move': white_move,
                            'remaining_time': white_time,
                            'color': 'White'
                        })
                    
                    # Process Black's move if it exists
                    if match.group(4):
                        black_move = match.group(4).strip()
                        black_clock = match.group(5)
                        black_time = self.convert_clock_to_seconds(black_clock)
                        
                        # Calculate time spent by Black
                        black_spent = last_black_time - black_time
                        last_black_time = black_time
                        
                        if not is_white and black_spent > 0:
                            move_times.append({
                                'move_number': move_num,
                                'time_spent': black_spent,
                                'move': black_move,
                                'remaining_time': black_time,
                                'color': 'Black'
                            })
            
            print(f"DEBUG: Processed {len(move_times)} moves for {'White' if is_white else 'Black'}")
            return sorted(move_times, key=lambda x: x['time_spent'], reverse=True)
            
        except Exception as e:
            print(f"Error analyzing move timing: {e}")
            print(f"Error details:", str(e))
            import traceback
            traceback.print_exc()
            return []

    def analyze_recent_game_timing(self, num_games: int = 20, moves_per_game: int = 3) -> List[Dict[str, Any]]:
        """
        Analyze timing for recent games.
        Returns a list of games with their longest-thought moves.
        """
        # Get recent games
        recent_games = sorted(self.games, key=lambda x: x['end_time'], reverse=True)[:num_games]
        
        game_timing_analysis = []
        
        for game in recent_games:
            move_times = self.get_move_timing_analysis(game)
            
            if move_times:
                # Get datetime for the game
                game_date = datetime.datetime.fromtimestamp(game['end_time'])
                
                # Get opening name
                opening = game['eco'].split('/')[-1] if 'eco' in game else 'Unknown Opening'
                
                # Get result
                result = self.get_player_result(game)
                
                # Get time control
                time_control = game.get('time_control', 'Unknown')
                
                # Calculate average time per move
                total_time = sum(move['time_spent'] for move in move_times)
                avg_time = total_time / len(move_times) if move_times else 0
                
                game_analysis = {
                    'date': game_date.strftime('%Y-%m-%d %H:%M'),
                    'url': game['url'],
                    'opening': opening,
                    'result': result,
                    'time_control': time_control,
                    'longest_moves': move_times[:moves_per_game],  # Get top N longest moves
                    'average_time_per_move': avg_time
                }
                
                game_timing_analysis.append(game_analysis)
        
        return game_timing_analysis