import requests
import time
from datetime import datetime, timedelta
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import logging

# Configuration
BASE_URL = "https://hacker-news.firebaseio.com/v0"
OUTPUT_DIR = Path("input")
FETCH_DELAY = 0.1
MAX_POSTS_TO_CHECK = 10

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_top_post_last_week():
    """Get highest-scored HN post from last week"""
    try:
        story_ids = requests.get(f"{BASE_URL}/topstories.json").json()
        one_week_ago = int((datetime.now() - timedelta(days=7)).timestamp())
        
        top_post = None
        for story_id in story_ids[:MAX_POSTS_TO_CHECK]:
            story = requests.get(f"{BASE_URL}/item/{story_id}.json").json()
            if story.get('time', 0) >= one_week_ago and (not top_post or story.get('score', 0) > top_post['score']):
                top_post = story
            time.sleep(FETCH_DELAY)
        
        return top_post
    except Exception as e:
        logger.error(f"Error fetching HN data: {e}")
        return None

def scrape_article(url):
    """Simplified article content scraper"""
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'iframe']):
            element.decompose()
        
        # Get clean text with basic spacing
        text = ' '.join(soup.get_text().split())
        return text[:10000]  # Limit to first 10k chars to avoid huge files
    except Exception as e:
        logger.warning(f"Error scraping article: {e}")
        return "Could not retrieve article content"

def save_largest_image(url, output_path):
    """Find and save the largest image from a webpage as weekly.jpg"""
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        images = []
        for img in soup.find_all('img', src=True):
            img_url = img['src'] if img['src'].startswith('http') else f"{url.rstrip('/')}/{img['src'].lstrip('/')}"
            images.append(img_url)

        largest = None
        for img_url in images[:5]:  # Check first 5 images only
            try:
                img_data = requests.get(img_url, timeout=5).content
                img = Image.open(BytesIO(img_data))
                size = img.size[0] * img.size[1]
                if not largest or size > largest[0]:
                    largest = (size, img.copy())  # Copy to keep open reference
            except Exception as e:
                continue

        if largest:
            img = largest[1]
            img = img.convert("RGB")  # Convert to RGB to ensure compatibility with JPEG
            img.save(output_path / "weekly.jpg", format="JPEG", quality=85)
            return True
    except Exception as e:
        logger.warning(f"Error saving image: {e}")
    return False

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    logger.info("Finding top HN post from last week...")
    post = get_top_post_last_week()
    if not post:
        logger.error("No suitable post found")
        return
    
    # Save article data
    article_text = scrape_article(post['url']) if 'url' in post else "No URL available"
    with open(OUTPUT_DIR / "article.txt", 'w') as f:
        f.write(f"Title: {post.get('title', 'N/A')}\n")
        f.write(f"Author: {post.get('by', 'N/A')}\n")
        f.write(f"Score: {post.get('score', 'N/A')}\n")
        f.write(f"URL: {post.get('url', 'N/A')}\n\n")
        f.write(article_text)
    
    # Save image if available
    if 'url' in post:
        logger.info("Attempting to save article image...")
        if save_largest_image(post['url'], OUTPUT_DIR):
            logger.info("Image saved successfully")
        else:
            logger.info("No suitable image found")
    
    logger.info(f"Article saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
