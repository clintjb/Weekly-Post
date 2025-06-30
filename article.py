import requests
import time
from datetime import datetime, timedelta
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import logging

# Misc Configuration
BASE_URL = "https://hacker-news.firebaseio.com/v0"
OUTPUT_DIR = Path("input")
FETCH_DELAY = 0.2  # Delay between my API calls to be somewhat fair and not get banned
MAX_POSTS = 50  # Number of top posts to check to find the highest score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_top_post():
    """Grabs the top article from last week: gets the article IDs - filters by date - finds the highest score and returns the best post"""
    try:
        story_ids = requests.get(f"{BASE_URL}/topstories.json").json()
        week_ago = (datetime.now() - timedelta(days=7)).timestamp()
        
        top_post = None
        for story_id in story_ids[:MAX_POSTS]:
            story = requests.get(f"{BASE_URL}/item/{story_id}.json").json()
            if story.get('time', 0) >= week_ago and (not top_post or story['score'] > top_post['score']):
                top_post = story
            time.sleep(FETCH_DELAY)
        
        return top_post
    except Exception as e:
        logger.error(f"Error fetching HN data: {e}")
        return None

def scrape_article(url):
    """BS to scrape the webpage, parses the HTML, removes any unwanted elements (scripts/styles/nav/footer/iframes etc) extracts as clean text, drops it 10k chars and returns the content"""
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for element in soup(['script', 'style', 'nav', 'footer', 'iframe']):
            element.decompose()
        
        return ' '.join(soup.get_text().split())[:10000]
    except Exception as e:
        logger.warning(f"Error scraping article: {e}")
        return "Could not retrieve article content"

def save_image(url, output_path):
    """Again uses BT to grab the page, parses HTML for images & downloads the first 5, finds the largest image (by pixel count) resizes to max 900x600 and saves as weekly.jpg"""
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        img_urls = [img['src'] if img['src'].startswith('http') else f"{url.rstrip('/')}/{img['src'].lstrip('/')}"
                    for img in soup.find_all('img', src=True)][:5]
        
        largest = None
        for img_url in img_urls:
            try:
                img_data = requests.get(img_url, timeout=5).content
                img = Image.open(BytesIO(img_data))
                size = img.size[0] * img.size[1]
                if not largest or size > largest[0]:
                    largest = (size, img.copy())
            except Exception as inner_e: # Catch specific exceptions for image fetching/opening
                logger.debug(f"Could not process image {img_url}: {inner_e}") # Use debug for individual image errors
                continue

        if largest:
            img = largest[1].convert("RGB")
            img.thumbnail((900, 600))
            img.save(output_path / "weekly.jpg", "JPEG", quality=85)
            logger.info("Image found in article and saved.")
            return True
        else:
            logger.info("Couldnt find an image - using the backup")
            alt_url = "https://clintbird.com/images/posts/2025/weekly_alt.jpg"
            img_data = requests.get(alt_url, timeout=5).content
            img = Image.open(BytesIO(img_data)).convert("RGB")
            img.thumbnail((900, 600))
            img.save(output_path / "weekly.jpg", "JPEG", quality=85)
            return True
            
    except Exception as e:
        logger.warning(f"Error saving image: {e}")
        return False

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    logger.info("Finding top HN post...")
    if not (post := get_top_post()):
        logger.error("No post found")
        return
    
    with open(OUTPUT_DIR / "article.txt", 'w') as f:
        f.write(f"Title: {post.get('title', 'N/A')}\nAuthor: {post.get('by', 'N/A')}\n")
        f.write(f"Score: {post.get('score', 'N/A')}\nURL: {post.get('url', 'N/A')}\n\n")
        f.write(scrape_article(post['url']) if 'url' in post else "No URL available")
    
    if 'url' in post and save_image(post['url'], OUTPUT_DIR):
        logger.info("Image saved")
    
    logger.info(f"Article URL: {post.get('url', 'N/A')}")

if __name__ == "__main__":
    main()
