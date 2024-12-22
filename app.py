from flask import Flask, render_template, jsonify
import requests
import time
from functools import lru_cache
import logging

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
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site'
        }

        # First, get the roster information
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
                player_id = str(player[14])  # PLAYER_ID
                print(player)
                player_details.append({
                    'name': player[3],       # PLAYER
                    'number': player[4],     # NUM
                    'position': player[5],   # POSITION
                    'height': player[6],     # HEIGHT
                    'weight': f"{player[7]} lbs",  # WEIGHT
                    'stats': {
                        'ppg': 0.0,
                        'rpg': 0.0,
                        'apg': 0.0,
                        'spg': 0.0,
                        'bpg': 0.0,
                        'fg_pct': 'N/A'
                    },
                    'image_url': f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png"
                })

                # Get player stats
                stats_url = f"https://stats.nba.com/stats/playerprofilev2"
                stats_params = {
                    'PlayerID': player_id,
                    'PerMode': 'PerGame',
                    'LeagueID': '00'
                }

                stats_response = requests.get(stats_url, headers=headers, params=stats_params, timeout=10)
                if stats_response.status_code == 200:
                    stats_data = stats_response.json()
                    if 'resultSets' in stats_data and len(stats_data['resultSets']) > 0:
                        season_stats = stats_data['resultSets'][1]['rowSet']
                        if season_stats:
                            current_stats = season_stats[-1]  # Get most recent season
                            player_details[-1]['stats'].update({
                                'ppg': round(float(current_stats[3]), 1),   # PTS
                                'rpg': round(float(current_stats[5]), 1),   # REB
                                'apg': round(float(current_stats[4]), 1),   # AST
                                'spg': round(float(current_stats[6]), 1),   # STL
                                'bpg': round(float(current_stats[7]), 1),   # BLK
                                'fg_pct': f"{round(float(current_stats[11] * 100), 1)}%"  # FG_PCT
                            })

                # Add delay to avoid rate limiting
                time.sleep(0.5)

            except (IndexError, TypeError, ValueError) as e:
                logger.error(f"Error processing player data: {str(e)}")
                continue
            except requests.RequestException as e:
                logger.error(f"Error fetching player stats: {str(e)}")
                continue

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
        return render_template('index.html', players=roster)
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}")
        return jsonify({"error": "An error occurred while loading the roster"}), 500

if __name__ == '__main__':
    app.run(debug=True) 