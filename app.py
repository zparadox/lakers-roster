from flask import Flask, render_template, jsonify
import requests
import time
from functools import lru_cache
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def validate_response_data(data):
    """Validate the response data structure"""
    if not isinstance(data, dict):
        return False
    if 'resultSets' not in data:
        return False
    if not data['resultSets']:
        return False
    if 'rowSet' not in data['resultSets'][0]:
        return False
    return True

def calculate_fg_percentage(fgm, fga):
    """Calculate field goal percentage"""
    try:
        if not fga or float(fga) == 0:
            return "0.0%"
        fg_pct = (float(fgm) / float(fga)) * 100
        return f"{round(fg_pct, 1)}%"
    except (TypeError, ValueError, ZeroDivisionError):
        return "0.0%"

def get_player_stats(player_id, headers):
    """Fetch player stats from NBA Stats API"""
    try:
        # Get current season stats
        stats_url = "https://stats.nba.com/stats/playergamelog"
        stats_params = {
            'PlayerID': player_id,
            'Season': '2023-24',
            'SeasonType': 'Regular Season'
        }

        stats_response = requests.get(stats_url, headers=headers, params=stats_params, timeout=10)
        stats_response.raise_for_status()
        stats_data = stats_response.json()

        if not stats_data.get('resultSets') or not stats_data['resultSets'][0].get('rowSet'):
            return None

        # Calculate averages from game logs
        games = stats_data['resultSets'][0]['rowSet']
        games_played = len(games)
        
        if games_played == 0:
            return {
                'ppg': 0.0,
                'rpg': 0.0,
                'apg': 0.0,
                'spg': 0.0,
                'bpg': 0.0,
                'fg_pct': '0.0%',
                'games_played': 0
            }

        total_stats = {
            'points': 0,
            'rebounds': 0,
            'assists': 0,
            'steals': 0,
            'blocks': 0,
            'fgm': 0,
            'fga': 0
        }

        for game in games:
            total_stats['points'] += float(game[24])     # PTS
            total_stats['rebounds'] += float(game[20])   # REB
            total_stats['assists'] += float(game[21])    # AST
            total_stats['steals'] += float(game[22])     # STL
            total_stats['blocks'] += float(game[23])     # BLK
            total_stats['fgm'] += float(game[7])        # FGM
            total_stats['fga'] += float(game[8])        # FGA

        return {
            'ppg': round(total_stats['points'] / games_played, 1),
            'rpg': round(total_stats['rebounds'] / games_played, 1),
            'apg': round(total_stats['assists'] / games_played, 1),
            'spg': round(total_stats['steals'] / games_played, 1),
            'bpg': round(total_stats['blocks'] / games_played, 1),
            'fg_pct': calculate_fg_percentage(total_stats['fgm'], total_stats['fga']),
            'games_played': games_played
        }

    except (requests.RequestException, IndexError, KeyError, ValueError) as e:
        logger.error(f"Error fetching stats for player {player_id}: {str(e)}")
        return None

@lru_cache(maxsize=1)  # Cache the roster data for 1 hour
def get_lakers_roster():
    try:
        # NBA Stats API endpoints with required headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Host': 'stats.nba.com',
            'Connection': 'keep-alive',
            'x-nba-stats-token': 'true',
            'x-nba-stats-origin': 'stats',
            'Referer': 'https://www.nba.com/',
            'Origin': 'https://www.nba.com',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }

        # Get team roster
        roster_url = "https://stats.nba.com/stats/commonteamroster"
        roster_params = {
            'LeagueID': '00',
            'Season': '2023-24',
            'TeamID': '1610612747'  # Lakers team ID
        }

        response = requests.get(roster_url, headers=headers, params=roster_params, timeout=10)
        response.raise_for_status()
        roster_data = response.json()

        if not validate_response_data(roster_data):
            logger.error("Invalid roster data structure")
            return []

        # Process roster data
        player_details = []
        for player in roster_data['resultSets'][0]['rowSet']:
            try:
                player_name = player[3]  # PLAYER
                player_id = str(player[14])  # PLAYER_ID
                jersey_number = player[4]  # NUM
                position = player[5]  # POSITION
                height = player[6]  # HEIGHT

                # Get player stats
                stats = get_player_stats(player_id, headers)
                if stats is None:
                    stats = {
                        'ppg': 0.0,
                        'rpg': 0.0,
                        'apg': 0.0,
                        'spg': 0.0,
                        'bpg': 0.0,
                        'fg_pct': '0.0%',
                        'games_played': 0
                    }

                player_details.append({
                    'name': player_name,
                    'number': jersey_number,
                    'position': position,
                    'height': height,
                    'stats': stats,
                    'image_url': f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png"
                })

                # Add delay to avoid rate limiting
                time.sleep(0.5)

            except (IndexError, TypeError, ValueError) as e:
                logger.error(f"Error processing player data: {str(e)}")
                continue

        # Sort players by PPG
        player_details.sort(key=lambda x: x['stats']['ppg'], reverse=True)
        return player_details

    except requests.RequestException as e:
        logger.error(f"Error fetching data: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return []

@app.route('/')
def index():
    try:
        roster = get_lakers_roster()
        current_season = "2023-24"
        return render_template('index.html', 
                             players=roster, 
                             season=current_season,
                             current_year=datetime.now().year)
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}")
        return jsonify({"error": "An error occurred while loading the roster"}), 500

if __name__ == '__main__':
    app.run(debug=True) 
    app.run(debug=True) 