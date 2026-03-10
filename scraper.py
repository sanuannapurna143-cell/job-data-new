import cloudscraper
from bs4 import BeautifulSoup
import json
import time

def get_inner_details(scraper, link):
    # Nua features add hela (Syllabus, Apply Link, Official PDF)
    details = {
        "age_limit": "Not Available", 
        "application_fee": "Not Available",
        "apply_link": "Not Available",
        "official_notification": "Not Available",
        "syllabus_link": "Not Available"
    }
    if not link:
        return details
    
    try:
        time.sleep(5) # Block ru banchiba pain 5 second gap
        response = scraper.get(link)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Age au Fee khujiba
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                text = row.text.lower()
                if 'age limit' in text and details['age_limit'] == "Not Available":
                    details['age_limit'] = row.text.replace('\n', ' ').strip()
                elif 'application fee' in text and details['application_fee'] == "Not Available":
                    details['application_fee'] = row.text.replace('\n', ' ').strip()
        
        # Nua jinis: Syllabus au Apply Link khujiba
        links = soup.find_all('a')
        for a in links:
            if not a.get('href'): continue
            link_text = a.text.lower()
            href = a['href']
            
            if 'apply online' in link_text and details['apply_link'] == "Not Available":
                details['apply_link'] = href
            elif 'official notification' in link_text and details['official_notification'] == "Not Available":
                details['official_notification'] = href
            elif 'syllabus' in link_text and details['syllabus_link'] == "Not Available":
                details['syllabus_link'] = href
                    
    except Exception as e:
        pass 
        
    return details

def get_jobs(url, filename):
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    try:
        print(f"Khojuchhi: {filename}...")
        response = scraper.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        jobs_data = []
        tables = soup.find_all('table')

        for table in tables:
            if 'Post Date' in table.text or 'Qualification' in table.text:
                rows = table.find_all('tr')
                
                # Ebe [1:] ra artha hela PURA SABU JOB asiba, kebala 10 ta nuhe
                for row in rows[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 6:
                        post_date = cols[0].text.strip()
                        board_name = cols[1].text.strip()
                        post_name = cols[2].text.strip()
                        qualification = cols[3].text.strip()
                        last_date = cols[5].text.strip()
                        
                        job_link = ""
                        last_col = cols[-1]
                        a_tag = last_col.find('a')
                        if a_tag and 'href' in a_tag.attrs:
                            job_link = a_tag['href']

                        print(f"  -> Bhitara page check karuchhi: {post_name[:20]}...")
                        inner_data = get_inner_details(scraper, job_link)

                        jobs_data.append({
                            "date": post_date,
                            "board": board_name,
                            "title": post_name,
                            "qualification": qualification,
                            "last_date": last_date,
                            "link": job_link,
                            "age_limit": inner_data['age_limit'],
                            "application_fee": inner_data['application_fee'],
                            "apply_link": inner_data['apply_link'],
                            "official_notification": inner_data['official_notification'],
                            "syllabus_link": inner_data['syllabus_link']
                        })
                break 

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(jobs_data, f, ensure_ascii=False, indent=4)
        print(f"Safalata! {filename} save hoigala.")

    except Exception as e:
        print(f"Asubidha hela {filename} re: {e}")

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
        print("\nRajya badalaiba purbaru 2 minute bishrama...\n")
        time.sleep(120)
