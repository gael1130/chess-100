import json
import requests
import os
from datetime import datetime
import time
from django.conf import settings
from typing import Optional, List, Dict
import logging

logger = logging.getLogger('stats_app')

class ChessComAPI:
    BASE_URL = "https://api.chess.com/pub"
    RATE_LIMIT_DELAY = 0.5  # 500ms between requests
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'My Python Application. Contact me at email@example.com'
        }
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Implement rate limiting."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - time_since_last_request)
        self.last_request_time = time.time()
    
    def _make_request(self, url: str) -> Optional[Dict]:
        """Make a rate-limited API request."""
        self._rate_limit()
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None

def fetch_and_save_chess_data(username: str) -> Optional[List[Dict]]:
    """Fetch chess games data from Chess.com API for a specified username."""
    today_date = datetime.now().strftime('%Y-%m-%d')
    cache_dir = os.path.join(settings.BASE_DIR, 'stats_app', 'data')
    filename = os.path.join(cache_dir, f'{username}_{today_date}.json')

    # Ensure cache directory exists
    os.makedirs(cache_dir, exist_ok=True)

    # Check for cached data
    if os.path.exists(filename):
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(filename)).strftime('%Y-%m-%d')
        if file_mod_time == today_date:
            logger.info(f"Loading cached data for {username}")
            try:
                with open(filename, 'r') as file:
                    return json.load(file)
            except json.JSONDecodeError:
                logger.error(f"Corrupted cache file: {filename}")
                os.remove(filename)

    # Fetch new data
    api = ChessComAPI()
    archives_url = f"{ChessComAPI.BASE_URL}/player/{username}/games/archives"
    archives_data = api._make_request(archives_url)

    if not archives_data:
        logger.error(f"Failed to fetch archives for user {username}")
        return None

    archives = archives_data.get('archives', [])
    games = []

    # Fetch games from each archive
    for archive_url in archives:
        archive_data = api._make_request(archive_url)
        if archive_data:
            games.extend(archive_data.get('games', []))
        else:
            logger.warning(f"Failed to fetch games from {archive_url}")

    if not games:
        logger.warning(f"No games found for user {username}")
        return None

    # Cache the results
    try:
        with open(filename, 'w') as file:
            json.dump(games, file, indent=4)
        logger.info(f"Cached {len(games)} games for {username}")
    except IOError as e:
        logger.error(f"Failed to cache games: {e}")

    return games