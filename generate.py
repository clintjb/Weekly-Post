import os
import requests
import markdown
from pathlib import Path

# --- Config ---
API_URL = "https://api.llmapi.com/chat/completions"
API_KEY = os.getenv("API_KEY")
INPUT_FILES = {
    'tone': 'input/tone.txt',
    'article': 'input/article.txt'
}
OUTPUT_FILE = '2025-04-24-hacker-news-post.md'

# --- Helper Functions ---
def read_file(filename):
    return Path(filename).read_text(encoding='utf-8')

def write_file(filename, content):
    Path(filename).write_text(content, encoding='utf-8')

def generate_jekyll_post(md_content):
    front_matter = """---
layout: post
tags_color: '#666e76'
title: 'Hacker News Of The Week'
date: 2025-04-24
description: Weekly automated blog post based on Hacker News number one topic
tags: [digitalization, GPT, quote, vibe, tech, debt, chatgpt]
categories: digitalization
comments: true
image: '/images/posts/2025/weekly.jpg'
---
"""
    return front_matter + f"![](/images/posts/2025/weekly.jpg)\n\n" + md_content

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
        "model": "deepseek-v3",
        "messages": [
            {
                "role": "system",
                "content": "You are a casual writer creating blog posts around technology. Mimic the user's style and return content using Markdown formatting."
            },
            {
                "role": "user",
                "content": f"Analyze this writing style:\n{tone}\n\nNow write a blog post in THAT style about:\n{article}\nUse Markdown formatting. Ensure its more like a personal blog post (without so many subheadings etc) and ensure there's no reference to the original article to make it appear really like a self written article"
            }
        ],
        "temperature": 0.9
    }

    # Get LLM response
    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()
    markdown_content = response.json()["choices"][0]["message"]["content"]

    # Save as Jekyll post
    write_file(OUTPUT_FILE, generate_jekyll_post(markdown_content))
    
    print("Success: Jekyll post created")

except Exception as e:
    print(f"Error: {e}")
