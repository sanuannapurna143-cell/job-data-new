import cloudscraper
from bs4 import BeautifulSoup
import json
import os
import requests
import urllib3

# 🚨 SSL Verification କୁ ପୁରା ବନ୍ଦ କରିବା ପାଇଁ
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrape_site(url, board_name):
    print(f"📡 Scanning {board_name}...")
    try:
        # User-Agent ସହ ସିଧା Requests ବ୍ୟବହାର କରିବା (Better for Govt Sites)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0 Safari/537.36'}
        
        # verify=False ସହ SSL ଚେକିଂ କୁ ବନ୍ଦ କରାଗଲା
        response = requests.get(url, headers=headers, verify=False, timeout=20)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            updates = []
            links = soup.find_all('a', href=True)
            
            count = 0
            for a in links:
                text = a.text.strip().replace('\n', ' ')
                if len(text) > 15 and any(word in text.lower() for word in ['notice', 'result', 'admit', 'cgl', 'ri', 'amin', 'police', 'constable']):
                    href = a['href']
                    full_link = href if href.startswith('http') else url.split('/Public')[0] + href
                    updates.append({"board": board_name, "title": text, "link": full_link})
                    count += 1
                if count >= 10: break
            return updates
        else:
            print(f"  ❌ {board_name} Status Code: {response.status_code}")
            return []
    except Exception as e:
        print(f"  ❌ {board_name} Error: {str(e)}")
        return []

if __name__ == "__main__":
    mega_data = []
    
    # ୧. OSSC
    mega_data += scrape_site("https://www.ossc.gov.in/Public/Pages/Whats_new.aspx", "OSSC")
    # ୨. OSSSC
    mega_data += scrape_site("https://www.osssc.gov.in/Public/OSSSC/Default.aspx", "OSSSC")
    # ୩. OPSC
    mega_data += scrape_site("https://opsc.gov.in/Public/OPSC/Default.aspx", "OPSC")
    # ୪. Police
    mega_data += scrape_site("https://odishapolice.gov.in/", "Police")

    filename = "odisha_official_updates.json"
    
    # ଡାଟା ମିଳୁ କି ନମିଳୁ, ଫାଇଲ୍ ଟିଏ ବନାଇବା (ଯେମିତି କି GitHub Actions ସେଭ୍ କରିପାରିବ)
    if not mega_data:
        mega_data = [{"board": "System", "title": "No new notifications for now.", "link": "#"}]

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(mega_data[:100], f, ensure_ascii=False, indent=4)
        
    print(f"\n✅ {filename} Successfully Saved with {len(mega_data)} items!")
