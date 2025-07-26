import genanki
import json
import os
import sys
from datetime import datetime

class ChessAnkiError(Exception):
    """Custom error class for Chess Anki card generation."""
    pass

# Define the Anki note model with enhanced fields
CHESS_MODEL = genanki.Model(
    1607392319,  # Unique model ID
    'Chess Position Analysis',
    fields=[
        {'name': 'Position'},
        {'name': 'GameDate'},
        {'name': 'PlayerColor'},
        {'name': 'MoveNumber'},
        {'name': 'ThinkTime'},
        {'name': 'GameURL'},
        {'name': 'BestMove'},
        {'name': 'Analysis'},
        {'name': 'Evaluation'}
    ],
    templates=[
        {
            'name': 'Chess Card',
            'qfmt': '''
                <div class="card-front">
                    <div class="game-info">
                        <p>Game Date: {{GameDate}}</p>
                        <p>Playing as: {{PlayerColor}}</p>
                        <p>Move: {{MoveNumber}}</p>
                        <p>Time Spent Thinking: {{ThinkTime}}</p>
                        <p class="game-url"><a href="{{GameURL}}">View Game Online</a></p>
                    </div>
                    {{Position}}
                    <p class="question">What is the best move in this position?</p>
                </div>
            ''',
            'afmt': '''
                {{FrontSide}}
                <hr>
                <div class="card-back">
                    <div class="evaluation">Position Evaluation: {{Evaluation}}</div>
                    {{BestMove}}
                    <div class="analysis">
                        {{Analysis}}
                    </div>
                </div>
            '''
        }
    ],
    css='''
        .card-front, .card-back {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
        }
        .game-info {
            color: #666;
            font-size: 14px;
            margin-bottom: 15px;
            text-align: left;
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
        }
        .game-url {
            margin-top: 8px;
        }
        .game-url a {
            color: #0066cc;
            text-decoration: none;
        }
        .game-url a:hover {
            text-decoration: underline;
        }
        .question {
            font-weight: bold;
            margin-top: 15px;
            font-size: 16px;
            color: #2c3e50;
        }
        .evaluation {
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .analysis {
            font-family: monospace;
            text-align: left;
            white-space: pre-wrap;
            margin-top: 15px;
            padding: 10px;
            background: #f5f5f5;
            border-radius: 5px;
        }
        hr {
            margin: 20px 0;
            border: none;
            border-top: 1px solid #ddd;
        }
    '''
)

def validate_svg_file(filepath):
    """Validate SVG file exists and contains valid content."""
    if not os.path.exists(filepath):
        raise ChessAnkiError(f"SVG file not found: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip().startswith('<svg'):
                raise ChessAnkiError(f"Invalid SVG content in file: {filepath}")
            return content
    except Exception as e:
        raise ChessAnkiError(f"Error reading SVG file {filepath}: {str(e)}")

def process_evaluation(eval_value):
    """Format evaluation value for display."""
    if isinstance(eval_value, str) and eval_value.startswith('M'):
        return f"Mate in {eval_value[1:]}"
    elif isinstance(eval_value, (int, float)):
        return f"{eval_value:+.2f}"
    return str(eval_value)

def create_chess_deck(input_file='analyzed_games.json', output_path='chess_positions.apkg'):
    """Create Anki deck from analyzed chess positions with error handling."""
    try:
        # Validate input file
        if not os.path.exists(input_file):
            raise ChessAnkiError(f"Input file not found: {input_file}")
        
        # Load and validate analyzed games data
        with open(input_file, 'r', encoding='utf-8') as f:
            try:
                analyzed_games = json.load(f)
            except json.JSONDecodeError as e:
                raise ChessAnkiError(f"Invalid JSON in input file: {str(e)}")
        
        if not analyzed_games:
            raise ChessAnkiError("No games found in input file")
        
        # Create deck
        deck = genanki.Deck(
            2059400110,  # Unique deck ID
            'Chess Position Analysis'
        )
        
        cards_created = 0
        errors = []
        
        for game_num, game in enumerate(analyzed_games, 1):
            game_date = game.get('end_time_utc', 'Unknown Date')
            player_color = game.get('player_color', 'Unknown')
            game_url = game.get('url', '#')
            
            for think in game.get('player_top_thinks', []):
                try:
                    # Validate and read SVG files
                    position_svg = validate_svg_file(think['position_file'])
                    best_move_svg = validate_svg_file(think['best_move_file'])
                    
                    # Create note with enhanced fields
                    note = genanki.Note(
                        model=CHESS_MODEL,
                        fields=[
                            position_svg,  # Position
                            game_date,     # GameDate
                            player_color,  # PlayerColor
                            str(think['move_number']),  # MoveNumber
                            think['time_spent_formatted'],  # ThinkTime
                            game_url,      # GameURL
                            best_move_svg, # BestMove
                            think['analysis'],  # Analysis
                            process_evaluation(think['evaluation'])  # Evaluation
                        ]
                    )
                    deck.add_note(note)
                    cards_created += 1
                    
                except Exception as e:
                    error_msg = f"Error processing think in game {game_num}: {str(e)}"
                    errors.append(error_msg)
                    print(f"Warning: {error_msg}")
        
        if cards_created == 0:
            raise ChessAnkiError("No valid cards could be created")
        
        # Save the deck
        genanki.Package(deck).write_to_file(output_path)
        print(f"\nSuccess! Created {cards_created} cards in deck {output_path}")
        
        if errors:
            print("\nWarnings during processing:")
            for error in errors:
                print(f"- {error}")
                
    except ChessAnkiError as e:
        print(f"\nError creating Anki deck: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1)

def main():
    print("Starting Anki deck generation...")
    create_chess_deck()

if __name__ == "__main__":
    main()