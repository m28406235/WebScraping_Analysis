import os
import warnings

# Suppress warnings and configure environment
os.environ["LOKY_MAX_CPU_COUNT"] = "4"
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="joblib")
import pandas as pd
pd.options.mode.chained_assignment = None

# Web scraping constants
BASE_URL = "https://www.gsmarena.com"
JSON_FILE = "phones.json"
MAX_CONCURRENT_REQUESTS = 2  # Reduced to avoid high request rates
REQUEST_DELAY = (3, 6)  # Increased delay range in seconds
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1"
]
PROXIES = [
    # Add your proxy list here, e.g., "http://proxy1:port", "http://proxy2:port"
    # Example: "http://123.456.789.012:8080"
    # Leave empty to disable proxies
]
SEARCH_URLS = [
    "https://www.gsmarena.com/results.php3?nPriceMin=900&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=700&nPriceMax=900&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=600&nPriceMax=700&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=450&nPriceMax=600&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=350&nPriceMax=450&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=300&nPriceMax=350&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=250&nPriceMax=300&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=200&nPriceMax=250&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nYearMin=2022&nPriceMin=150&nPriceMax=200&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nYearMax=2022&nPriceMin=150&nPriceMax=200&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMax=150&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1"
]