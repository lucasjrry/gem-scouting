import logging
import traceback
import re
from datetime import datetime
from playwright.sync_api import sync_playwright
from sqlalchemy.orm import Session

# Import our Database tools
from src.database.db import SessionLocal
from src.database.models import Player, Team, Country, PositionGroup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_fotmob_date(date_obj):
    """Robust Date Parser for strings or dicts"""
    if not date_obj: return None
    date_str = date_obj.get('utcTime') if isinstance(date_obj, dict) else date_obj
    if not isinstance(date_str, str): return None
    try:
        clean_str = date_str.replace("Z", "").split(".")[0]
        return datetime.fromisoformat(clean_str).date()
    except:
        return None

def parse_market_text(value_str):
    """Parses '€180M' -> 180000000"""
    if not value_str or not isinstance(value_str, str): return None
    
    try:
        # Remove currency symbols and whitespace
        clean = re.sub(r"[€£$]", "", value_str).strip().upper()
        
        multiplier = 1
        if "M" in clean:
            multiplier = 1_000_000
            clean = clean.replace("M", "")
        elif "K" in clean:
            multiplier = 1_000
            clean = clean.replace("K", "")
            
        return int(float(clean) * multiplier)
    except:
        return None

def get_info_value(info_list, target_labels):
    """
    CRASH-PROOF HELPER:
    Handles cases where 'title' is a Dictionary OR just a String.
    """
    if not info_list: return None
    if isinstance(target_labels, str): target_labels = [target_labels]
    
    targets_lower = [t.lower() for t in target_labels]

    for item in info_list:
        if not isinstance(item, dict): continue
        
        title_data = item.get('title')
        value_data = item.get('value')
        
        match = False
        
        # CASE A: Title is a Dictionary (The complex one)
        if isinstance(title_data, dict):
            key_text = str(title_data.get('key', '')).lower()
            default_text = str(title_data.get('default', '')).lower()
            if key_text in targets_lower or default_text in targets_lower:
                match = True
                
        # CASE B: Title is a String (The one that crashed you)
        elif isinstance(title_data, str):
            if title_data.lower() in targets_lower:
                match = True
        
        if match:
            # Found it! Now extract the value safely
            if isinstance(value_data, dict):
                return value_data.get('fallback')
            return value_data
            
    return None

def map_position_group(fotmob_label: str) -> PositionGroup:
    if not fotmob_label: return None
    label = fotmob_label.lower()
    
    if "goalkeeper" in label: return PositionGroup.GOALKEEPER
    if "centre back" in label: return PositionGroup.CENTRE_BACK
    if "left back" in label or "right back" in label: return PositionGroup.FULL_BACK
    if any(x in label for x in ["defensive midfield", "central midfield"]): return PositionGroup.MIDFIELDER
    if any(x in label for x in ["attacking midfield", "right wing", "left wing", "winger"]): return PositionGroup.WINGER_AM
    if any(x in label for x in ["center forward", "striker", "cf", "st"]): return PositionGroup.STRIKER
    return None

def scrape_and_save_player(url):
    db: Session = SessionLocal()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            logger.info(f"🌍 Navigating to {url}...")
            page.goto(url)
            page.wait_for_selector("h1")

            next_data = page.evaluate("() => window.__NEXT_DATA__")
            fallback = next_data['props']['pageProps']['fallback']
            
            # Find the main player object
            player_data = None
            for key, data in fallback.items():
                if isinstance(data, dict) and 'name' in data:
                     # We look for birthDate or contractEnd to confirm it's the main profile
                     if 'contractEnd' in data or 'birthDate' in data:
                        player_data = data
                        break
            
            if not player_data:
                logger.error("❌ Could not find valid player data.")
                return

            logger.info(f"✅ Extracted Data for: {player_data.get('name')}")

            # --- EXTRACTION ---
            fotmob_id = player_data.get('id')
            name = player_data.get('name')
            birth_date = parse_fotmob_date(player_data.get('birthDate'))
            contract_expiry = parse_fotmob_date(player_data.get('contractEnd'))
            
            # Use our NEW crash-proof librarian
            info_list = player_data.get('playerInformation', [])
            raw_mv_text = get_info_value(info_list, ['Market value', 'Transfer value'])
            current_value = parse_market_text(raw_mv_text)

            # Country
            country_name = "Unknown"
            meta = player_data.get('meta', {})
            if isinstance(meta, dict):
                country_name = meta.get('personJSONLD', {}).get('nationality', {}).get('name')

            primary_team = player_data.get('primaryTeam')
            team_name = primary_team.get('teamName') if isinstance(primary_team, dict) else None

            # --- DB CHECKS ---
            country_obj = db.query(Country).filter(Country.name == country_name).first()
            if not country_obj:
                logger.warning(f"⚠️ Country '{country_name}' not found. Skipping insert.")
                return

            team_obj = db.query(Team).filter(Team.name == team_name).first()
            if not birth_date:
                logger.error("🛑 HALTING: Birth Date is None.")
                return

            # --- UPSERT ---
            player = db.query(Player).filter(Player.fotmob_id == fotmob_id).first()
            if not player:
                logger.info("🆕 Creating new player...")
                player = Player(fotmob_id=fotmob_id)
            else:
                logger.info("🔄 Updating player...")

            player.name = name
            player.birth_date = birth_date
            player.nationality_id = country_obj.id
            player.contract_expiry = contract_expiry
            player.current_market_value = current_value 
            
            if team_obj: player.current_team_id = team_obj.id
            
            # Position Mapping
            pos_desc = player_data.get('positionDescription', {})
            raw_pos_label = None
            if isinstance(pos_desc, dict):
                 primary = pos_desc.get('primaryPosition', {})
                 if isinstance(primary, dict): raw_pos_label = primary.get('label') 
                 if not raw_pos_label:
                     str_pos = pos_desc.get('strPos', {})
                     if isinstance(str_pos, dict): raw_pos_label = str_pos.get('label')

            mapped_group = map_position_group(raw_pos_label)
            if mapped_group: player.position_group = mapped_group
            if raw_pos_label: player.specific_positions = [raw_pos_label]
            
            db.add(player)
            db.commit()
            
            # Display Result
            val_display = f"€{current_value:,.0f}" if current_value else "None"
            logger.info(f"💾 SAVED: {name} | Value: {val_display} | Contract: {contract_expiry}")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    scrape_and_save_player("https://www.fotmob.com/players/737066/erling-haaland")