import cloudscraper
from bs4 import BeautifulSoup
import json
import time
import re

def get_inner_details(scraper, link):
    details = {
        "full_title": "Not Available",
        "total_posts": "Not Available",
        "salary": "Not Available",
        "age_limit": "Not Available", 
        "application_fee": "Not Available",
        "apply_mode": "Not Available",
        "selection_process": "Not Available", # ନୂଆ: ପିଲାଙ୍କ ପାଇଁ ସିଲେକ୍ସନ୍ ପ୍ରୋସେସ୍
        "syllabus": "Not Available",
        "qualification": "Not Available", 
        "official_website": "Not Available",
        "official_notification": "Not Available"
    }
    if not link:
        return details
    
    try:
        time.sleep(5) 
        response = scraper.get(link)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        page_text = soup.text.lower()
        
        # ୧. ମଣିଷ ଭଳିଆ ଟେବୁଲ୍ ପଢିବା (Vertical Column Tracking for Salary, Qual, Fee)
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if not rows: continue
            
            # ହେଡିଂ କଲମ୍ ନମ୍ବର ଖୋଜିବା
            headers = [th.text.lower().strip() for th in rows[0].find_all(['th', 'td'])]
            salary_idx, qual_idx, fee_idx = -1, -1, -1
            
            for i, h in enumerate(headers):
                if 'salary' in h or 'stipend' in h or 'pay' in h or 'remuneration' in h: salary_idx = i
                if 'qualification' in h or 'degree' in h: qual_idx = i
                if 'fee' in h: fee_idx = i
                
            # ଯଦି ହେଡିଂ ମିଳିଲା, ତେବେ ତଳ ଧାଡ଼ିରୁ ସଠିକ୍ ଡାଟା ଆଣିବା (ହେଡିଂ କୁ ଇଗନୋର୍ କରି)
            if len(rows) > 1 and (salary_idx != -1 or qual_idx != -1 or fee_idx != -1):
                for row in rows[1:]:
                    cols = row.find_all('td')
                    if not cols: continue
                    
                    if salary_idx != -1 and salary_idx < len(cols) and details['salary'] == "Not Available":
                        val = cols[salary_idx].text.strip()
                        if val and 'post name' not in val.lower() and 'stipend' not in val.lower():
                            details['salary'] = val.replace('\n', ' ')
                            
                    if qual_idx != -1 and qual_idx < len(cols) and details['qualification'] == "Not Available":
                        val = cols[qual_idx].text.strip()
                        if val and 'post name' not in val.lower():
                            details['qualification'] = val.replace('\n', ' ')
                            
                    if fee_idx != -1 and fee_idx < len(cols) and details['application_fee'] == "Not Available":
                        val = cols[fee_idx].text.strip()
                        if val and 'category' not in val.lower():
                            details['application_fee'] = val.replace('\n', ' ')

        # ୨. ସାଧାରଣ ବାମ-ଡାହାଣ ପଢିବା (ଅନ୍ୟାନ୍ୟ ଜିନିଷ ପାଇଁ)
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                text = row.text.lower()
                row_clean = row.text.replace('\n', ' ').strip()
                cols = row.find_all(['td', 'th'])
                
                if 'post name' in text and details['full_title'] == "Not Available":
                    if len(cols) >= 2: details['full_title'] = cols[1].text.strip()
                
                elif 'apply mode' in text and details['apply_mode'] == "Not Available":
                    if len(cols) >= 2: details['apply_mode'] = cols[1].text.strip()
                    else:
                        val = row_clean.lower().replace('apply mode', '').replace(':', '').strip()
                        details['apply_mode'] = val.title() if val else "Not Available"

                elif ('qualification' in text or 'educational qualification' in text) and 'fee' not in text and details['qualification'] == "Not Available":
                    if len(cols) >= 2: details['qualification'] = cols[1].text.replace('\n', ' ').strip()
                    else: details['qualification'] = row_clean

                elif 'age limit' in text and details['age_limit'] == "Not Available":
                    if len(cols) >= 2: details['age_limit'] = cols[1].text.replace('\n', ' ').strip()
                    else: details['age_limit'] = row_clean
                        
                elif ('no of posts' in text or 'total vacancy' in text) and details['total_posts'] == "Not Available":
                    if len(cols) >= 2: details['total_posts'] = cols[1].text.replace('\n', ' ').strip()
                        
                elif ('salary' in text or 'scale of pay' in text or 'pay scale' in text) and details['salary'] == "Not Available":
                    if len(cols) >= 2: details['salary'] = cols[1].text.replace('\n', ' ').strip()

                elif 'syllabus' in text and details['syllabus'] == "Not Available":
                    details['syllabus'] = row_clean
                    
                if details['application_fee'] == "Not Available":
                    if 'application fee' in text or 'examination fee' in text:
                        if len(cols) >= 2: details['application_fee'] = cols[1].text.replace('\n', ' ').strip()

        # ୩. ହେଡିଂ ବ୍ଲକର୍ (ଯଦି କୌଣସି ହେଡିଂ ଧରାପଡିଛି, ତାକୁ କାଟିଦେବ)
        bad_words = ['post name', 'category', 'application fee', 'consolidated stipend', 'consolidated stipend (per month)', 'stipend', 'salary', 'qualification']
        for key in ['salary', 'qualification', 'application_fee']:
            val_lower = details[key].lower().strip()
            if any(bad == val_lower for bad in bad_words):
                details[key] = "Not Available"

        # ୪. Selection Process ଖୋଜିବା (ପିଲାଙ୍କ ପାଇଁ)
        selection_keywords = ['selection process', 'selection procedure']
        for tag in soup.find_all(['h2', 'h3', 'h4', 'strong', 'b', 'p']):
            if any(kw in tag.get_text().lower() for kw in selection_keywords):
                next_ul = tag.find_next(['ul', 'ol'])
                if next_ul:
                    items = [li.get_text(strip=True) for li in next_ul.find_all('li')]
                    if items:
                        details['selection_process'] = ", ".join(items)
                        break

        # ୫. ଅଫିସିଆଲ୍ ଲିଙ୍କ୍
        apply_link_found = False
        for element in soup.find_all(['li', 'tr', 'p']):
            text = element.text.lower()
            a_tags = element.find_all('a')
            for a in a_tags:
                href = a.get('href', '')
                if not href or href == '#' or ('freejobalert.com' in href.lower() and '.pdf' not in href.lower()): continue
                
                if 'apply online' in text or 'apply here' in text: apply_link_found = True
                if 'official website' in text and details['official_website'] == "Not Available": details['official_website'] = href
                elif ('notification' in text or 'detail' in text) and details['official_notification'] == "Not Available": details['official_notification'] = href
                    
        if details['apply_mode'] == "Not Available" or details['apply_mode'] == "":
            if apply_link_found or 'apply online' in page_text: details['apply_mode'] = "Online"
            elif 'walk-in' in page_text or 'walk in' in page_text: details['apply_mode'] = "Walk-in"
            else: details['apply_mode'] = "Offline / Notification ଦେଖନ୍ତୁ"
                    
    except Exception as e:
        pass 
        
    return details

def get_jobs(url, filename):
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    try:
        print(f"ଖୋଜୁଛି: {filename}...")
        response = scraper.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        jobs_data = []
        tables = soup.find_all('table')

        for table in tables:
            if 'Post Date' in table.text or 'Qualification' in table.text:
                rows = table.find_all('tr')
                
                for row in rows[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 6:
                        post_date = cols[0].text.strip()
                        board_name = cols[1].text.strip()
                        post_name = cols[2].text.strip()
                        outer_qualification = cols[3].text.strip() 
                        last_date = cols[5].text.strip()
                        
                        job_link = ""
                        last_col = cols[-1]
                        a_tag = last_col.find('a')
                        if a_tag and 'href' in a_tag.attrs:
                            job_link = a_tag['href']

                        print(f"  -> ଭିତର ପେଜ୍ ଚେକ୍ କରୁଛି: {post_name[:20]}...")
                        inner_data = get_inner_details(scraper, job_link)

                        final_title = inner_data['full_title'] if inner_data['full_title'] != "Not Available" else post_name
                        final_qualification = inner_data['qualification'] if inner_data['qualification'] != "Not Available" else outer_qualification

                        final_total_posts = inner_data['total_posts']
                        if final_total_posts == "Not Available":
                            match = re.search(r'(\d+)\s*(?:post|vacancy|posts|vacancies)', post_name, re.IGNORECASE)
                            if match: final_total_posts = match.group(1)
                            else:
                                match2 = re.search(r'-\s*(\d+)', post_name)
                                if match2: final_total_posts = match2.group(1)

                        jobs_data.append({
                            "date": post_date,
                            "board": board_name,
                            "title": final_title,
                            "qualification": final_qualification, 
                            "last_date": last_date,
                            "total_posts": final_total_posts,
                            "salary": inner_data['salary'],
                            "age_limit": inner_data['age_limit'],
                            "application_fee": inner_data['application_fee'],
                            "selection_process": inner_data['selection_process'], # ପିଲାଙ୍କୁ ଦେଖାଇବା ପାଇଁ ଆଡ୍ ହେଲା
                            "apply_mode": inner_data['apply_mode'], 
                            "syllabus": inner_data['syllabus'],
                            "official_website": inner_data['official_website'],
                            "official_notification": inner_data['official_notification']
                        })
                break 

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(jobs_data, f, ensure_ascii=False, indent=4)
        print(f"ସଫଳତା! {filename} ସେଭ୍ ହୋଇଗଲା।")

    except Exception as e:
        print(f"ଅସୁବିଧା ହେଲା {filename} ରେ: {e}")

job_sources = {
    "odisha_jobs.json": "https://www.freejobalert.com/odisha-government-jobs/",
    "central_jobs.json": "https://www.freejobalert.com/government-jobs/",
    "andhra_jobs.json": "https://www.freejobalert.com/ap-government-jobs/"
}

total_files = len(job_sources)
current = 0

for file, url in job_sources.items():
    current += 1
    get_jobs(url, file)
    
    if current < total_files:
        print("\nରାଜ୍ୟ ବଦଳାଇବା ପୂର୍ବରୁ ୨ ମିନିଟ୍ ବିଶ୍ରାମ...\n")
        time.sleep(120)
