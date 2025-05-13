import os
import time
import asyncio
import argparse
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from datetime import datetime
from tabulate import tabulate
from dotenv import load_dotenv
import pyperclip
from pprint import pprint
import array_help

class TFTTimeline:
    def __init__(self):
        self.base_url = "https://www.metatft.com/player"

    async def process_players_tab(self, soup, match_data):
        """Process the Players tab content"""
        # Extract opponent rank data
        rank_summary = soup.find('div', class_='GameRankSummary')
        if rank_summary:
            rank_data = {
                'tier': None,
                'division': None,
                'lp': None
            }
            
            # Get rank tier (e.g., PLATINUM)
            rank_div = rank_summary.find('div', class_='PlayerRank')
            if rank_div:
                rank_data['tier'] = rank_div.get_text(strip=True).lower()
            
            # Get division (e.g., IV)
            division_span = rank_summary.find('span', class_='PlayerRankDivision')
            if division_span:
                rank_data['division'] = division_span.get_text(strip=True)
            
            # Get LP
            lp_div = rank_summary.find('div', class_='PlayerRankLP')
            if lp_div:
                rank_data['lp'] = lp_div.get_text(strip=True)
            
            match_data['opponent_rank'] = rank_data
            
        # Extract player match data
        player_matches = soup.find_all('div', class_='PlayerGameMatch')
        players_data = []
        
        print("\nPlayers in match:")
        for player_match in player_matches:
            player_data = self.extract_player_data(player_match)
            players_data.append(player_data)
            print(f"- {player_data['name']} #{player_data.get('tag', '')}")
        
        match_data['players'] = players_data
        return match_data

    def extract_player_data(self, player_match):
        player_data = {}
        
        try:
            # Get placement
            placement_div = player_match.find('div', class_='PlayerMatchSummaryPlacement')
            if placement_div:
                player_data['placement'] = placement_div.get_text(strip=True)
            
            # Get player level
            level_div = player_match.find('div', class_='PlayerLevel')
            if level_div:
                player_data['level'] = level_div.get_text(strip=True)
            
            # Get player name and tag
            name_link = player_match.find('a', class_='PlayerMatchName')
            if not name_link:
                name_link = player_match.find('div', class_='PlayerMatchName')
            if name_link:
                try:
                    name_text = name_link.get_text(strip=True)
                    
                    tagline = name_link.find('span', class_='PlayerTagline')
                    if tagline:
                        tag_text = tagline.get_text(strip=True)
                        # Remove the tag from the name
                        name_text = name_text.replace(tag_text, '').strip()
                        player_data['tag'] = tag_text
                    else:
                        player_data['tag'] = ''
                    
                    player_data['name'] = name_text
                except Exception:
                    player_data['name'] = 'Unknown'
                    player_data['tag'] = ''
            else:
                player_data['name'] = 'Unknown'
                player_data['tag'] = ''
            
            # Get match stage
            duration_div = player_match.find('div', class_='PlayerMatchDuration')
            if duration_div:
                try:
                    duration_text = duration_div.get_text(strip=True)
                    if '•' in duration_text:
                        _, stage = duration_text.split('•')
                        player_data['stage'] = stage.strip()
                except Exception:
                    player_data['stage'] = 'Unknown'
            else:
                player_data['stage'] = 'Unknown'
            
            # Get stats (damage done, board value) from PlayerMatchSection StatSection
            stats_section = player_match.find('div', class_='PlayerMatchSection StatSection')
            if stats_section:
                stats = stats_section.find_all('div', class_='PlayerMatchStat')
                for stat in stats:
                    stat_text = stat.find('div', class_='PlayerMatchStatText')
                    if stat_text:
                        # Check for damage done icon
                        if stat_text.find('img', class_='DamageDoneIcon'):
                            player_data['damage_done'] = stat_text.get_text(strip=True).replace('Damage Done', '').strip()
                        # Check for board value icon
                        elif stat_text.find('img', class_='BoardValueIcon'):
                            player_data['board_value'] = stat_text.get_text(strip=True).replace('Board Value', '').strip()
            
            # Get traits
            try:
                player_data['traits'] = self.extract_traits(player_match)
            except Exception:
                player_data['traits'] = []
            
            # Get units
            try:
                player_data['units'] = self.extract_units(player_match)
            except Exception:
                player_data['units'] = []
            
            return player_data
            
        except Exception:
            return player_data

    def extract_traits(self, player_match):
        """Extract traits for a player"""
        traits = []
        trait_containers = player_match.find_all('div', class_='TraitCompactContainer')
        for trait in trait_containers:
            # Get trait name from mask-image URL
            icon_container = trait.find('div', class_='TraitCompactIconContainer')
            if icon_container:
                style = icon_container.get('style', '')
                if 'mask-image' in style:
                    # Extract trait name from URL
                    trait_name = style.split('traits/')[1].split('.png')[0]
                    trait_data = {
                        'name': trait_name,
                        'count': trait.get_text(strip=True)
                    }
                    traits.append(trait_data)
        return traits

    def extract_units(self, player_match):
        units = []
        unit_wrappers = player_match.find_all('div', class_='Unit_Wrapper')
        for unit in unit_wrappers:
            try:
                unit_data = {}
                unit_data['tier'] = '1'
                stars_img = unit.find('img', class_='Stars_img')
                if stars_img:
                    tier_alt = stars_img.get('alt', '')
                    if tier_alt:
                        unit_data['tier'] = tier_alt.replace('Tier ', '')
                
                unit_img = unit.find('img', class_='Unit_img')
                if unit_img:
                    unit_data['name'] = unit_img.get('alt', '') 
                unit_data['items'] = self.extract_unit_items(unit)
                
                units.append(unit_data)
                
            except Exception:
                continue
                
        return units

    def extract_unit_items(self, unit):
        items = []
        try:
            item_imgs = unit.find_all('img', class_='Item_img')
            for item in item_imgs:
                item_name = item.get('alt', '')
                if item_name:
                    items.append(item_name)
        except Exception:
            pass
        return items
    
    def players_tab_summary(self, soup):
        try:
            summary_div = soup.find('div', class_='GameSummary')
            if not summary_div:
                return []
            summary_data = []
            summary_tags = summary_div.find_all('div', class_='PlayerTag')
            for tag in summary_tags:
                # found a case with only one class
                tag_type = 'none' if len(tag.get('class', []))==1 else tag.get('class', [])[1].replace('PlayerTag', '')
                summary_data.append(f"{tag.get_text(strip=True)}:{tag_type}")
            return summary_data
        except Exception as e:
            print(f"Error get summary: {str(e)}")
            return []

    def players_tab_avg_rank(self, soup):
        rank_summary = soup.find('div', class_='GameRankSummary')
        if not rank_summary:
            return {}
        rank_div = rank_summary.find('div', class_='PlayerRank')
        division_span = rank_summary.find('span', class_='PlayerRankDivision')
        lp_div = rank_summary.find('div', class_='PlayerRankLP')
        if not rank_div or not division_span or not lp_div:
            return {}
        avg_rank_data = {}
        avg_rank_data['tier'] = rank_div.get_text(strip=True).lower()
        avg_rank_data['division'] = division_span.get_text(strip=True)
        avg_rank_data['lp'] = lp_div.get_text(strip=True)
        return avg_rank_data
    
    def players_tab_players(self, soup):
        player_list = soup.find_all('div', class_='PlayerGameMatchDropdown')
        players_data = []
        for player in player_list:
            player_data = self.players_tab_player_data(player)
            players_data.append(player_data)
        return players_data

    def check_get_text(self, content):
        if not content:
            return ''
        return content.get_text(strip=True)
    
    def players_tab_player_data(self, player):
        player_data = {}
        placement_div = player.find('div', class_='PlayerMatchSummaryPlacement')
        player_data['placement'] = self.check_get_text(placement_div)
        level_div = player.find('div', class_='PlayerLevel')
        player_data['level'] = self.check_get_text(level_div)
        name_link = player.find('a', class_='PlayerMatchName')
        if not name_link:
            name_link = player.find('div', class_='PlayerMatchName')
        name_text = self.check_get_text(name_link)
        tagline = name_link.find('span', class_='PlayerTagline')
        tag_text = self.check_get_text(tagline)
        player_data['name'] = name_text
        player_data['tag'] = tag_text
        duration_div = player.find('div', class_='PlayerMatchDuration')
        if duration_div:
            duration_text = self.check_get_text(duration_div)
            if '•' in duration_text:
                duration, stage = duration_text.split('•')
                player_data['duration'] = duration.strip()
                player_data['stage'] = stage.strip()
        
        stats_section = player.find('div', class_='PlayerMatchSection StatSection')
        if stats_section:
            stats = stats_section.find_all('div', class_='PlayerMatchStat')
            for stat in stats:
                stat_text = stat.find('div', class_='PlayerMatchStatText')
                if stat_text:
                    if stat_text.find('img', class_='DamageDoneIcon'):
                        player_data['damage_done'] = stat_text.get_text(strip=True).replace('Damage Done', '').strip()
                    elif stat_text.find('img', class_='BoardValueIcon'):
                        player_data['board_value'] = stat_text.get_text(strip=True).replace('Board Value', '').strip()
        try:
            
            # Get traits
            try:
                player_data['traits'] = self.extract_traits(player)
            except Exception:
                player_data['traits'] = []
            
            # Get units
            try:
                player_data['units'] = self.extract_units(player)
            except Exception:
                player_data['units'] = []
            
            return player_data
            
        except Exception:
            return player_data
            
    def players_tab_content(self, soup, match_data):
        match_data['players_summary'] = self.players_tab_summary(soup)
        match_data['avg_opponent_rank'] = self.players_tab_avg_rank(soup)
        match_data['players'] = self.players_tab_players(soup)
        
        return match_data
        
    async def process_tab_content(self, tab_name, content, match_data):
        soup = BeautifulSoup(content, 'html.parser')
        if tab_name.lower() == 'players':
            match_data = self.players_tab_content(soup, match_data)
        elif tab_name.lower() == 'personal summary':
            # Extract summary data from Personal Summary tab
            summary_div = soup.find('div', class_='GameSummary')
            if summary_div:
                summary_data = {
                    'positive': [],
                    'negative': [],
                    'ap': []
                }
                
                # Find all summary tags
                summary_tags = summary_div.find_all('div', class_='PlayerTag')
                for tag in summary_tags:
                    tag_text = tag.get_text(strip=True)
                    if 'PlayerTagpositive' in tag.get('class', []):
                        summary_data['positive'].append(tag_text)
                    elif 'PlayerTagnegative' in tag.get('class', []):
                        summary_data['negative'].append(tag_text)
                    elif 'PlayerTagAP' in tag.get('class', []):
                        summary_data['ap'].append(tag_text)
                
                match_data['personal_summary'] = summary_data
            
            # Extract stage breakdown data
            stage_breakdown = soup.find('div', class_='PlayerGameSummaryHighlightStage')
            if stage_breakdown:
                stage_data = []
                stages = stage_breakdown.find_all('div', class_='PlayerGameSummaryStage')
                
                for stage in stages:
                    stage_info = {}
                    
                    # Get stage name and win rate
                    win_rate_div = stage.find('div', class_='PlayerGameSummaryStageWinRate')
                    if win_rate_div:
                        stage_info['name'] = win_rate_div.find('div', class_='PlayerGameSummaryStageText').get_text(strip=True)
                        stage_info['win_rate'] = win_rate_div.find('div', class_='PlayerGameSummaryStageWinRateNumber').get_text(strip=True)
                    
                    # Get MVP unit
                    mvp_div = stage.find('div', class_='UnitMVP')
                    if mvp_div:
                        stage_info['mvp'] = {
                            'name': mvp_div.find('div', class_='UnitMVPName').get_text(strip=True),
                            'avg_damage': stage.find('div', class_='UnitMVPStat').find('div', class_='UnitMVPStatNumber').get_text(strip=True),
                            'max_damage': stage.find_all('div', class_='UnitMVPStat')[1].find('div', class_='UnitMVPStatNumber').get_text(strip=True),
                            'win_rate': stage.find_all('div', class_='UnitMVPStat')[2].find('div', class_='PlayerGameSummaryStageWinRateNumber').get_text(strip=True)
                        }
                    
                    stage_data.append(stage_info)
                
                match_data['stage_breakdown'] = stage_data
            
            # Extract economy data
            economy_div = soup.find('div', class_='PlayerGameSummaryEconomy')
            if economy_div:
                economy_data = {}
                
                # First row of stats
                first_row = economy_div.find('div', class_='PlayerGameSummaryHighlightStatsRow')
                if first_row:
                    stats = first_row.find_all('div', class_='PlayerGameSummaryHighlightStat')
                    for stat in stats:
                        stat_name = stat.find('div', class_='PlayerGameSummaryStageText').get_text(strip=True)
                        stat_value = stat.find('div', class_='PlayerGameSummaryHighlightStatNumber').get_text(strip=True)
                        economy_data[stat_name.lower()] = stat_value
                
                # Second row of stats
                second_row = economy_div.find_all('div', class_='PlayerGameSummaryHighlightStatsRow')[1]
                if second_row:
                    stats = second_row.find_all('div', class_='PlayerGameSummaryHighlightStat')
                    for stat in stats:
                        stat_name = stat.find('div', class_='PlayerGameSummaryStageText').get_text(strip=True)
                        stat_value = stat.find('div', class_='PlayerGameSummaryHighlightStatNumber').get_text(strip=True)
                        economy_data[stat_name.lower()] = stat_value
                
                match_data['economy'] = economy_data

            # Extract planning phase data
            planning_div = soup.find('div', class_='PlayerGameSummaryActions')
            if planning_div:
                planning_data = {}
                
                # First row of stats
                first_row = planning_div.find('div', class_='PlayerGameSummaryHighlightStatsRow')
                if first_row:
                    stats = first_row.find_all('div', class_='PlayerGameSummaryHighlightStat')
                    for stat in stats:
                        stat_name = stat.find('div', class_='PlayerGameSummaryStageText').get_text(strip=True)
                        stat_value = stat.find('div', class_='PlayerGameSummaryHighlightStatNumber').get_text(strip=True)
                        planning_data[stat_name.lower()] = stat_value
                
                # Second row of stats
                second_row = planning_div.find_all('div', class_='PlayerGameSummaryHighlightStatsRow')[1]
                if second_row:
                    stats = second_row.find_all('div', class_='PlayerGameSummaryHighlightStat')
                    for stat in stats:
                        stat_name = stat.find('div', class_='PlayerGameSummaryStageText').get_text(strip=True)
                        stat_value = stat.find('div', class_='PlayerGameSummaryHighlightStatNumber').get_text(strip=True)
                        planning_data[stat_name.lower()] = stat_value
                
                match_data['planning'] = planning_data

            # Extract key rounds data
            key_rounds_div = soup.find('div', class_='PlayerGameSummaryKeyRounds')
            if key_rounds_div:
                key_rounds_data = []
                key_round_rows = key_rounds_div.find_all('div', class_='KeyRoundRow')
                
                for row in key_round_rows:
                    round_data = {}
                    
                    # Get round title (Worst Loss, Clutch Win, etc.)
                    title_div = row.find('div', class_='KeyRoundTitle')
                    if title_div:
                        round_data['title'] = title_div.get_text(strip=True)
                    
                    # Get opponent name
                    opponent_div = row.find('div', class_='KeyRoundOpponent')
                    if opponent_div:
                        round_data['opponent'] = opponent_div.get_text(strip=True).replace('vs', '').strip()
                    
                    # Get HP loss or win chance
                    hp_loss = row.find('div', class_='HPLoss')
                    if hp_loss:
                        round_data['hp_loss'] = hp_loss.get_text(strip=True)
                    
                    win_chance = row.find('div', class_='KeyRoundWinChance')
                    if win_chance:
                        round_data['win_chance'] = win_chance.get_text(strip=True)
                    
                    # Get stage
                    stage_div = row.find('div', class_='KeyRoundStage')
                    if stage_div:
                        round_data['stage'] = stage_div.get_text(strip=True)
                    
                    # Get units
                    units_div = row.find('div', class_='KeyRoundUnits')
                    if units_div:
                        units = []
                        unit_divs = units_div.find_all('div', class_='KeyRoundUnit')
                        for unit in unit_divs:
                            unit_data = {}
                            
                            # Get unit tier
                            tier_img = unit.find('img', class_='KeyRoundTiers')
                            if tier_img:
                                unit_data['tier'] = tier_img.get('alt', '').replace('Tier ', '')
                            
                            # Get unit name
                            unit_img = unit.find('img', class_='KeyRoundUnitImage')
                            if unit_img:
                                unit_data['name'] = unit_img.get('alt', '')
                            
                            units.append(unit_data)
                        
                        round_data['units'] = units
                    
                    key_rounds_data.append(round_data)
                
                match_data['key_rounds'] = key_rounds_data
        elif tab_name.lower() == 'timeline':
            # Process timeline data
            timeline_data = {}
            
            # Find the timeline table
            timeline_table = soup.find('table')
            if timeline_table:
                
                # Get headers to know column positions
                headers = timeline_table.find('thead')
                if headers:
                    header_cells = headers.find_all('th')
                    header_map = {}
                    for i, cell in enumerate(header_cells):
                        header_map[cell.get_text(strip=True).lower()] = i
                
                # Get all rows except header
                rows = timeline_table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) < 0:
                        continue

                    stage = cells[0].get_text(strip=True)
                    
                    stage_data = {
                        'board': cells[header_map.get('board', 1)].get_text(strip=True) if len(cells) > header_map.get('board', 1) else 'N/A',
                        'item_bench': cells[header_map.get('item bench', 2)].get_text(strip=True) if len(cells) > header_map.get('item bench', 2) else 'N/A',
                        'level': cells[header_map.get('levels', 4)].get_text(strip=True) if len(cells) > header_map.get('levels', 4) else 'N/A',
                        'gold': cells[header_map.get('gold', 5)].get_text(strip=True) if len(cells) > header_map.get('gold', 5) else 'N/A',
                        'rerolls': cells[header_map.get('rerolls', 6)].get_text(strip=True) if len(cells) > header_map.get('rerolls', 6) else 'N/A',
                        'hp': cells[header_map.get('health', 7)].get_text(strip=True) if len(cells) > header_map.get('health', 7) else 'N/A',
                        'position': cells[header_map.get('position', 8)].get_text(strip=True) if len(cells) > header_map.get('position', 8) else 'N/A',
                        'damage': cells[header_map.get('damage', 9)].get_text(strip=True) if len(cells) > header_map.get('damage', 9) else 'N/A',
                        'scouting': cells[header_map.get('scouting', 10)].get_text(strip=True) if len(cells) > header_map.get('scouting', 10) else 'N/A',
                        'units': [],
                        'bench_items': [],
                        'upgrades': [],
                    }
                    
                    board_cell = cells[header_map.get('board', 1)]
                    unit_containers = board_cell.find_all('div', class_='StageUnitContainer') if board_cell else []
                    for container in unit_containers:
                        unit_img = container.find('img', class_='TableItemImg')
                        name = unit_img.get('alt', '') if unit_img else 'Unknown'
                        tier_img = container.find('img', class_='SmallStars') if unit_img else None
                        tier = tier_img.get('alt', '').replace('Tier ', '') if tier_img else '1'
                        unit_data = {
                            'name': name,
                            'tier': tier,
                            'items': []
                        }
                        
                        items_wrapper = container.find('div', class_='SmallItemsWrapper')
                        items = items_wrapper.find_all('img') if items_wrapper else []
                        for item in items:
                            array_help.append_none_check(unit_data['items'], item.get('alt', ''))
                            
                        stage_data['units'].append(unit_data)

                    item_bench_cell = cells[header_map.get('item bench', 2)]
                    items_bench_containers = item_bench_cell.find_all('img', class_='BenchItemImg') if item_bench_cell else []
                    
                    for container in items_bench_containers:
                        array_help.append_none_check(stage_data['bench_items'], container.get('alt', ''))

                    upgrade_cells = cells[header_map.get('upgrades', 3)]
                    unit_containers = upgrade_cells.find_all('div', class_='StageUnitContainer') if upgrade_cells else []
                    for container in unit_containers:
                        unit_img = container.find('img', class_='TableItemImg')
                        name = unit_img.get('alt', '') if unit_img else 'Unknown'
                        tier_img = container.find('img', class_='SmallStars') if unit_img else None
                        tier = tier_img.get('alt', '').replace('Tier ', '') if tier_img else '1'
                        unit_data = {
                            'name': name,
                            'tier': tier,
                        }
                        stage_data['upgrades'].append(unit_data)

                    timeline_data[stage] = stage_data
                
                match_data['timeline'] = timeline_data
            else:
                print("No timeline table found")
        
        return match_data

    async def get_match_details(self, page, match_id):
        """Get detailed data from all tabs of a match"""
        try:
            expand_button = await page.query_selector(f'#{match_id} .PlayerGameExpandImageContainer')
            if not expand_button:
                print(f"Could not find expand button for match {match_id}")
                return None
                
            await expand_button.click()
            
            await page.wait_for_selector(f'#{match_id} .PlayerGameDropdown', state='visible')
            await page.wait_for_timeout(1000)  # Give extra time for content to load
            
            match_container = await page.query_selector(f'#{match_id}')
            if not match_container:
                print(f"Could not find match container for {match_id}")
                return None
                
            tab_elements = await match_container.query_selector_all('.CompsTab .TabSelection')
            
            if len(tab_elements) == 0:
                tab_elements = await match_container.query_selector_all('.TabsContainer .TabSelection')
            
            match_data = {'match_id': match_id}
            
            for tab in tab_elements:
                try:
                    tab_name = await tab.text_content()
                    if tab_name.lower() == 'shop analysis':
                        continue
                    await tab.click()
                    await page.wait_for_timeout(500)

                    active_tab = await match_container.query_selector('.tab-content .tab-pane.active')
                    if not active_tab:
                        active_tab = await match_container.query_selector('.PlayerGameDropdown')
                    
                    if active_tab:
                        content = await active_tab.inner_html()
                        match_data = await self.process_tab_content(tab_name, content, match_data)
                
                except Exception as e:
                    print(f"Error processing tab {tab_name}: {str(e)}")
                    continue
            
            return match_data
            
        except Exception as e:
            print(f"Error getting details for match {match_id}: {str(e)}")
            return None

    async def get_player_data(self, riot_id, region="tw"):
        """Get player data from MetaTFT using Riot ID"""
        # Convert Riot ID to URL format (replace # with -)
        formatted_id = riot_id.replace('#', '-')
        url = f"{self.base_url}/{region}/{formatted_id}"
        print(f"Fetching data for {riot_id}...")
        
        async with async_playwright() as p:
            # Launch browser with increased timeout
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            page = await context.new_page()
            
            try:
                # Try loading the page with retries
                max_retries = 3
                retry_count = 0
                while retry_count < max_retries:
                    try:
                        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                        break
                    except Exception as e:
                        retry_count += 1
                        if retry_count == max_retries:
                            raise e
                        await asyncio.sleep(5)
                
                # Wait for the Ranked tab to be visible and click it
                try:
                    ranked_button = await page.wait_for_selector('button:has-text("Ranked")', timeout=30000)
                    if not ranked_button:
                        return None
                    await ranked_button.click()
                except Exception as e:
                    return None
                
                # Wait for the matches to load
                try:
                    await page.wait_for_selector('.PlayerGame', timeout=30000)
                except Exception as e:
                    return None
                
                # Get first match only
                match_elements = await page.query_selector_all('.PlayerGame')
                
                if match_elements:
                    match_id = await match_elements[0].get_attribute('id')
                    if match_id:
                        match_data = await self.get_match_details(page, match_id)
                        if match_data:
                            return [match_data]
                
                return None
                
            except Exception as e:
                print(f"Error fetching data: {e}")
                return None
            finally:
                await browser.close()

    def display_players_summary(self, recent_match, clipboard_text):
        """Display players summary data if available"""
        if 'players_summary' in recent_match:
            print("PLAYERS SUMMARY:")
            summary_data = recent_match['players_summary']
            if summary_data:
                for tag in summary_data:
                    print(f"+ {tag}")
                clipboard_text.extend(["\nSummary:"] + [f"- {tag}" for tag in summary_data])
        return clipboard_text

    def display_avg_opponent_rank(self, recent_match, clipboard_text):
        """Display average opponent rank data if available"""
        if 'avg_opponent_rank' in recent_match:
            print("\nAVG RANK:")
            rank_data = recent_match['avg_opponent_rank']
            print(f"Tier: {rank_data.get('tier', 'N/A')} {rank_data.get('division', 'N/A')}")
            clipboard_text.extend([
                "\nAVERAGE OPPONENT RANK:",
                f"Tier: {rank_data.get('tier', 'N/A')}",
                f"Division: {rank_data.get('division', 'N/A')}",
                f"LP: {rank_data.get('lp', 'N/A')}"
            ])
        return clipboard_text

    def display_players_data(self, recent_match, clipboard_text):
        print("display_players_data")
        if 'players' in recent_match:
            players_data = recent_match['players']
            
            if isinstance(players_data, list):
                for player in players_data:
                    if isinstance(player, dict):
                        print(f"\nP{player.get('placement', 'N/A')} Player: {player.get('name', 'N/A')}#{player.get('tag', 'N/A')}")
                        print(f"Lv: {player.get('level', 'N/A')}")
                        print(f"Stage: {player.get('stage', 'N/A')}")
                        print(f"Damage Done: {player.get('damage_done', 'N/A')}")
                        print(f"Board Value: {player.get('board_value', 'N/A')}")
                        
                        if 'traits' in player:
                            print("\nTraits:")
                            for trait in player['traits']:
                                print(f"{trait['name']}: {trait['count']}")
                        
                        # {'tier': '3', 'name': 'Twisted Fate', 'items': ['Hextech Gunblade', "Guinsoo's Rageblade", "Guinsoo's Rageblade"]}
                        if 'units' in player:
                            print("\nUnits:")
                            for unit in player['units']:
                                print(f"{unit['name']} (Tier {unit['tier']})")
                                if unit['items']:
                                    print("Items:")
                                    pprint(unit['items'])
                        
                        clipboard_text.extend([
                            f"\nPlayer: {player.get('name', 'N/A')} #{player.get('tag', 'N/A')}",
                            f"Placement: {player.get('placement', 'N/A')}",
                            f"Level: {player.get('level', 'N/A')}",
                            f"Stage: {player.get('stage', 'N/A')}",
                            f"Damage Done: {player.get('damage_done', 'N/A')}",
                            f"Board Value: {player.get('board_value', 'N/A')}"
                        ])
            else:
                if isinstance(players_data, dict) and 'html' in players_data:
                    soup = BeautifulSoup(players_data['html'], 'html.parser')
                    player_matches = soup.find_all('div', class_='PlayerGameMatch')
                    for player_match in player_matches:
                        player_data = self.extract_player_data(player_match)
                        print(f"\nP{player_data.get('placement', 'N/A')} Player: {player_data.get('name', 'N/A')} #{player_data.get('tag', 'N/A')}")
                        print(f"GET Level {player_data.get('level', 0)!=0} Stage {player_data.get('stage', 0)!=0} Damage Done {player_data.get('damage_done', -1)!=-1} Board Value {player_data.get('board_value', -1)!=-1}")
                        
                        # Display traits
                        if 'traits' in player_data:
                            print("\nTraits:")
                            for trait in player_data['traits']:
                                print(f"{trait['name']}: {trait['count']}")
                                #print first one only
                                print(f"...")
                                break
                        
                        # Display units
                        if 'units' in player_data:
                            print("\nUnits:")
                            for unit in player_data['units']:
                                print(f"\n{unit['name']} (Tier {unit['tier']})")
                                if unit['items']:
                                    print("Items:")
                                    for item in unit['items']:
                                        print(f"- {item}")
                                        #print first one only
                                        print(f"...")
                                        break
                                #print first one only   
                                print(f"...")
                                break
                        
                        clipboard_text.extend([
                            f"\nPlayer: {player_data.get('name', 'N/A')} #{player_data.get('tag', 'N/A')}",
                            f"Placement: {player_data.get('placement', 'N/A')}",
                            f"Level: {player_data.get('level', 'N/A')}",
                            f"Stage: {player_data.get('stage', 'N/A')}",
                            f"Damage Done: {player_data.get('damage_done', 'N/A')}",
                            f"Board Value: {player_data.get('board_value', 'N/A')}"
                        ])
                else:
                    print(f"Unexpected players data type: {type(players_data)}")
                    print(f"Players data content: {players_data}")
        return clipboard_text

    def display_personal_summary(self, recent_match, clipboard_text):
        """Display personal summary data if available"""
        if 'personal_summary' in recent_match:
            print("\nPERSONAL SUMMARY:")
            summary_data = recent_match['personal_summary']
            if summary_data['positive']:
                print("\nPositive:")
                for tag in summary_data['positive']:
                    print(f"- {tag}")
                clipboard_text.extend(["\nPositive:"] + [f"- {tag}" for tag in summary_data['positive']])
            if summary_data['negative']:
                print("\nNegative:")
                for tag in summary_data['negative']:
                    print(f"- {tag}")
                clipboard_text.extend(["\nNegative:"] + [f"- {tag}" for tag in summary_data['negative']])
            if summary_data['ap']:
                print("\nAP:")
                for tag in summary_data['ap']:
                    print(f"- {tag}")
                clipboard_text.extend(["\nAP:"] + [f"- {tag}" for tag in summary_data['ap']])
        return clipboard_text

    def display_stage_breakdown(self, recent_match, clipboard_text):
        """Display stage breakdown data if available"""
        if 'stage_breakdown' in recent_match:
            print("\nSTAGE BREAKDOWN:")
            for stage in recent_match['stage_breakdown']:
                print(f"\n{stage['name']}:")
                print(f"Win Rate: {stage['win_rate']}")
                if 'mvp' in stage:
                    mvp = stage['mvp']
                    print(f"MVP: {mvp['name']}")
                    print(f"Avg Damage/Round: {mvp['avg_damage']}")
                    print(f"Max Damage/Round: {mvp['max_damage']}")
                    print(f"Win Rate: {mvp['win_rate']}")
                clipboard_text.extend([
                    f"\n{stage['name']}:",
                    f"Win Rate: {stage['win_rate']}",
                    f"MVP: {mvp['name']}",
                    f"Avg Damage/Round: {mvp['avg_damage']}",
                    f"Max Damage/Round: {mvp['max_damage']}",
                    f"Win Rate: {mvp['win_rate']}"
                ])
        return clipboard_text

    def display_economy_data(self, recent_match, clipboard_text):
        """Display economy data if available"""
        if 'economy' in recent_match:
            print("\nECONOMY:")
            economy_data = recent_match['economy']
            print(f"Interest: {economy_data.get('interest', 'N/A')}")
            print(f"Streaks: {economy_data.get('streaks', 'N/A')}")
            print(f"Wins: {economy_data.get('wins', 'N/A')}")
            print(f"Best Streak: {economy_data.get('best streak', 'N/A')}")
            print(f"Rerolls: {economy_data.get('rerolls', 'N/A')}")
            print(f"XP Bought: {economy_data.get('xp bought', 'N/A')}")
            clipboard_text.extend([
                "\nECONOMY:",
                f"Interest: {economy_data.get('interest', 'N/A')}",
                f"Streaks: {economy_data.get('streaks', 'N/A')}",
                f"Wins: {economy_data.get('wins', 'N/A')}",
                f"Best Streak: {economy_data.get('best streak', 'N/A')}",
                f"Rerolls: {economy_data.get('rerolls', 'N/A')}",
                f"XP Bought: {economy_data.get('xp bought', 'N/A')}"
            ])
        return clipboard_text

    def display_planning_data(self, recent_match, clipboard_text):
        """Display planning phase data if available"""
        if 'planning' in recent_match:
            print("\nPLANNING PHASE:")
            planning_data = recent_match['planning']
            print(f"Scouting Time: {planning_data.get('scouting time', 'N/A')}")
            print(f"Actions/Round: {planning_data.get('actions/round', 'N/A')}")
            print(f"Repositions: {planning_data.get('repositions', 'N/A')}")
            print(f"Board Changes: {planning_data.get('board changes', 'N/A')}")
            clipboard_text.extend([
                "\nPLANNING PHASE:",
                f"Scouting Time: {planning_data.get('scouting time', 'N/A')}",
                f"Actions/Round: {planning_data.get('actions/round', 'N/A')}",
                f"Repositions: {planning_data.get('repositions', 'N/A')}",
                f"Board Changes: {planning_data.get('board changes', 'N/A')}"
            ])
        return clipboard_text

    def display_key_rounds(self, recent_match, clipboard_text):
        """Display key rounds data if available"""
        if 'key_rounds' in recent_match:
            print("\nKEY ROUNDS:")
            for round_data in recent_match['key_rounds']:
                print(f"\n{round_data['title']}:")
                print(f"Opponent: {round_data['opponent']}")
                if 'hp_loss' in round_data:
                    print(f"HP Loss: {round_data['hp_loss']}")
                if 'win_chance' in round_data:
                    print(f"Win Chance: {round_data['win_chance']}")
                print(f"Stage: {round_data['stage']}")
                print("Units:")
                for unit in round_data['units']:
                    print(f"- {unit['name']} (Tier {unit['tier']})")
                
                clipboard_text.extend([
                    f"\n{round_data['title']}:",
                    f"Opponent: {round_data['opponent']}"
                ])
                if 'hp_loss' in round_data:
                    clipboard_text.append(f"HP Loss: {round_data['hp_loss']}")
                if 'win_chance' in round_data:
                    clipboard_text.append(f"Win Chance: {round_data['win_chance']}")
                clipboard_text.extend([
                    f"Stage: {round_data['stage']}",
                    "Units:"
                ])
                for unit in round_data['units']:
                    clipboard_text.append(f"- {unit['name']} (Tier {unit['tier']})")
        return clipboard_text

    def display_timeline(self, recent_match, clipboard_text):
        if 'timeline' in recent_match:
            print("\nTIMELINE:")
            timeline_data = recent_match['timeline']
            
            if isinstance(timeline_data, dict):
                # Handle dictionary format timeline
                for stage_key, stage_data in timeline_data.items():
                    if isinstance(stage_data, dict):
                        print(f"\nStage: {stage_key}")
                        if 'units' in stage_data:
                            print("Board:")
                            board_text = ""
                            for unit in stage_data['units']:
                                unit_text = f"- {unit['name']} ({unit['tier']})"
                                if 'items' in unit and unit['items']:
                                    unit_text += " items: " + ', '.join(unit['items'])
                                print(unit_text)
                                board_text+=(unit_text)

                        if 'bench_items' in stage_data:
                            item_bench_text = ""
                            print("Bench Items:")
                            for item in stage_data['bench_items']:
                                print(f"- {item}")
                                item_bench_text+=(f"- {item}")

                        if 'upgrades' in stage_data:
                            upgrades_text = ""
                            print("Upgrades:")
                            for upgrade in stage_data['upgrades']:
                                print(f"- {upgrade['name']} ({upgrade['tier']})")
                                upgrades_text+=(f"- {upgrade['name']} ({upgrade['tier']})")

                        print(f"Level: {stage_data.get('level', 'N/A')}")
                        print(f"Gold: {stage_data.get('gold', 'N/A')}")
                        print(f"Rerolls: {stage_data.get('rerolls', 'N/A')}")
                        print(f"HP: {stage_data.get('hp', 'N/A')}")
                        print(f"Position: {stage_data.get('position', 'N/A')}")
                        print(f"Damage: {stage_data.get('damage', 'N/A')}")
                        
                        # Add to clipboard text
                        clipboard_text.extend([
                            f"\nStage: {stage_key}",
                            f"Units:",
                            f"{board_text}",
                            f"Bench Items:",
                            f"{item_bench_text}",
                            f"Upgrades:",
                            f"{upgrades_text}",
                            f"Level: {stage_data.get('level', 'N/A')}",
                            f"Gold: {stage_data.get('gold', 'N/A')}"
                            f"Rerolls: {stage_data.get('rerolls', 'N/A')}",
                            f"HP: {stage_data.get('hp', 'N/A')}",
                            f"Position: {stage_data.get('position', 'N/A')}",
                            f"Damage: {stage_data.get('damage', 'N/A')}"
                        ])
            else:
                print("No timeline data found")
        return clipboard_text

    def display_match_history(self, matches, write_file=True):
        if not matches:
            print("No matches found")
            return

        print("\n=== Recent Ranked TFT Matches ===")
        
        # Get the most recent match
        recent_match = matches[0]
        clipboard_text = []
        
        print(f"Match ID: {recent_match['match_id']}")
        clipboard_text.append(f"Match ID: {recent_match['match_id']}")
        
        # Display players summary data
        clipboard_text = self.display_players_summary(recent_match, clipboard_text)
        
        # Display average opponent rank
        clipboard_text = self.display_avg_opponent_rank(recent_match, clipboard_text)
        
        # Display players data
        clipboard_text = self.display_players_data(recent_match, clipboard_text)
        
        # Display personal summary data
        clipboard_text = self.display_personal_summary(recent_match, clipboard_text)
        
        # Display stage breakdown
        clipboard_text = self.display_stage_breakdown(recent_match, clipboard_text)
        
        # Display economy data
        clipboard_text = self.display_economy_data(recent_match, clipboard_text)
        
        # Display planning phase data
        clipboard_text = self.display_planning_data(recent_match, clipboard_text)
        
        # Display key rounds data
        clipboard_text = self.display_key_rounds(recent_match, clipboard_text)
        
        # Display timeline data
        clipboard_text = self.display_timeline(recent_match, clipboard_text)
        
        # Copy to clipboard
        pyperclip.copy('\n'.join(clipboard_text))
        print("\nData from most recent match has been copied to clipboard!")
        
        # Write to text file if write_file is True
        if write_file:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"tft_match_{timestamp}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(clipboard_text))
                print(f"\nMatch data has been written to {filename}")
            except Exception as e:
                print(f"Error writing to file: {e}")
        
        print("-" * 50)

def get_riot_id():
    """Get Riot ID from .env file or user input"""
    load_dotenv()
    riot_id = os.getenv('RIOT_ID')
    region = os.getenv('REGION', 'tw')
    
    if riot_id:
        print(f"Using Riot ID from .env: {riot_id}")
        print(f"Using region from .env: {region}")
        return riot_id, region
    
    # If not found in .env, get from user input
    riot_id = input("Enter Riot ID (format: name#tag): ").strip()
    region = input("Enter region (e.g., tw, na, euw): ").strip().lower()
    return riot_id, region

async def main():
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Fetch TFT match data')
        parser.add_argument('--no-file', action='store_true', help='Do not write match data to file')
        args = parser.parse_args()
        
        tft = TFTTimeline()
        
        # Get Riot ID and region
        riot_id, region = get_riot_id()
        
        print(f"\nFetching data for {riot_id}...")
        matches = await tft.get_player_data(riot_id, region)
        
        if matches:
            tft.display_match_history(matches, write_file=not args.no_file)
        else:
            print("No matches found or error occurred")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 