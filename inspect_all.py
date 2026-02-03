import json
from playwright.sync_api import sync_playwright

def inspect_all_keys():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # You can change this URL to test other players later
        url = "https://www.fotmob.com/players/737066/erling-haaland"
        print(f"🌍 Inspecting: {url}")
        page.goto(url)
        page.wait_for_selector("h1")

        next_data = page.evaluate("() => window.__NEXT_DATA__")
        fallback = next_data['props']['pageProps']['fallback']
        
        print(f"\n📂 FOUND {len(fallback)} TOP-LEVEL CACHE KEYS:")
        print("="*60)
        
        for key, data in fallback.items():
            print(f"\n🔑 KEY: {key}")
            
            if isinstance(data, dict):
                # Print the immediate children keys of this object
                keys_list = list(data.keys())
                print(f"   Type: Dictionary with {len(keys_list)} keys")
                print(f"   Children: {keys_list[:10]} {'...' if len(keys_list)>10 else ''}")
                
                # Special check for 'name' to identify player objects
                if 'name' in data:
                    print(f"   👤 Entity Name: {data['name']}")
                    
            elif isinstance(data, list):
                print(f"   Type: List with {len(data)} items")
                if len(data) > 0:
                    print(f"   First Item Keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Primitive Type'}")
            else:
                print(f"   Type: {type(data)} | Value: {str(data)[:50]}...")
                
        print("\n" + "="*60)
        browser.close()

if __name__ == "__main__":
    inspect_all_keys()