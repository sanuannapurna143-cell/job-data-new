import cloudscraper
from bs4 import BeautifulSoup
import json
import os
import time

def scrape_fast_updates(url, filename):
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    
    # ୧. ପୁରୁଣା ଡାଟା ଲୋଡ୍ କର (Incremental Logic)
    existing_updates = []
    existing_titles = set()
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                existing_updates = json.load(f)
                for item in existing_updates:
                    existing_titles.add(item.get('title', ''))
        except: pass

    try:
        print(f"⚡ Fast Scan: {filename}...")
        response = scraper.get(url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        new_updates = []
        tables = soup.find_all('table')

        for table in tables:
            # FreeJobAlert ର ଅପଡେଟ୍ ଟେବୁଲ୍ ଗୁଡ଼ିକରେ ସାଧାରଣତଃ ଏହି ଶବ୍ଦ ଥାଏ
            if any(k in table.text for k in ['Post Date', 'Update Title', 'Board', 'Exam Date']):
                rows = table.find_all('tr')
                
                for row in rows[1:]:
                    cols = row.find_all('td')
                    
                    # ରେଜଲ୍ଟ ଆଉ ଆଡମିଟ୍ କାର୍ଡ ଟେବୁଲ୍ ରେ ସାଧାରଣତଃ ୩ ରୁ ୫ ଟି କଲମ୍ ଥାଏ
                    if len(cols) >= 3:
                        date_str = cols[0].text.strip()
                        board = cols[1].text.strip()
                        title_col = cols[2]
                        title = title_col.text.strip()
                        
                        # ଡାଉନଲୋଡ୍ ଲିଙ୍କ୍ ଖୋଜିବା
                        link = ""
                        a_tag = title_col.find('a')
                        if a_tag and 'href' in a_tag.attrs:
                            link = a_tag['href']
                        elif len(cols) > 3:
                            # ବେଳେବେଳେ ଲିଙ୍କ୍ ଲାଷ୍ଟ କଲମ୍ ରେ ଥାଏ
                            a_tag_last = cols[-1].find('a')
                            if a_tag_last and 'href' in a_tag_last.attrs:
                                link = a_tag_last['href']

                        # ୨. ଯଦି ଏହି ଅପଡେଟ୍ ଆଗରୁ ଅଛି, ଛାଡ଼ିଦିଅ
                        if title in existing_titles:
                            continue

                        # ନୂଆ ଅପଡେଟ୍ କୁ ଲିଷ୍ଟ୍ ରେ ଯୋଡ଼
                        if link: # ଲିଙ୍କ୍ ଥିଲେ ହିଁ ସେଭ୍ କରିବା
                            new_updates.append({
                                "date": date_str,
                                "board": board,
                                "title": title,
                                "link": link
                            })
                break 

        if new_updates:
            print(f"  -> {len(new_updates)} ଟି ନୂଆ ଆସିଛି!")
        else:
            print("  -> କିଛି ନୂଆ ନାହିଁ।")

        # ୩. ନୂଆ + ପୁରୁଣା ମିଶାଇ ସେଭ୍ କରିବା (ଶେଷ ୧୦୦ ଟି ରଖିବା)
        final_data = new_updates + existing_updates
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(final_data[:100], f, ensure_ascii=False, indent=4)

    except Exception as e:
        print(f"❌ Error in {filename}: {e}")

# ଏଠାରେ କେବଳ Results, Admit Cards ଆଉ Education ର ଲିଙ୍କ୍ ରହିବ
update_sources = {
    "results.json": "https://www.freejobalert.com/exam-results/",
    "admit_cards.json": "https://www.freejobalert.com/admit-card/",
    "answer_keys.json": "https://www.freejobalert.com/answer-keys/",
    "syllabus.json": "https://www.freejobalert.com/syllabus/",
    "education.json": "https://www.freejobalert.com/new-edu-updates/"
}

print("ଦ୍ୱିତୀୟ ସ୍କ୍ରାପର୍ ଆରମ୍ଭ ହେଲା...\n")
for file, url in update_sources.items():
    scrape_fast_updates(url, file)
    time.sleep(2) # ଏଥିପାଇଁ ଖାଲି ୨ ସେକେଣ୍ଡ ବିଶ୍ରାମ ଯଥେଷ୍ଟ
print("\nସବୁ Fast Updates ସରିଗଲା!")
