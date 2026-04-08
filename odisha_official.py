import cloudscraper
from bs4 import BeautifulSoup
import json
import os
import urllib3

# ସରକାରୀ ୱେବସାଇଟ୍ ରେ SSL ସମସ୍ୟା ଥିଲେ ଇଗନୋର୍ କରିବା ପାଇଁ
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrape_all_odisha(filename):
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows'})
    all_official_updates = []

    print("\n🚀 ଓଡ଼ିଶାର ସମସ୍ତ ଅଫିସିଆଲ୍ ସାଇଟ୍ ସ୍କାନିଂ ଆରମ୍ଭ ହେଲା...\n")

    # ================= ୧. OSSC (ଓଡ଼ିଶା ଷ୍ଟାଫ୍ ସିଲେକ୍ସନ୍) =================
    try:
        print("⚡ Scanning OSSC...")
        ossc_url = "https://www.ossc.gov.in/Public/Pages/Whats_new.aspx"
        response = scraper.get(ossc_url, verify=False, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        count = 0
        for a in soup.find_all('a', href=True):
            text = a.text.strip().replace('\n', ' ').replace('\r', '')
            if len(text) > 15 and any(word in text.lower() for word in ['notice', 'result', 'admit', 'cgl', 'ltr', 'syllabus']):
                link = a['href'] if a['href'].startswith('http') else "https://www.ossc.gov.in" + a['href']
                all_official_updates.append({"board": "OSSC", "title": text, "link": link})
                count += 1
                if count >= 15: break
    except Exception as e:
        print(f"❌ OSSC ରେ ସମସ୍ୟା: {e}")

    # ================= ୨. OSSSC (ସବ୍-ଅର୍ଡିନେଟ୍) =================
    try:
        print("⚡ Scanning OSSSC...")
        osssc_url = "https://www.osssc.gov.in/Public/OSSSC/Default.aspx"
        response = scraper.get(osssc_url, verify=False, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        count = 0
        for a in soup.find_all('a', href=True):
            text = a.text.strip().replace('\n', ' ').replace('\r', '')
            if len(text) > 15 and any(word in text.lower() for word in ['notice', 'result', 'admit', 'cre', 'ri', 'amin', 'forest']):
                link = a['href'] if a['href'].startswith('http') else "https://www.osssc.gov.in" + a['href']
                all_official_updates.append({"board": "OSSSC", "title": text, "link": link})
                count += 1
                if count >= 15: break
    except Exception as e:
        print(f"❌ OSSSC ରେ ସମସ୍ୟା: {e}")

    # ================= ୩. OPSC (ପବ୍ଲିକ୍ ସର୍ଭିସ୍ କମିଶନ୍) =================
    try:
        print("⚡ Scanning OPSC...")
        opsc_url = "https://opsc.gov.in/Public/OPSC/Default.aspx"
        response = scraper.get(opsc_url, verify=False, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        count = 0
        for a in soup.find_all('a', href=True):
            text = a.text.strip().replace('\n', ' ').replace('\r', '')
            if len(text) > 15 and any(word in text.lower() for word in ['notice', 'result', 'admit', 'oas', 'oes', 'medical']):
                link = a['href'] if a['href'].startswith('http') else "https://opsc.gov.in" + a['href']
                all_official_updates.append({"board": "OPSC", "title": text, "link": link})
                count += 1
                if count >= 15: break
    except Exception as e:
        print(f"❌ OPSC ରେ ସମସ୍ୟା: {e}")

    # ================= ୪. Odisha Police (ପୋଲିସ୍ ବିଭାଗ) =================
    try:
        print("⚡ Scanning Odisha Police...")
        police_url = "https://odishapolice.gov.in/"
        response = scraper.get(police_url, verify=False, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        count = 0
        for a in soup.find_all('a', href=True):
            text = a.text.strip().replace('\n', ' ').replace('\r', '')
            if len(text) > 15 and any(word in text.lower() for word in ['recruitment', 'result', 'admit', 'constable', 'battalion', 'sepoy']):
                link = a['href'] if a['href'].startswith('http') else "https://odishapolice.gov.in" + a['href']
                all_official_updates.append({"board": "Odisha Police", "title": text, "link": link})
                count += 1
                if count >= 15: break
    except Exception as e:
        print(f"❌ Odisha Police ରେ ସମସ୍ୟା: {e}")

    # ================= ଡାଟା ସେଭ୍ କରିବା ଲଜିକ୍ =================
    existing_data = []
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except: pass

    if all_official_updates:
        # Title ଚେକ୍ କରି Duplicate ହଟାଇବା
        existing_titles = {j.get('title') for j in existing_data}
        unique_new = [n for n in all_official_updates if n['title'] not in existing_titles]
        
        final_data = unique_new + existing_data
        
        # ସବୁଠୁ ନୂଆ ୧୫୦ ଟି ଡାଟା ରଖିବା
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(final_data[:150], f, ensure_ascii=False, indent=4)
        print(f"\n✅ ସଫଳତା! {len(unique_new)} ଟି ନୂଆ ସରକାରୀ ନୋଟିସ୍ {filename} ରେ ସେଭ୍ ହେଲା।")
    else:
        print("\n✅ କିଛି ନୂଆ ସରକାରୀ ଅପଡେଟ୍ ନାହିଁ।")

if __name__ == "__main__":
    # ଏହି ଗୋଟିଏ JSON ଫାଇଲ୍ ରେ ଓଡ଼ିଶାର ସବୁ ସରକାରୀ ନୋଟିସ୍ ରହିବ
    scrape_all_odisha("odisha_official_updates.json")
