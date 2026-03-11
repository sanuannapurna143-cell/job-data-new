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
        "syllabus": "Not Available",
        "qualification": "Not Available", # ନୂଆ: ଭିତରୁ ଲମ୍ବା ଯୋଗ୍ୟତା ଆଣିବା ପାଇଁ
        "official_website": "Not Available",
        "official_notification": "Not Available"
    }
    if not link:
        return details
    
    try:
        time.sleep(5) 
        response = scraper.get(link)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            fee_header_found = False
            salary_header_found = False
            
            for row in rows:
                text = row.text.lower()
                row_clean = row.text.replace('\n', ' ').strip()
                cols = row.find_all(['td', 'th'])
                
                if 'post name' in text and details['full_title'] == "Not Available":
                    if len(cols) >= 2:
                        details['full_title'] = cols[1].text.strip()
                    else:
                        details['full_title'] = row.text.replace('\n', ' ').strip()
                
                # Apply Mode କୁ ସିଧା ଟେବୁଲ୍ ରୁ ଆଣିବା (ଫାଲତୁ ଅନଲାଇନ୍ ଆସିବନି)
                elif 'apply mode' in text and details['apply_mode'] == "Not Available":
                    if len(cols) >= 2:
                        details['apply_mode'] = cols[1].text.strip()
                    else:
                        val = row_clean.lower().replace('apply mode', '').replace(':', '').strip()
                        details['apply_mode'] = val.title() if val else "Not Available"

                # ନୂଆ: Qualification କୁ ଭିତର ଟେବୁଲ୍ ରୁ ଖୋଜିବା
                elif ('qualification' in text or 'educational qualification' in text) and 'fee' not in text and details['qualification'] == "Not Available":
                    if len(cols) >= 2:
                        details['qualification'] = cols[1].text.replace('\n', ' ').strip()
                    else:
                        details['qualification'] = row_clean

                elif 'age limit' in text and details['age_limit'] == "Not Available":
                    if len(cols) >= 2:
                        details['age_limit'] = cols[1].text.replace('\n', ' ').strip()
                    else:
                        details['age_limit'] = row_clean
                        
                elif ('no of posts' in text or 'total vacancy' in text) and details['total_posts'] == "Not Available":
                    if len(cols) >= 2:
                        details['total_posts'] = cols[1].text.replace('\n', ' ').strip()
                    else:
                        details['total_posts'] = row_clean.replace('no of posts', '').replace('total vacancy', '').strip()
                        
                elif ('salary' in text or 'scale of pay' in text or 'pay scale' in text or 'pay matrix' in text or 'remuneration' in text or 'stipend' in text) and 'qualification' not in text and details['salary'] == "Not Available":
                    if len(cols) >= 2:
                        details['salary'] = cols[1].text.replace('\n', ' ').strip()
                    else:
                        if 'rs' in text or 'rupee' in text or '₹' in text or 'level' in text or 'as per' in text:
                            details['salary'] = row_clean
                        else:
                            salary_header_found = True
                
                elif salary_header_found and details['salary'] == "Not Available":
                    if 'qualification' in text or 'age limit' in text or 'post' in text:
                        salary_header_found = False
                    else:
                        if len(cols) >= 2:
                            details['salary'] = cols[1].text.replace('\n', ' ').strip()
                        else:
                            details['salary'] = row_clean
                        salary_header_found = False
                        
                elif 'syllabus' in text and details['syllabus'] == "Not Available":
                    details['syllabus'] = row_clean

                if details['application_fee'] == "Not Available":
                    if 'application fee' in text or 'examination fee' in text:
                        if any(char.isdigit() for char in row_clean) or 'rs' in text or 'rupee' in text or 'nil' in text or 'exempted' in text or '₹' in text:
                            details['application_fee'] = row_clean
                        else:
                            fee_header_found = True
                    elif fee_header_found:
                        if any(char.isdigit() for char in row_clean) or 'rs' in text or 'rupee' in text or 'nil' in text or 'exempted' in text or '₹' in text:
                            details['application_fee'] = row_clean
                        fee_header_found = False

        if details['application_fee'] == "Not Available":
            for p in soup.find_all(['p', 'li']):
                p_text = p.text.lower()
                if 'fee' in p_text and ('rs.' in p_text or 'rupees' in p_text or 'nil' in p_text or '₹' in p_text):
                    details['application_fee'] = p.text.strip()
                    break

        if details['salary'] == "Not Available":
            for p in soup.find_all(['p', 'li']):
                p_text = p.text.lower()
                if ('salary' in p_text or 'pay' in p_text or 'remuneration' in p_text) and ('rs' in p_text or 'rupee' in p_text or '₹' in p_text or 'as per' in p_text):
                    details['salary'] = p.text.strip()
                    break

        apply_link_found = False
        page_text_lower = soup.text.lower()
        for element in soup.find_all(['li', 'tr', 'p']):
            text = element.text.lower()
            a_tags = element.find_all('a')
            
            for a in a_tags:
                href = a.get('href', '')
                if not href or href == '#' or ('freejobalert.com' in href.lower() and '.pdf' not in href.lower()):
                    continue
                
                if 'apply online' in text or 'apply here' in text:
                    apply_link_found = True

                if 'official website' in text and details['official_website'] == "Not Available":
                    details['official_website'] = href
                elif ('notification' in text or 'detail' in text) and details['official_notification'] == "Not Available":
                    details['official_notification'] = href
                    
        # Apply Mode ର ବ୍ୟାକଅପ୍ ପ୍ଲାନ୍ (କେବଳ ଯଦି ଟେବୁଲ୍ ରେ ନମିଳେ)
        if details['apply_mode'] == "Not Available" or details['apply_mode'] == "":
            if apply_link_found or 'apply online' in page_text_lower:
                details['apply_mode'] = "Online"
            elif 'walk-in' in page_text_lower or 'walk in' in page_text_lower:
                details['apply_mode'] = "Walk-in"
            else:
                details['apply_mode'] = "Offline / Notification ଦେଖନ୍ତୁ"
                    
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
                        outer_qualification = cols[3].text.strip() # ବାହାର ଯୋଗ୍ୟତା
                        last_date = cols[5].text.strip()
                        
                        job_link = ""
                        last_col = cols[-1]
                        a_tag = last_col.find('a')
                        if a_tag and 'href' in a_tag.attrs:
                            job_link = a_tag['href']

                        print(f"  -> ଭିତର ପେଜ୍ ଚେକ୍ କରୁଛି: {post_name[:20]}...")
                        inner_data = get_inner_details(scraper, job_link)

                        final_title = inner_data['full_title'] if inner_data['full_title'] != "Not Available" else post_name

                        # ଲମ୍ବା Qualification ଆଣିବା ଲଜିକ୍
                        final_qualification = inner_data['qualification'] if inner_data['qualification'] != "Not Available" else outer_qualification

                        final_total_posts = inner_data['total_posts']
                        if final_total_posts == "Not Available":
                            match = re.search(r'(\d+)\s*(?:post|vacancy|posts|vacancies)', post_name, re.IGNORECASE)
                            if match:
                                final_total_posts = match.group(1)
                            else:
                                match2 = re.search(r'-\s*(\d+)', post_name)
                                if match2:
                                    final_total_posts = match2.group(1)

                        jobs_data.append({
                            "date": post_date,
                            "board": board_name,
                            "title": final_title,
                            "qualification": final_qualification, # ଏଥର ଲମ୍ବା ଆସିବ!
                            "last_date": last_date,
                            "total_posts": final_total_posts,
                            "salary": inner_data['salary'],
                            "age_limit": inner_data['age_limit'],
                            "application_fee": inner_data['application_fee'],
                            "apply_mode": inner_data['apply_mode'], # ଏଥର ସଠିକ୍ ଆସିବ!
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
