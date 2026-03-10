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
                    details['syllabus'] = row.text.replace('\n', ' ').strip() # କେବଳ ଟେକ୍ସଟ୍

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
 
