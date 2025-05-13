import os
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from tabulate import tabulate

class TFTTimeline:
    def __init__(self):
        self.base_url = "https://lolchess.gg/profile"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_player_data(self, summoner_name, region="tw"):
        """Get player data from lolchess.gg"""
        url = f"{self.base_url}/{region}/{summoner_name}"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                print(f"Failed to fetch data: {response.status_code}")
                return None

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract recent matches
            matches = []
            match_elements = soup.select('.profile__match-history__item')
            
            for match in match_elements:
                match_data = {
                    'placement': match.select_one('.placement').text.strip(),
                    'date': match.select_one('.time').text.strip(),
                    'traits': [trait.text.strip() for trait in match.select('.trait')],
                    'units': [unit.text.strip() for unit in match.select('.unit')]
                }
                matches.append(match_data)
            
            return matches
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None

    def display_match_history(self, matches):
        """Display match history in a formatted way"""
        if not matches:
            print("No matches found")
            return

        print("\n=== Recent TFT Matches ===")
        for match in matches:
            print(f"\nPlacement: {match['placement']}")
            print(f"Date: {match['date']}")
            print("Traits:")
            for trait in match['traits']:
                print(f"- {trait}")
            print("Units:")
            for unit in match['units']:
                print(f"- {unit}")
            print("-" * 50)

def main():
    try:
        tft = TFTTimeline()
        
        # Get summoner name from user
        summoner_name = input("Enter summoner name: ").strip()
        region = input("Enter region (e.g., tw, na, euw): ").strip().lower()
        
        while True:
            print(f"\nFetching data for {summoner_name}...")
            matches = tft.get_player_data(summoner_name, region)
            
            if matches:
                tft.display_match_history(matches)
            else:
                print("No matches found or error occurred")
            
            # Wait before next check
            print("\nWaiting 60 seconds before next update...")
            time.sleep(60)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 