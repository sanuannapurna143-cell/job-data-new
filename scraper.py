import cloudscraper
from bs4 import BeautifulSoup
import json
import time

def get_inner_details(scraper, link):
    details = {
        "total_posts": "Not Available",
        "salary": "Not Available",
        "age_limit": "Not Available", 
        "application_fee": "Not Available",
        "apply_link": "Not Available",
        "official_notification": "Not Available",
        "syllabus": "Not Available",
        "official_website": "Not Available"
    }
    if not link:
        return details
    
    try:
        time.sleep(5) # Block ରୁ ବଞ୍ଚିବା ପାଇଁ
        response = scraper.get(link)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ୧. ଟେବୁଲ୍ ସ୍କାନିଂ (ଦରମା, ବୟସ, ଟୋଟାଲ ପୋଷ୍ଟ ଏବଂ ସିଲାବସ୍ ଟେକ୍ସଟ୍)
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                text = row.text.lower()
                
                if 'age limit' in text and details['age_limit'] == "Not Available":
                    details['age_limit'] = row.text.replace('\n', ' ').strip()
                elif ('application fee' in text or 'examination fee' in text) and details['application_fee'] == "Not Available":
                    details['application_fee'] = row.text.replace('\n', ' ').strip()
                elif ('no of posts' in text or 'total vacancy' in text) and details['total_posts'] == "Not Available":
                    details['total_posts'] = row.text.replace('\n', ' ').replace('no of posts', '').replace('total vacancy', '').strip()
                elif ('salary' in text or 'scale of pay' in text or 'pay scale' in text) and details['salary'] == "Not Available":
                    details['salary'] = row.text.replace('\n', ' ').strip()
                elif 'syllabus' in text and details['syllabus'] == "Not Available":
                    details['syllabus'] = row.text.replace('\n', ' ').strip()

        # ୨. ଲୁଚିଥିବା ଫିସ୍ ଖୋଜିବା
        if details['application_fee'] == "Not Available":
            for p in soup.find_all(['p', 'li']):
                p_text = p.text.lower()
                if 'fee' in p_text and ('rs.' in p_text or 'rupees' in p_text):
                    details['application_fee'] = p.text.strip()
                    break

        # ୩. ସ୍ମାର୍ଟ ଏବଂ କ୍ଲିନ୍ ଲିଙ୍କ୍ ସ୍କାନର୍ (Anti-FreeJobAlert Shield ସହ)
        links = soup.find_all('a')
        for a in links:
            if not a.get('href'): continue
            
            link_text = a.text.lower().strip()
            href = a['href']
            
            # ଯଦି ଲିଙ୍କ୍ ରେ freejobalert ଅଛି କିନ୍ତୁ ତାହା pdf ନୁହେଁ, ତେବେ ତାକୁ ସିଧା ରିଜେକ୍ଟ କର
            is_fja_link = 'freejobalert.com' in href.lower()
            is_pdf = '.pdf' in href.lower()
            if is_fja_link and not is_pdf:
                continue
            
            # Apply Online ଲିଙ୍କ୍
            if 'apply online' in link_text and details['apply_link'] == "Not Available":
                details['apply_link'] = href
                
            # Official Notification (PDF)
            elif ('notification' in link_text or 'detail' in link_text or 'download' in link_text) and details['official_notification'] == "Not Available":
                if 'pdf' in link_text or is_pdf or 'notification' in link_text:
                    details['official_notification'] = href
                    
            # Official Website
            elif 'official website' in link_text and details['official_website'] == "Not Available":
                details['official_website'] = href
                    
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
                
                # rows[1:] ମାନେ ସବୁ ଚାକିରି ଆଣିବ, କେବଳ ୧୦ଟା ନୁହେଁ
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

                        print(f"  -> ଭିତର ପେଜ୍ ଚେକ୍ କରୁଛି: {post_name[:20]}...")
                        inner_data = get_inner_details(scraper, job_link)

                        # ଆମର ନୂଆ ୧୧ଟି ଯାକ ଡାଟା ଗୋଟିଏ ଜାଗାରେ
                        jobs_data.append({
                            "date": post_date,
                            "board": board_name,
                            "title": post_name,
                            "qualification": qualification,
                            "last_date": last_date,
                            "link": job_link,
                            "total_posts": inner_data['total_posts'],
                            "salary": inner_data['salary'],
                            "age_limit": inner_data['age_limit'],
                            "application_fee": inner_data['application_fee'],
                            "apply_link": inner_data['apply_link'],
                            "official_notification": inner_data['official_notification'],
                            "syllabus": inner_data['syllabus'],
                            "official_website": inner_data['official_website']
                        })
                break 

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(jobs_data, f, ensure_ascii=False, indent=4)
        print(f"ସଫଳତା! {filename} ସେଭ୍ ହୋଇଗଲା।")

    except Exception as e:
        print(f"ଅସୁବିଧା ହେଲା {filename} ରେ: {e}")

# ଆମର ସବୁ ରାଜ୍ୟର ଲିଷ୍ଟ
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
