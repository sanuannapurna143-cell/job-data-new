import cloudscraper
from bs4 import BeautifulSoup
import json
import time
import re
import base64  # ନୂଆ ଯୋଡ଼ା ହୋଇଛି (Lock ପାଇଁ)

def get_inner_details(scraper, link):
    details = {
        "full_title": "Not Available",
        "total_posts": "Not Available",
        "salary": "Not Available",
        "age_limit": "Not Available", 
        "application_fee": "Not Available",
        "apply_mode": "Not Available",
        "selection_process": "Not Available", 
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
        
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if not rows: continue
            
            headers = [th.text.lower().strip() for th in rows[0].find_all(['th', 'td'])]
            salary_idx, qual_idx, fee_idx = -1, -1, -1
            
            for i, h in enumerate(headers):
                if 'salary' in h or 'stipend' in h or 'pay' in h or 'remuneration' in h: salary_idx = i
                if 'qualification' in h or 'degree' in h: qual_idx = i
                if 'fee' in h: fee_idx = i
                
            if len(rows) > 1 and (salary_idx != -1 or qual_idx != -1 or fee_idx != -1):
                for row in rows[1:]:
                    cols = row.find_all('td')
                    if not cols: continue
                    
                    if salary_idx != -1 and salary_idx < len(cols):
                        val = cols[salary_idx].text.replace('\n', ' ').strip()
                        if val and 'post name' not in val.lower() and 'stipend' not in val.lower():
                            if details['salary'] == "Not Available" or len(val) > len(details['salary']):
                                details['salary'] = val
                            
                    if qual_idx != -1 and qual_idx < len(cols):
                        val = cols[qual_idx].text.replace('\n', ' ').strip()
                        if val and 'post name' not in val.lower():
                            if details['qualification'] == "Not Available" or len(val) > len(details['qualification']):
                                details['qualification'] = val
                            
                    if fee_idx != -1 and fee_idx < len(cols):
                        val = cols[fee_idx].text.replace('\n', ' ').strip()
                        if val and 'category' not in val.lower():
                            if details['application_fee'] == "Not Available" or len(val) > len(details['application_fee']):
                                details['application_fee'] = val

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

                elif ('qualification' in text or 'educational qualification' in text) and 'fee' not in text:
                    val = cols[1].text.replace('\n', ' ').strip() if len(cols) >= 2 else row_clean
                    if details['qualification'] == "Not Available" or len(val) > len(details['qualification']):
                        details['qualification'] = val

                elif 'age limit' in text:
                    val = cols[1].text.replace('\n', ' ').strip() if len(cols) >= 2 else row_clean
                    if details['age_limit'] == "Not Available" or len(val) > len(details['age_limit']):
                        details['age_limit'] = val
                        
                elif ('no of posts' in text or 'total vacancy' in text or 'vacancy' in text):
                    val = cols[1].text.replace('\n', ' ').strip() if len(cols) >= 2 else ""
                    if val and (details['total_posts'] == "Not Available" or len(val) > len(details['total_posts'])):
                        details['total_posts'] = val
                        
                elif ('salary' in text or 'scale of pay' in text or 'pay scale' in text):
                    val = cols[1].text.replace('\n', ' ').strip() if len(cols) >= 2 else ""
                    if val and (details['salary'] == "Not Available" or len(val) > len(details['salary'])):
                        details['salary'] = val

                elif 'syllabus' in text and details['syllabus'] == "Not Available":
                    details['syllabus'] = row_clean
                    
                if 'application fee' in text or 'examination fee' in text:
                    val = cols[1].text.replace('\n', ' ').strip() if len(cols) >= 2 else ""
                    if val and (details['application_fee'] == "Not Available" or len(val) > len(details['application_fee'])):
                        details['application_fee'] = val

        bad_words = ['post name', 'category', 'application fee', 'consolidated stipend', 'consolidated stipend (per month)', 'stipend', 'salary', 'qualification']
        for key in ['salary', 'qualification', 'application_fee']:
            val_lower = details[key].lower().strip()
            if any(bad == val_lower for bad in bad_words):
                details[key] = "Not Available"

        avoid_words = ['answer key', 'admit card', 'result', 'syllabus 202', 'online form', 'recruitment 202', 'download mobile app', 'telegram', 'whatsapp']

        def extract_full_details(keywords):
            for tag in soup.find_all(['h2', 'h3', 'h4', 'strong', 'b']):
                tag_text = tag.get_text().lower()
                if any(kw in tag_text for kw in keywords) and len(tag_text) < 50:
                    content = []
                    nxt = tag.find_next_sibling()
                    while nxt and nxt.name not in ['h2', 'h3', 'h4', 'script', 'style']:
                        if nxt.name in ['ul', 'ol']:
                            for li in nxt.find_all('li'):
                                li_text = li.get_text(strip=True)
                                if not any(bad in li_text.lower() for bad in avoid_words):
                                    content.append(li_text)
                        elif nxt.name in ['p', 'table']:
                            p_text = nxt.get_text(separator=" ", strip=True) 
                            if p_text and not any(bad in p_text.lower() for bad in avoid_words):
                                content.append(p_text)
                        nxt = nxt.find_next_sibling()
                    
                    if content:
                        return " || ".join(content)
            return "Not Available"
        
        age_data = extract_full_details(['age limit', 'age relaxation'])
        if age_data != "Not Available" and (details['age_limit'] == "Not Available" or len(age_data) > len(details['age_limit'])): 
            details['age_limit'] = age_data

        selection_data = extract_full_details(['selection process', 'selection procedure'])
        if selection_data != "Not Available": 
            details['selection_process'] = selection_data

        salary_data = extract_full_details(['salary', 'pay scale', 'stipend', 'remuneration'])
        if salary_data != "Not Available" and (details['salary'] == "Not Available" or len(salary_data) > len(details['salary'])): 
            details['salary'] = salary_data

        qual_data = extract_full_details(['qualification', 'educational qualification'])
        if qual_data != "Not Available" and (details['qualification'] == "Not Available" or len(qual_data) > len(details['qualification'])): 
            details['qualification'] = qual_data

        fee_data = extract_full_details(['application fee', 'examination fee'])
        if fee_data != "Not Available" and (details['application_fee'] == "Not Available" or len(fee_data) > len(details['application_fee'])): 
            details['application_fee'] = fee_data

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
        print(f"Deep Scan Start: {filename}...")
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
                        
                        final_qualification = inner_data['qualification']
                        if final_qualification == "Not Available" or len(outer_qualification) > len(final_qualification):
                            final_qualification = outer_qualification

                        final_total_posts = inner_data['total_posts']
                        if final_total_posts == "Not Available" or final_total_posts.lower() == "not mentioned":
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
                            "selection_process": inner_data['selection_process'], 
                            "apply_mode": inner_data['apply_mode'], 
                            "syllabus": inner_data['syllabus'],
                            "official_website": inner_data['official_website'],
                            "official_notification": inner_data['official_notification']
                        })
                break 

        # ==========================================
        # ଏଇଠି ହିଁ ଅସଲି ଲକ୍ (Lock) ଲଗା ହୋଇଛି!
        # ==========================================
        
        # ୧. ଡାଟାକୁ ଗୋଟିଏ Text ରେ ପରିଣତ କରୁଛି
        json_string = json.dumps(jobs_data, ensure_ascii=False)
        
        # ୨. ଡାଟାକୁ Encrypt କରୁଛି (ବାହାର ଲୋକଙ୍କୁ ଏହା ଗୋଳମାଳିଆ ଲାଗିବ)
        encoded_data = base64.b64encode(json_string.encode('utf-8')).decode('utf-8')
        
        # ୩. ଫାଇଲ୍‌ରେ ସେଭ୍ କରୁଛି
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(encoded_data)
            
        # ==========================================

        print(f"ସଫଳତା! {filename} master deep scan complete and LOCKED.")

    except Exception as e:
        print(f"Error ଆସିଲା {filename} ରେ: {e}")

job_sources = {
    "odisha_jobs.json": "https://www.freejobalert.com/odisha-government-jobs/",
    # ତୁମର ବାକି ସବୁ ଲିଙ୍କ୍ ଏଠାରେ ଯେମିତି ଥିଲା ସେମିତି ରହିବ (ମୁଁ ଉଦାହରଣ ପାଇଁ ଗୋଟିଏ ରଖିଛି)
}

total_files = len(job_sources)
current = 0

for file, url in job_sources.items():
    current += 1
    get_jobs(url, file)
    
    if current < total_files:
        print(f"\n[{current}/{total_files}] ପରବର୍ତ୍ତୀ ଲିଙ୍କ୍ କୁ ଯିବା ପୂର୍ବରୁ ୨ ମିନିଟ୍ ବିଶ୍ରାମ...\n")
        time.sleep(120)
