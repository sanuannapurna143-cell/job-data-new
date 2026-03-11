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
        
        # 1. SOB TABLE SCAN KORBE (Not just first table)
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                text = row.text.lower()
                row_clean = row.text.replace('\n', ' ').strip()
                cols = row.find_all(['td', 'th'])
                
                # Full Title
                if 'post name' in text and details['full_title'] == "Not Available":
                    if len(cols) >= 2: details['full_title'] = cols[1].text.strip()
                
                # Apply Mode
                elif 'apply mode' in text and details['apply_mode'] == "Not Available":
                    if len(cols) >= 2: details['apply_mode'] = cols[1].text.strip()
                    else:
                        val = row_clean.lower().replace('apply mode', '').replace(':', '').strip()
                        details['apply_mode'] = val.title() if val else "Not Available"

                # Inner Total Posts
                elif ('no of posts' in text or 'total vacancy' in text or 'vacancy' in text) and details['total_posts'] == "Not Available":
                    if len(cols) >= 2: details['total_posts'] = cols[1].text.replace('\n', ' ').strip()
                        
                # Salary theke asha
                elif ('salary' in text or 'scale of pay' in text or 'pay scale' in text) and details['salary'] == "Not Available":
                    if len(cols) >= 2: details['salary'] = cols[1].text.replace('\n', ' ').strip()

                # Syllabus
                elif 'syllabus' in text and details['syllabus'] == "Not Available":
                    details['syllabus'] = row_clean

        # 2. DEEP SCAN - HEADINGS ER NICHE (For Details)
        # Avoid korar jonne bad words (Sidebar er faltu link theke bachar jonne)
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
                            p_text = nxt.get_text(separator=" | ", strip=True)
                            if p_text and not any(bad in p_text.lower() for bad in avoid_words):
                                content.append(p_text)
                        nxt = nxt.find_next_sibling()
                    
                    if content:
                        return " || ".join(content)
            return "Not Available"

        # DEEP SCAN APPLY KORA HOLO:
        
        # Age Limit Deep Scan
        age_data = extract_full_details(['age limit', 'age relaxation'])
        if age_data != "Not Available": details['age_limit'] = age_data

        # Selection Process Deep Scan
        selection_data = extract_full_details(['selection process', 'selection procedure'])
        if selection_data != "Not Available": details['selection_process'] = selection_data

        # Salary / Stipend Deep Scan
        salary_data = extract_full_details(['salary', 'pay scale', 'stipend', 'remuneration'])
        if salary_data != "Not Available": details['salary'] = salary_data

        # Qualification Deep Scan
        qual_data = extract_full_details(['qualification', 'educational qualification'])
        if qual_data != "Not Available": details['qualification'] = qual_data

        # Application Fee Deep Scan
        fee_data = extract_full_details(['application fee', 'examination fee'])
        if fee_data != "Not Available": details['application_fee'] = fee_data

        # 3. LINK SCANNER
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
                    
        # Apply Mode Backup
        if details['apply_mode'] == "Not Available" or details['apply_mode'] == "":
            if apply_link_found or 'apply online' in page_text: details['apply_mode'] = "Online"
            elif 'walk-in' in page_text or 'walk in' in page_text: details['apply_mode'] = "Walk-in"
            else: details['apply_mode'] = "Offline / Notification Dekhun"
                    
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

                        print(f"  -> Vitorer page deep check korchhi: {post_name[:20]}...")
                        inner_data = get_inner_details(scraper, job_link)

                        final_title = inner_data['full_title'] if inner_data['full_title'] != "Not Available" else post_name
                        final_qualification = inner_data['qualification'] if inner_data['qualification'] != "Not Available" else outer_qualification

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

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(jobs_data, f, ensure_ascii=False, indent=4)
        print(f"Success! {filename} master deep scan complete.")

    except Exception as e:
        print(f"Error aschhe {filename} te: {e}")

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
        print("\nState change korar age 2 minute wait korchhi...\n")
        time.sleep(120)
