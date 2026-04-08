import cloudscraper
from bs4 import BeautifulSoup
import json
import os
import time

def scrape_fast_updates(url, filename):
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows'})
    
    # ୧. ପୁରୁଣା ଡାଟା ଲୋଡ୍ କରିବା
    existing_updates = []
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                existing_updates = json.load(f)
        except: pass

    try:
        print(f"\n🔎 Scanning Full Page: {url}")
        response = scraper.get(url, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        all_new_data = []
        tables = soup.find_all('table') # ସବୁ ଟେବୁଲ୍ ଖୋଜିବ

        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2: continue
            
            header_text = table.text.lower()
            # ଯଦି ଟେବୁଲ୍ ଭିତରେ ଏହି ଶବ୍ଦ ଅଛି, ତେବେ ଡାଟା ଟାଣିବ
            if any(k in header_text for k in ['board', 'result', 'admit card', 'education', 'syllabus', 'answer key']):
                
                for row in rows[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        # ଡାଟା ବାହାର କରିବା
                        date_val = cols[0].text.strip()
                        board_val = cols[1].text.strip()
                        title_val = cols[2].text.strip()
                        
                        # ଲିଙ୍କ୍ ଖୋଜିବା
                        link_tag = cols[2].find('a') or cols[-1].find('a')
                        link = link_tag['href'] if link_tag else ""

                        # 📍 "Get Details" ସମସ୍ୟା ଠିକ୍ କରିବା Logic
                        final_title = title_val
                        final_board = board_val

                        # ଯଦି ଟାଇଟଲ୍ ଖାଲି ଅଛି କିମ୍ବା "Get Details" ଲେଖାଅଛି
                        if any(x in title_val.lower() for x in ["click", "details", "here"]) or len(title_val) < 5:
                            final_title = board_val
                            final_board = "Update"

                        if not final_title or "post name" in final_title.lower():
                            continue

                        all_new_data.append({
                            "date": date_val,
                            "board": final_board,
                            "title": final_title,
                            "link": link
                        })
                # ଏଠାରେ break ଲଗାଯାଇନି, ଯାହାଦ୍ୱାରା ସେ ସବୁ ଟେବୁଲ୍ ପଢ଼ିବ

        if all_new_data:
            # Duplicate ହଟାଇବା
            existing_titles = {j.get('title') for j in existing_updates}
            unique_new = [n for n in all_new_data if n['title'] not in existing_titles]
            
            # ନୂଆ ଡାଟାକୁ ଉପରେ ରଖିବା
            final_json_data = unique_new + existing_updates
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(final_json_data[:150], f, ensure_ascii=False, indent=4)
            print(f"  ✅ Success! {len(unique_new)} new items added to {filename}")
        else:
            print(f"  ✅ No new data found for {filename}")

    except Exception as e:
        print(f"  ❌ Error: {e}")

# --- ସବୁ ୫ଟି ଯାକ ସେକ୍ସନ୍ ---
if __name__ == "__main__":
    sources = {
        "results.json": "https://www.freejobalert.com/exam-results/",
        "admit_cards.json": "https://www.freejobalert.com/admit-card/",
        "education.json": "https://www.freejobalert.com/new-edu-updates/",
        "answer_keys.json": "https://www.freejobalert.com/answer-keys/",
        "syllabus.json": "https://www.freejobalert.com/syllabus/"
    }
    
    for file_name, web_url in sources.items():
        scrape_fast_updates(web_url, file_name)
        time.sleep(5)
