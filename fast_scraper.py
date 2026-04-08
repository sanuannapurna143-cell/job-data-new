import cloudscraper
from bs4 import BeautifulSoup
import json
import os
import time

# ଏହି ଫଙ୍କସନ୍ ରେଜଲ୍ଟ, ଆଡମିଟ୍ କାର୍ଡ ଇତ୍ୟାଦି ପାଇଁ ଡାଟା ଟାଣିବ
def scrape_fast_updates(url, filename):
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
    )
    
    # ୧. ପୁରୁଣା ଡାଟା ଲୋଡ୍ କରିବା (ଯେମିତି କି ଡାଟା ଡିଲିଟ୍ ହେବନି)
    existing_updates = []
    existing_titles = set()
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    existing_updates = data
                    for item in existing_updates:
                        existing_titles.add(item.get('title', ''))
        except Exception as e:
            print(f"  ⚠ ପୁରୁଣା ଫାଇଲ୍ ପଢିବାରେ ଏରର୍: {e}")

    try:
        print(f"\n⚡ ସ୍କାନିଂ: {filename}...")
        response = scraper.get(url, timeout=20)
        
        if response.status_code != 200:
            print(f"  ❌ ପେଜ୍ ଖୋଲିଲାନି! Status: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        new_found_data = []
        
        # ୨. ଟେବୁଲ୍ ଖୋଜିବା ଲଜିକ୍
        tables = soup.find_all('table')

        for table in tables:
            header_text = table.text.lower()
            # ରେଜଲ୍ଟ ପେଜ୍‌ର ଟେବୁଲ୍ କୁ ଚିହ୍ନିବା
            if any(k in header_text for k in ['post date', 'result', 'admit card', 'update']):
                rows = table.find_all('tr')
                
                for row in rows[1:]: # Header ଛାଡି
                    cols = row.find_all('td')
                    
                    # ରେଜଲ୍ଟ/ଆଡମିଟ୍ କାର୍ଡ ଟେବୁଲ୍ ରେ ସାଧାରଣତଃ ୩-୪ଟି କଲମ୍ ଥାଏ
                    if len(cols) >= 3:
                        date_str = cols[0].text.strip()
                        board = cols[1].text.strip()
                        title_col = cols[2]
                        title = title_col.text.strip()
                        
                        # ଲିଙ୍କ୍ ଖୋଜିବା
                        link = ""
                        a_tag = title_col.find('a')
                        if a_tag and 'href' in a_tag.attrs:
                            link = a_tag['href']

                        # ଯଦି ଟାଇଟଲ୍ ନୂଆ, ତେବେ ଯୋଡ଼
                        if title and title not in existing_titles:
                            new_found_data.append({
                                "date": date_str,
                                "board": board,
                                "title": title,
                                "link": link
                            })
                
                if new_found_data: break # ଡାଟା ମିଳିଗଲେ ପରବର୍ତ୍ତୀ ଟେବୁଲ୍ କୁ ଯିବନି

        # ୩. ନୂଆ + ପୁରୁଣା ମିଶାଇ ସେଭ୍ କରିବା
        if new_found_data:
            print(f"  ✅ {len(new_found_data)} ଟି ନୂଆ ଅପଡେଟ୍ ମିଳିଲା।")
            final_data = new_found_data + existing_updates
            # ସର୍ବାଧିକ ୧୦୦ ଟି ଡାଟା ରଖିବା
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(final_data[:100], f, ensure_ascii=False, indent=4)
            print(f"  💾 {filename} ଅପଡେଟ୍ ହୋଇଗଲା।")
        else:
            print("  ✅ କିଛି ନୂଆ ଡାଟା ନାହିଁ।")

    except Exception as e:
        print(f"  ❌ Error: {e}")

# --- ସବୁ ଲିଙ୍କ୍ ର ଲିଷ୍ଟ୍ (ଏଇଟା ହିଁ ସ୍କ୍ରାପର୍ ର ମେନ୍ କାମ) ---
if __name__ == "__main__":
    update_sources = {
        "results.json": "https://www.freejobalert.com/exam-results/",
        "admit_cards.json": "https://www.freejobalert.com/admit-card/",
        "answer_keys.json": "https://www.freejobalert.com/answer-keys/",
        "syllabus.json": "https://www.freejobalert.com/syllabus/",
        "education.json": "https://www.freejobalert.com/new-edu-updates/"
    }

    for file, url in update_sources.items():
        scrape_fast_updates(url, file)
        time.sleep(5) # Cloudflare ସୁରକ୍ଷା ପାଇଁ ବିଶ୍ରାମ
