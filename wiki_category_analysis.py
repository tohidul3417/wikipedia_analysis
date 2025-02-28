import requests
import sys
import json
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from tqdm import tqdm
import os
from datetime import datetime, timedelta
import hashlib

# Create cache directory if it doesn't exist
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_filename(category_name, suffix):
    """Generate a cache filename for a given category and suffix."""
    # Create a safe filename using hash
    category_hash = hashlib.md5(category_name.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{category_hash}_{suffix}.json")

def load_cache(cache_file, max_age_hours=24):
    """Load cached data if it exists and is not too old."""
    if not os.path.exists(cache_file):
        return None
        
    # Check if cache is too old
    file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
    if datetime.now() - file_time > timedelta(hours=max_age_hours):
        return None
        
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def save_cache(cache_file, data):
    """Save data to cache file."""
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def download_nltk_data():
    """Download required NLTK data."""
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('punkt')
        nltk.download('stopwords')

def get_category_members(category_name):
    """Get all pages in a given category."""
    cache_file = get_cache_filename(category_name, "pages")
    cached_pages = load_cache(cache_file)
    
    if cached_pages is not None:
        print("Using cached category members...")
        return cached_pages
    
    base_url = "https://en.wikipedia.org/w/api.php"
    pages = []
    
    params = {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "cmtitle": f"Category:{category_name}",
        "cmlimit": "500"
    }
    
    while True:
        response = requests.get(base_url, params=params)
        data = response.json()
        
        if 'error' in data:
            print(f"Error: {data['error']['info']}")
            return []
            
        members = data['query']['categorymembers']
        pages.extend([member['title'] for member in members if member['ns'] == 0])
        
        if 'continue' not in data:
            break
            
        params['cmcontinue'] = data['continue']['cmcontinue']
    
    # Cache the results
    save_cache(cache_file, pages)
    return pages

def get_page_content(page_title):
    """Get the content of a Wikipedia page."""
    base_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "titles": page_title,
        "prop": "extracts",
        "explaintext": True
    }
    
    response = requests.get(base_url, params=params)
    data = response.json()
    
    pages = data['query']['pages']
    page_id = list(pages.keys())[0]
    
    if 'extract' not in pages[page_id]:
        return ""
        
    return pages[page_id]['extract']

def process_text(text):
    """Process text and return word frequencies excluding stop words."""
    # Tokenize text
    tokens = word_tokenize(text.lower())
    
    # Remove stop words and non-alphabetic tokens
    stop_words = set(stopwords.words('english'))
    words = [word for word in tokens if word.isalpha() and word not in stop_words]
    
    # Count frequencies
    return Counter(words)

def main():
    if len(sys.argv) != 2:
        print("Usage: python wiki_category_analysis.py <category_name>")
        sys.exit(1)
        
    category_name = sys.argv[1]
    
    # Check for cached word frequencies
    freq_cache_file = get_cache_filename(category_name, "frequencies")
    cached_frequencies = load_cache(freq_cache_file)
    
    if cached_frequencies is not None:
        print("Using cached word frequencies...")
        total_frequencies = Counter(cached_frequencies)
    else:
        # Download required NLTK data
        download_nltk_data()
        
        print(f"\nFetching pages in category: {category_name}")
        pages = get_category_members(category_name)
        
        if not pages:
            print("No pages found in the category.")
            return
            
        print(f"Found {len(pages)} pages.")
        
        # Process each page
        total_frequencies = Counter()
        
        for page in tqdm(pages, desc="Processing pages"):
            content = get_page_content(page)
            frequencies = process_text(content)
            total_frequencies.update(frequencies)
            
        # Cache the results
        save_cache(freq_cache_file, dict(total_frequencies))
    
    # Display results
    print("\nMost common non-common words and their frequencies:")
    for word, freq in total_frequencies.most_common(20):
        print(f"{word}: {freq}")

if __name__ == "__main__":
    main()
