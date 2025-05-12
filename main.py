import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from scraper.fetcher import scrape
from database.mongo import save_mongo

if __name__ == "__main__":
    try:
        asyncio.run(scrape())
        save_mongo()
        print("Run visualizations with: streamlit run src/visualization/plots.py")
    except RuntimeError as e:
        print(str(e))
        sys.exit(1)