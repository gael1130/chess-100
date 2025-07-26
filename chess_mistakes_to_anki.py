import genanki
import json
import os
import sys
from datetime import datetime

class ChessAnkiError(Exception):
    """Custom error class for Chess Anki card generation."""
    pass

CHESS_MODEL = genanki.Model(
    1607392319,
    'Chess Mistakes Analysis',
    fields=[
        {'name': 'Position'},        # Position SVG
        {'name': 'GameURL'},         # URL of the game
        {'name': 'PlayerColor'},     # Color played
        {'name': 'MoveNumber'},      # Move where mistake happened
        {'name': 'MovePlayed'},      # The actual move that was played
        {'name': 'PositionBefore'},  # Evaluation before mistake
        {'name': 'PositionAfter'},   # Evaluation after mistake
        {'name': 'PositionLoss'},    # How much was lost
        {'name': 'BestMoves'},       # Better moves with scores
        {'name': 'BestMovePosition'} # SVG with arrow showing best move
    ],
    templates=[
        {
            'name': 'Chess Mistake Card',
            'qfmt': '''
                <div class="card-front">
                    <div class="game-info">
                        <p>Playing as: {{PlayerColor}}</p>
                        <p>Move: {{MoveNumber}}</p>
                        <p><a href="{{GameURL}}">View Game Online</a></p>
                    </div>
                    {{Position}}
                    <p class="question">What would be the best move in this position?</p>
                </div>
            ''',
            'afmt': '''
                {{FrontSide}}
                <hr>
                <div class="card-back">
                    <div class="position-info">
                        <p>You played: <span class="move-played">{{MovePlayed}}</span></p>
                        <p>Evaluation before: {{PositionBefore}}</p>
                        <p>Evaluation after: {{PositionAfter}}</p>
                        <p class="position-loss">Position loss: {{PositionLoss}}</p>
                    </div>
                    <div class="best-moves">
                        <h3>Better moves were:</h3>
                        {{BestMoves}}
                    </div>
                    {{BestMovePosition}}
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
        .game-info a {
            color: #0066cc;
            text-decoration: none;
        }
        .question {
            font-weight: bold;
            margin-top: 15px;
            font-size: 16px;
            color: #2c3e50;
        }
        .position-info {
            background: #f5f5f5;
            padding: 10px;
            border-radius: 5px;
            margin: 15px 0;
        }
        .position-loss {
            color: #e74c3c;
            font-weight: bold;
        }
        .best-moves {
            text-align: left;
            margin: 15px 0;
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

def format_better_moves(better_moves):
    """Format the list of better moves into HTML."""
    if not better_moves:
        return "No better moves found"
    
    moves_html = "<ul>"
    for move in better_moves:
        moves_html += f"<li>{move['move']} (Score: {move['score']})</li>"
    moves_html += "</ul>"
    return moves_html

def create_chess_deck(input_file, output_file='chess_mistakes.apkg'):
    """Create Anki deck from analyzed chess mistakes."""
    try:
        # Validate input file
        if not os.path.exists(input_file):
            raise ChessAnkiError(f"Input file not found: {input_file}")
        
        # Load analyzed mistakes
        with open(input_file, 'r', encoding='utf-8') as f:
            try:
                analyzed_mistakes = json.load(f)
            except json.JSONDecodeError as e:
                raise ChessAnkiError(f"Invalid JSON in input file: {str(e)}")
        
        if not analyzed_mistakes:
            raise ChessAnkiError("No mistakes found in input file")
        
        # Create deck
        deck = genanki.Deck(
            2059400110,
            'Chess Mistakes Analysis'
        )
        
        cards_created = 0
        errors = []
        
        for mistake in analyzed_mistakes:
            try:
                # Validate and read SVG files
                position_svg = validate_svg_file(mistake['position_svg'])
                best_move_svg = validate_svg_file(mistake['best_move_svg'])
                
                # Format better moves list
                better_moves_html = format_better_moves(mistake['better_moves'])
                
                # Create note
                note = genanki.Note(
                    model=CHESS_MODEL,
                    fields=[
                        position_svg,               # Position
                        mistake['game_url'],        # GameURL
                        mistake['player_color'],    # PlayerColor
                        str(mistake['move_number']), # MoveNumber
                        mistake['move_played'],     # MovePlayed - The actual move that was played
                        mistake['position_before'], # PositionBefore
                        mistake['position_after'],  # PositionAfter
                        mistake['position_loss'],   # PositionLoss
                        better_moves_html,          # BestMoves
                        best_move_svg              # BestMovePosition
                    ]
                )
                deck.add_note(note)
                cards_created += 1
                
            except Exception as e:
                error_msg = f"Error processing mistake: {str(e)}"
                errors.append(error_msg)
                print(f"Warning: {error_msg}")
        
        if cards_created == 0:
            raise ChessAnkiError("No valid cards could be created")
        
        # Save the deck
        genanki.Package(deck).write_to_file(output_file)
        print(f"\nSuccess! Created {cards_created} cards in deck {output_file}")
        
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
    # Get the most recent analysis file
    mistakes_dir = "chess_mistakes"
    json_files = [f for f in os.listdir(mistakes_dir) if f.startswith("analyzed_mistakes_") and f.endswith(".json")]
    
    if not json_files:
        print("No analysis files found in chess_mistakes directory")
        sys.exit(1)
    
    # Sort by timestamp in filename
    latest_file = sorted(json_files)[-1]
    input_file = os.path.join(mistakes_dir, latest_file)
    
    print(f"Starting Anki deck generation using {input_file}...")
    create_chess_deck(input_file)

if __name__ == "__main__":
    main()