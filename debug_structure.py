from playwright.sync_api import sync_playwright

def find_paths(data, target_value, path=""):
    """Recursive function to find where a specific value lives in the JSON"""
    if isinstance(data, dict):
        for k, v in data.items():
            new_path = f"{path}.{k}"
            if str(v) == str(target_value):
                print(f"🎯 FOUND '{target_value}' at: {new_path}")
            find_paths(v, target_value, new_path)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            new_path = f"{path}[{i}]"
            if str(item) == str(target_value):
                print(f"🎯 FOUND '{target_value}' at: {new_path}")
            find_paths(item, target_value, new_path)

def debug_fotmob_structure():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("🌍 Navigating to FotMob...")
        page.goto("https://www.fotmob.com/players/737066/erling-haaland")
        page.wait_for_selector("h1")

        # 1. Grab the Data
        next_data = page.evaluate("() => window.__NEXT_DATA__")
        fallback = next_data.get('props', {}).get('pageProps', {}).get('fallback', {})
        
        player_data = None
        for key, data in fallback.items():
            if isinstance(data, dict) and data.get("name") == "Erling Haaland":
                player_data = data
                break
        
        if player_data:
            print("\n🔍 --- HUNTING FOR MISSING DATA ---")
            # We look for known values to find their keys
            find_paths(player_data, "Norway")      # Country
            find_paths(player_data, "195")         # Height (cm)
            find_paths(player_data, "Left")        # Foot
            find_paths(player_data, "2000-07-21")  # Birth Date (ISO format)
            find_paths(player_data, "21 Jul 2000") # Birth Date (Display format)
            
            # Print top-level keys to see what broad categories exist
            print(f"\n📂 Top Level Keys: {list(player_data.keys())}")
        else:
            print("❌ Could not find player object.")

        browser.close()

if __name__ == "__main__":
    debug_fotmob_structure()