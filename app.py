from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from wiki_category_analysis import (
    get_cache_filename,
    load_cache,
    get_category_members,
    get_page_content,
    process_text,
    download_nltk_data,
    save_cache
)
from collections import Counter
from typing import Dict, List, Any
import os

app = FastAPI()

# Create directories if they don't exist
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(BASE_DIR, "templates")
static_dir = os.path.join(BASE_DIR, "static")

os.makedirs(templates_dir, exist_ok=True)
os.makedirs(static_dir, exist_ok=True)

# Mount static files directory
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Setup templates
templates = Jinja2Templates(directory=templates_dir)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/analyze/{category}")
async def analyze_category(category: str) -> Dict[str, Any]:
    # Check cache first
    freq_cache_file = get_cache_filename(category, "frequencies")
    cached_frequencies = load_cache(freq_cache_file)
    
    if cached_frequencies is not None:
        frequencies = Counter(cached_frequencies)
        print(f"Using cached data for category: {category}")
    else:
        # Download NLTK data if needed
        download_nltk_data()
        
        # Get pages
        print(f"Fetching pages for category: {category}")
        pages = get_category_members(category)
        if not pages:
            print(f"No pages found for category: {category}")
            return {
                "status": "error",
                "message": f"No pages found in category '{category}'. Please check the category name and try again.",
                "words": []
            }
            
        # Process pages
        frequencies = Counter()
        for page in pages:
            content = get_page_content(page)
            page_frequencies = process_text(content)
            frequencies.update(page_frequencies)
            
        # Cache results
        save_cache(freq_cache_file, dict(frequencies))
    
    # Convert to list of dictionaries for JSON response
    words_list = [
        {"word": word, "frequency": freq}
        for word, freq in frequencies.most_common(100)  # Show top 100 words
    ]
    
    # Check if we found any words
    if not words_list:
        return {
            "status": "error",
            "message": f"No significant words found in category '{category}'. This might be an empty category or contain only common words.",
            "words": []
        }
    
    return {
        "status": "success",
        "message": f"Found {len(words_list)} words in category '{category}'",
        "words": words_list
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
