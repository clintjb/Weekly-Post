import os
import requests
import markdown
from pathlib import Path
from datetime import datetime

# Misc Configuration
API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.getenv("API_KEY")

TODAY = datetime.now().strftime("%A %d %B %Y")

INPUT_FILES = {
    'tone': 'input/tone.txt',
    'article': 'input/article.txt'
}
OUTPUT_FILE = '2025-06-21-hacker-news-post.md'
    
# Helper functions & encodings ensuring no issues
def read_file(filename):
    return Path(filename).read_text(encoding='utf-8')

def write_file(filename, content):
    Path(filename).write_text(content, encoding='utf-8')

# Reads tone/article files, sends to LLM API to generate blog post in my style, wraps it up with my theme header as well as a disclaimer, before saving to an output file
def generate_jekyll_post(md_content):
    theme_header = """---
layout: post
tags_color: '#666e76'
title: 'A Weekly Automated Post'
date: 2025-06-21
description: A blog post generated with LLMs based on this weeks Hacker News
tags: [digitalization, GPT, hacker, news, tech, LLM, automation, blog]
categories: digitalization
comments: true
image: '/images/posts/2025/weekly.jpg'
---
"""
    disclaimer = f"""_⚠️ **THIS POST IS GENERATED WITH LLMs**: This post is newly generated a few times a week based on trending articles from hacker news. It takes the tone of my writing style, takes the topic from Hacker News - throws in some LLM magic and generates this post. Please be aware I don't read what gets generated here - it means I may agree, I may not - its a crap shoot - its not meant to be an opinion piece but merely [an experiment](https://github.com/clintjb/Weekly-Post) with the services from [OpenRouter](https://openrouter.ai) - last updated {TODAY}_

"""
    return theme_header + f"![](/images/posts/2025/weekly.jpg)\n\n" + disclaimer + md_content

# --- Main Execution ---
try:
    # Read input files
    tone = read_file(INPUT_FILES['tone'])
    article = read_file(INPUT_FILES['article'])

    # Prepare API request
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek/deepseek-chat-v3-0324:free",
        "messages": [
            {
                "role": "system",
                "content": "You are a skilled writer who can perfectly mimic different writing styles while maintaining authenticity and personality."
            },
            {
                "role": "user",
                "content": f"""Analyze the following writing sample to understand the tone, voice, sentence structure, pacing, and formatting style of the author:
\n{tone}\n

Now, based on the following content:
\n{article}\n

Write a blog post in the same style and tone as the writing sample.
The output should read like a personal blog post, with a natural, reflective, or opinionated voice rather than a journalistic or report-like tone.
Use Markdown formatting, but avoid overuse of subheadings or bullet points—keep it more fluid and narrative.
Do not mention or reference the original article or source—make it feel entirely self-written.
Favor authenticity, personality, and coherence over formality or completeness."""
            }
        ],
        "temperature": 0.9
    }

    # Get the response from the LLM
    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()
    markdown_content = response.json()["choices"][0]["message"]["content"]

    # Save as a Jekyll post
    write_file(OUTPUT_FILE, generate_jekyll_post(markdown_content))
    
    print("Success: Jekyll post created")

except Exception as e:
    print(f"Error: {e}")
