import requests
from bs4 import BeautifulSoup
import time

def scrape_web_page(url, retries=3, backoff_factor=0.3):
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raise an error for bad status codes
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to extract meaningful content from the page
            main_content = soup.find('main')
            if main_content is None:
                main_content = soup.find('body')
            if main_content is None:
                main_content = soup  # Fallback to entire HTML if no body/main tag found

            text_content = main_content.get_text(separator=' ', strip=True)
            
            # Ensure a substantial amount of content is captured
            if len(text_content) < 100:
                print(f"Content too short from {url}")
                return None
            
            return text_content[:5000] if len(text_content) > 5000 else text_content

        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch {url} on attempt {attempt+1}: {e}")
            if attempt < retries - 1:
                time.sleep(backoff_factor * (2 ** attempt))  # Exponential backoff
            else:
                return None
