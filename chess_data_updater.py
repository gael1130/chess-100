import requests
import json
import time
from typing import List, Dict, Any
import os

class ChessDataUpdater:
    def __init__(self, filename: str):
        self.filename = filename
        self.base_url = "https://api.chess.com/pub"
        self.existing_games = self.load_existing_games()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; ChessGameAnalyzer/1.0; +http://example.com)',
            'Accept': 'application/json'
        }

    def load_existing_games(self) -> List[Dict[str, Any]]:
        """Load existing games from JSON file."""
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                return json.load(f)
        return []

    def save_games(self, games: List[Dict[str, Any]]):
        """Save games to JSON file."""
        with open(self.filename, 'w') as f:
            json.dump(games, f, indent=2)

    def get_existing_urls(self) -> set:
        """Get set of existing game URLs."""
        return {game['url'] for game in self.existing_games}

    def make_request(self, url: str, retries: int = 3) -> requests.Response:
        """Make a request with retry logic and rate limiting."""
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                time.sleep(2)  # Rate limiting - wait 2 seconds between requests
                return response
            except requests.RequestException as e:
                if attempt == retries - 1:  # Last attempt
                    raise
                print(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                time.sleep(5)  # Wait longer between retries

    def get_correct_username_case(self, username: str) -> str:
        """Get the correct case-sensitive username from Chess.com API."""
        try:
            response = self.make_request(f"{self.base_url}/player/{username}")
            return response.json().get('username', username)
        except requests.RequestException as e:
            print(f"Error fetching user profile: {e}")
            return username

    def get_archives_urls(self, username: str) -> List[str]:
        """Get list of monthly archive URLs for a user."""
        try:
            correct_username = self.get_correct_username_case(username)
            print(f"Fetching archives for user: {correct_username}")
            
            response = self.make_request(f"{self.base_url}/player/{correct_username}/games/archives")
            return response.json()['archives']
        except requests.RequestException as e:
            print(f"Error fetching archives: {e}")
            return []

    def get_games_from_archive(self, archive_url: str) -> List[Dict[str, Any]]:
        """Get games from a monthly archive URL."""
        try:
            response = self.make_request(archive_url)
            return response.json()['games']
        except requests.RequestException as e:
            print(f"Error fetching games from {archive_url}: {e}")
            return []

    def update_games(self, username: str) -> tuple:
        """
        Update games for a given username.
        Returns tuple of (new_games_count, total_games_count).
        """
        try:
            existing_urls = self.get_existing_urls()
            archives = self.get_archives_urls(username)
            
            if not archives:
                print("No archives found. Please check the username.")
                return 0, len(self.existing_games)
                
            new_games = []
            print(f"Found {len(archives)} monthly archives")
            
            # Process most recent archives first
            for archive_url in reversed(archives):
                print(f"Fetching games from {archive_url}")
                
                # Get games from this archive
                games = self.get_games_from_archive(archive_url)
                print(f"Found {len(games)} games in archive")
                
                # Check if we've found any new games
                new_in_archive = [game for game in games if game['url'] not in existing_urls]
                print(f"Found {len(new_in_archive)} new games in this archive")
                
                if not new_in_archive and new_games:
                    # If no new games in this archive and we already found some new games,
                    # we can skip older archives
                    print("No new games found in this archive, skipping older archives")
                    break
                    
                new_games.extend(new_in_archive)

            # Combine existing and new games
            all_games = self.existing_games + new_games
            
            # Sort games by end time
            all_games.sort(key=lambda x: x['end_time'], reverse=True)
            
            # Save updated games
            self.save_games(all_games)
            
            return len(new_games), len(all_games)
        except Exception as e:
            print(f"An error occurred during update: {e}")
            return 0, len(self.existing_games)

def update_chess_data(username: str, filename: str) -> tuple:
    """
    Convenience function to update chess data for a user.
    Returns tuple of (new_games_count, total_games_count).
    """
    updater = ChessDataUpdater(filename)
    return updater.update_games(username)

if __name__ == "__main__":
    # Path to your JSON file
    filename = "chess_stats/stats_app/data/Kalel1130.json"

    # Update the data
    new_games, total_games = update_chess_data("kalel1130", filename)

    print(f"Added {new_games} new games")
    print(f"Total games in database: {total_games}")