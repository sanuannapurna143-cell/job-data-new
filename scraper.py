import cloudscraper
from bs4 import BeautifulSoup
import json
import time

def get_inner_details(scraper, link):
    details = {"age_limit": "Not Available", "application_fee": "Not Available"}
    if not link:
        return details
    
    try:
        time.sleep(5) # ଭିତର ପେଜ୍ ଖୋଲିବା ବେଳେ ବ୍ଲକ୍ ନହେବା ପାଇଁ ୫ ସେକେଣ୍ଡ ବିଶ୍ରାମ
        response = scraper.get(link)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                text = row.text.lower()
                if 'age limit' in text:
                    details['age_limit'] = row.text.replace('\n', ' ').strip()
                elif 'application fee' in text:
                    details['application_fee'] = row.text.replace('\n', ' ').strip()
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
                
                # କେବଳ ଟପ୍ ୧୦ଟି ଚାକିରି ଆଣିବା
                for row in rows[1:11]:
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

                        print(f"  -> ଭିତର ପେଜ୍ ଚେକ୍ କରୁଛି: {post_name[:20]}...")
                        inner_data = get_inner_details(scraper, job_link)

                        jobs_data.append({
                            "date": post_date,
                            "board": board_name,
                            "title": post_name,
                            "qualification": qualification,
                            "last_date": last_date,
                            "link": job_link,
                            "age_limit": inner_data['age_limit'],
                            "application_fee": inner_data['application_fee']
                        })
                break 

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(jobs_data, f, ensure_ascii=False, indent=4)
        print(f"ସଫଳତା! {filename} ସେଭ୍ ହୋଇଗଲା।")

    except Exception as e:
        print(f"ଅସୁବିଧା ହେଲା {filename} ରେ: {e}")

# ବର୍ତ୍ତମାନ ଟେଷ୍ଟିଂ ପାଇଁ ୩ଟି ରାଜ୍ୟ
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
