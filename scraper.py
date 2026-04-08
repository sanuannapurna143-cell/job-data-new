import cloudscraper
from bs4 import BeautifulSoup
import json
import time
import re
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# --- ୧. ୟୁଜର୍ ପାଇଁ ସୂଚନା ---
# ଏହି କୋଡ୍ Jobs, Results, Admit Cards, Education ସବୁକୁ ସ୍କ୍ରାପ୍ କରିବ।
# Incremental Logic ଲଗାଯାଇଛି ଯାହାଦ୍ୱାରା ପୁରୁଣା ଡାଟା ପୁଣି ସ୍କ୍ରାପ୍ ହେବନି।

def get_urgency(last_date_str):
    """ଚାକିରି ଶେଷ ହେବାକୁ କେତେ ଦିନ ବାକି ଅଛି ଜାଣିବା ପାଇଁ"""
    try:
        match = re.search(r'(\d{2}-\d{2}-\d{4})', last_date_str)
        if match:
            last_date = datetime.strptime(match.group(1), '%d-%m-%Y').date()
            days_left = (last_date - datetime.now().date()).days
            if days_left <= 3: return "High"
            if days_left <= 7: return "Medium"
        return "Normal"
    except:
        return "Normal"

def get_inner_details(scraper, link):
    """ଭିତର ପେଜ୍‌ରୁ ସବୁ ଡିଟେଲ୍ସ (Age, Fee, Syllabus) ଆଣିବା ପାଇଁ"""
    details = {
        "full_title": "Not Available", "total_posts": "Not Available",
        "salary": "Not Available", "age_limit": "Not Available", 
        "application_fee": "Not Available", "apply_mode": "Not Available",
        "selection_process": "Not Available", "syllabus": "Not Available",
        "qualification": "Not Available", "official_website": "Not Available",
        "official_notification": "Not Available"
    }
    if not link or 'freejobalert.com' not in link: return details
    
    try:
        time.sleep(0.5) # Fast Scraping
        response = scraper.get(link, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ତୁମର ସେହି ସବୁ ପୁରୁଣା ଡିଟେଲ୍ ପାର୍ସିଂ ଲଜିକ୍ (Deep Scan)
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                text = row.text.lower()
                cols = row.find_all(['td', 'th'])
                if len(cols) < 2: continue
                val = cols[1].text.replace('\n', ' ').strip()

                if 'post name' in text: details['full_title'] = val
                elif 'age limit' in text: details['age_limit'] = val
                elif 'salary' in text or 'pay scale' in text: details['salary'] = val
                elif 'qualification' in text: details['qualification'] = val
                elif 'application fee' in text: details['application_fee'] = val
                elif 'selection process' in text: details['selection_process'] = val
                elif 'apply mode' in text: details['apply_mode'] = val
                elif 'syllabus' in text: details['syllabus'] = row.text.strip()

        # Link Extraction
        for a in soup.find_all('a', href=True):
            href = a['href']
            txt = a.text.lower()
            if 'official website' in txt: details['official_website'] = href
            elif 'notification' in txt and '.pdf' in href: details['official_notification'] = href

    except: pass
    return details

def process_row(args):
    """Thread Worker: ପ୍ରତିଟି ଚାକିରିକୁ ପ୍ରୋସେସ୍ କରିବ"""
    scraper, row_data = args
    p_date, board, title, qual, l_date, link = row_data
    
    # ଡିଟେଲ୍ସ ଆଣିବା
    inner = get_inner_details(scraper, link)
    
    return {
        "date": p_date,
        "board": board,
        "title": inner['full_title'] if inner['full_title'] != "Not Available" else title,
        "qualification": inner['qualification'] if len(inner['qualification']) > len(qual) else qual,
        "last_date": l_date,
        "urgency": get_urgency(l_date),
        "total_posts": inner['total_posts'],
        "salary": inner['salary'],
        "age_limit": inner['age_limit'],
        "application_fee": inner['application_fee'],
        "selection_process": inner['selection_process'],
        "apply_mode": inner['apply_mode'],
        "syllabus": inner['syllabus'],
        "official_website": inner['official_website'],
        "official_notification": inner['official_notification']
    }

def scrape_master(url, filename):
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows'})
    print(f"\n⚡ ସ୍କାନିଂ ଆରମ୍ଭ: {filename}")

    # ପୁରୁଣା ଡାଟା ଚେକ୍ କରିବା (Incremental Update)
    existing_titles = set()
    existing_data = []
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
            existing_titles = {j['title'] for j in existing_data}

    try:
        response = scraper.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        rows_to_scrape = []
        tables = soup.find_all('table')
        for table in tables:
            # FreeJobAlert ର ସବୁ ପେଜ୍‌ରେ 'Board' କିମ୍ବା 'Organization' ଥାଏ
            if any(k in table.text for k in ['Board', 'Organization', 'Update Title']):
                for tr in table.find_all('tr')[1:]:
                    cols = tr.find_all('td')
                    if len(cols) >= 3:
                        # ଡାଟା ବାହାର କରିବା (Handling different table structures)
                        d = cols[0].text.strip()
                        b = cols[1].text.strip()
                        t = cols[2].text.strip()
                        q = cols[3].text.strip() if len(cols) > 3 else "N/A"
                        l = cols[5].text.strip() if len(cols) > 5 else "N/A"
                        lnk = cols[-1].find('a')['href'] if cols[-1].find('a') else ""

                        # ଯଦି ଟାଇଟଲ୍ ନୂଆ, ତେବେ ଲିଷ୍ଟ୍‌ରେ ଯୋଡ଼
                        if t not in existing_titles:
                            rows_to_scrape.append((d, b, t, q, l, lnk))
                break

        # ନୂଆ ଡାଟାକୁ Threading ସହ ସ୍କ୍ରାପ୍ କରିବା
        new_jobs = []
        if rows_to_scrape:
            print(f"  -> {len(rows_to_scrape)} ଟି ନୂଆ ଅପଡେଟ୍ ମିଳିଲା।")
            with ThreadPoolExecutor(max_workers=10) as executor:
                new_jobs = list(executor.map(process_row, [(scraper, r) for r in rows_to_scrape]))
        else:
            print("  -> କିଛି ନୂଆ ଅପଡେଟ୍ ନାହିଁ।")

        # ପୁରୁଣା + ନୂଆ ଡାଟାକୁ ମିଶାଇ ସେଭ୍ କରିବା (Last 50 items)
        final_data = new_jobs + existing_data
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(final_data[:60], f, ensure_ascii=False, indent=4)
        
    except Exception as e:
        print(f"❌ Error in {filename}: {e}")

# --- ସବୁ କାଟେଗୋରୀର ଲିଷ୍ଟ୍ ---
all_sources = {
    "odisha_jobs.json": "https://www.freejobalert.com/odisha-government-jobs/",
    "central_jobs.json": "https://www.freejobalert.com/government-jobs/",
    "bank_jobs.json": "https://www.freejobalert.com/bank-jobs/",
    "results.json": "https://www.freejobalert.com/exam-results/",
    "admit_cards.json": "https://www.freejobalert.com/admit-card/",
    "answer_keys.json": "https://www.freejobalert.com/answer-keys/",
    "education_updates.json": "https://www.freejobalert.com/new-edu-updates/",
    "syllabus.json": "https://www.freejobalert.com/syllabus/"
}

# ରନ୍ କରିବା
for file, url in all_sources.items():
    scrape_master(url, file)
    time.sleep(5) # ଛୋଟ ବିଶ୍ରାମ

print("\n🙏 ସବୁ କାମ ସରିଲା ଭାଇ! ଜଗନ୍ନାଥ ସହାୟ ହେବେ।")
