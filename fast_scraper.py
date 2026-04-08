import cloudscraper
from bs4 import BeautifulSoup
import json
import os
import time

def scrape_fast_updates(url, filename):
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows'})
    
    existing_updates = []
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                existing_updates = json.load(f)
        except: pass

    try:
        print(f"\n⚡ Scanning: {filename}...")
        response = scraper.get(url, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        new_updates = []
        tables = soup.find_all('table')

        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2: continue
            
            header_text = table.text.lower()
            # ସବୁ ପ୍ରକାରର ଅପଡେଟ୍ ଟେବୁଲ୍ କୁ ଚିହ୍ନିବା ପାଇଁ logic
            if any(k in header_text for k in ['board', 'result', 'admit card', 'education', 'syllabus', 'answer key']):
                
                for row in rows[1:]:
                    cols = row.find_all('td')
                    
                    if len(cols) >= 3:
                        # ଡାଟା ଟାଣିବା
                        raw_date = cols[0].text.strip()
                        raw_board = cols[1].text.strip()
                        raw_title = cols[2].text.strip()
                        
                        # ଲିଙ୍କ୍ ଖୋଜିବା
                        link_tag = cols[2].find('a') or cols[-1].find('a')
                        link = link_tag['href'] if link_tag else ""

                        # 📍 ପିଲାଙ୍କ ପାଇଁ ଡାଟା କୁ ସଫା କରିବା (Cleaning Logic)
                        final_title = raw_title
                        final_board = raw_board

                        # ଯଦି ଟାଇଟଲ୍ ରେ "Get Details" ଅଛି, ତେବେ Board ନାଁ କୁ ହିଁ Title ବନାଅ
                        if any(x in raw_title.lower() for x in ["click", "details", "here"]) or len(raw_title) < 5:
                            final_title = raw_board
                            final_board = "Update"

                        if not final_title or final_title.lower() == "post name": continue

                        new_updates.append({
                            "date": raw_date,
                            "board": final_board,
                            "title": final_title,
                            "link": link
                        })
                break

        if new_updates:
            existing_titles = {j.get('title') for j in existing_updates}
            filtered_new = [n for n in new_updates if n['title'] not in existing_titles]
            
            final_data = filtered_new + existing_updates
            # ସର୍ବାଧିକ ୧୦୦ ଟି ଡାଟା ରଖିବା
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(final_data[:100], f, ensure_ascii=False, indent=4)
            print(f"  ✅ {len(filtered_new)} New items added to {filename}")
        else:
            print(f"  ✅ {filename} is already up to date.")

    except Exception as e:
        print(f"  ❌ Error in {filename}: {e}")

# --- ଏଠାରେ ଅଛି ପୁରା ଲିଷ୍ଟ (The Full List) ---
if __name__ == "__main__":
    sources = {
        "results.json": "https://www.freejobalert.com/exam-results/",
        "admit_cards.json": "https://www.freejobalert.com/admit-card/",
        "education.json": "https://www.freejobalert.com/new-edu-updates/",
        "answer_keys.json": "https://www.freejobalert.com/answer-keys/",
        "syllabus.json": "https://www.freejobalert.com/syllabus/"
    }
    
    for file, url in sources.items():
        scrape_fast_updates(url, file)
        time.sleep(5) # Cloudflare ବ୍ଲକ୍ ନକରିବା ପାଇଁ
