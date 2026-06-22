import urllib.request
import xml.etree.ElementTree as ET
import html
import re
import json
import time
import os
import sys

def clean_html(raw_html):
    # Remove HTML tags
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    # Decode HTML entities (e.g. &lt; to <, &#32; to space)
    text = html.unescape(cleantext)
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_comment_entry(entry, ns):
    id_node = entry.find('atom:id', ns)
    title_node = entry.find('atom:title', ns)
    author_node = entry.find('atom:author/atom:name', ns)
    content_node = entry.find('atom:content', ns)
    link_node = entry.find('atom:link', ns)
    updated_node = entry.find('atom:updated', ns)
    
    comment_id = id_node.text.split('/')[-1] if id_node is not None else "unknown"
    title = title_node.text if title_node is not None else ""
    author = author_node.text if author_node is not None else "unknown"
    raw_content = content_node.text if content_node is not None else ""
    permalink = link_node.attrib.get('href', '') if link_node is not None else ""
    updated_time = updated_node.text if updated_node is not None else ""
    
    # Extract the thread title from the entry title/preview
    # Usually: "/u/username on Thread Title" or "Comment on Thread Title by /u/username"
    thread_title = title
    if " on " in title:
        parts = title.split(" on ", 1)
        thread_title = parts[1]
    elif "Comment on " in title and " by " in title:
        parts = title.split("Comment on ", 1)
        if " by " in parts[1]:
            thread_title = parts[1].rsplit(" by ", 1)[0]

    body = clean_html(raw_content)
    
    # Clean up standard Reddit footer from RSS content
    # e.g., "submitted by /u/name [link] [comments]"
    footer_pattern = re.compile(r'\s*submitted by\s+/u/\S+\s+\[link\]\s+\[comments\]\s*$', re.IGNORECASE)
    body = footer_pattern.sub('', body)
    
    return {
        "comment_id": comment_id,
        "author": author,
        "thread_title": thread_title,
        "body": body,
        "permalink": permalink,
        "updated": updated_time
    }

def scrape_soccer_comments(target_count=220, output_file="data/raw_comments.json"):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Load existing comments if file exists
    comments_dict = {}
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                comments_dict = {c['comment_id']: c for c in existing_data}
                print(f"Loaded {len(comments_dict)} existing comments from {output_file}.")
        except Exception as e:
            print(f"Error loading existing data: {e}")
            
    url = "https://www.reddit.com/r/soccer/comments.rss"
    user_agent = "osx:takemeter:v1.0 (by /u/DavidSong74)"
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    
    consecutive_errors = 0
    
    while len(comments_dict) < target_count:
        print(f"Current unique comments count: {len(comments_dict)} / {target_count}")
        print("Fetching latest comments feed...")
        
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': user_agent}
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                consecutive_errors = 0
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                entries = root.findall('atom:entry', ns)
                
                new_added = 0
                for entry in entries:
                    comment = parse_comment_entry(entry, ns)
                    # Ignore empty/short comments if we want quality text, or keep them all
                    if comment['comment_id'] not in comments_dict and len(comment['body']) > 10:
                        comments_dict[comment['comment_id']] = comment
                        new_added += 1
                        
                print(f"Added {new_added} new unique comments in this fetch.")
                
                # Save progress immediately
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(list(comments_dict.values()), f, indent=2, ensure_ascii=False)
                    
                if len(comments_dict) >= target_count:
                    break
                    
                print("Sleeping 65 seconds to avoid rate limiting...")
                time.sleep(65)
                
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print("Rate limit hit (429). Sleeping 90 seconds...")
                time.sleep(90)
            else:
                print(f"HTTP Error {e.code}: {e.reason}")
                consecutive_errors += 1
                time.sleep(30)
        except Exception as e:
            print(f"Error during fetch: {e}")
            consecutive_errors += 1
            time.sleep(30)
            
        if consecutive_errors >= 5:
            print("Too many consecutive errors. Exiting.")
            sys.exit(1)
            
    print(f"\nScraping complete! Saved {len(comments_dict)} comments to {output_file}.")

if __name__ == "__main__":
    # If run directly, run the scraper
    scrape_soccer_comments(target_count=220)
