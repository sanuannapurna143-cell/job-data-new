import requests
from bs4 import BeautifulSoup
import json
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def clean_url(base_url, link):
    if not link: return ""
    # JavaScript ଲିଙ୍କ୍ ଗୁଡିକୁ ହଟାଇବା (ଏଗୁଡିକ ଆପ୍ ରେ କାମ କରିବନି)
    if "javascript:" in link:
        return base_url 
    
    # Relative paths (..) କୁ ଠିକ୍ କରିବା
    if link.startswith(".."):
        link = link.replace("..", "", 1)
        
    if not link.startswith("http"):
        # Base URL ସହ ଯୋଡିବା
        from urllib.parse import urljoin
        return urljoin(base_url, link)
    
    return link

def scrape_odisha_pro(url, board_name):
    print(f"📡 Scanning {board_name}...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        updates = []
        
        # OSSC/OSSSC ରେ ସାଧାରଣତଃ ଟେବୁଲ୍ ଭିତରେ ଡାଟା ଥାଏ
        for a in soup.find_all('a', href=True):
            text = a.get_text(strip=True).replace('\n', ' ')
            raw_link = a['href']
            
            # କେବଳ ଦରକାରୀ ଖବର ଟାଣିବା
            if len(text) > 15 and any(word in text.lower() for word in ['notice', 'result', 'admit', 'cgl', 'ri', 'amin', 'syllabus']):
                formatted_link = clean_url(url, raw_link)
                
                # ଯଦି ଲିଙ୍କ୍ ଟି ସଠିକ୍ ଭାବେ ବାହାରିଲା
                if formatted_link and formatted_link != url:
                    updates.append({
                        "board": board_name,
                        "title": text,
                        "link": formatted_link
                    })
            if len(updates) >= 15: break
        return updates
    except Exception as e:
        print(f"❌ Error in {board_name}: {e}")
        return []

if __name__ == "__main__":
    final_results = []
    final_results += scrape_odisha_pro("https://www.ossc.gov.in/Public/Pages/Whats_new.aspx", "OSSC")
    final_results += scrape_odisha_pro("https://www.osssc.gov.in/Public/OSSSC/Default.aspx", "OSSSC")
    final_results += scrape_odisha_pro("https://opsc.gov.in/Public/OPSC/Default.aspx", "OPSC")

    # ଡାଟା ସେଭ୍ କରିବା
    with open("odisha_official_updates.json", "w", encoding='utf-8') as f:
        json.dump(final_results, f, ensure_ascii=False, indent=4)
    print("\n✅ Clean Data Saved to odisha_official_updates.json")
