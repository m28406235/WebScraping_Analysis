# Phone Analysis Project

This project scrapes smartphone specifications from [GSMArena](https://www.gsmarena.com), processes the data, stores it in MongoDB, and visualizes key metrics using Streamlit. The code is modularized into multiple files for better organization and maintainability, separating concerns such as configuration, web scraping, data processing, database operations, and visualization. To avoid being blocked by GSMArena's rate-limiting mechanisms, the scraper implements low concurrency, extended delays, proxy rotation, and adaptive retries.

## Project Structure
```
WebScraping_Analysis/
├── src/
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── fetcher.py
│   │   └── parser.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   ├── processor.py
│   │   └── tier_assigner.py
│   ├── database/
│   │   ├── __init__.py
│   │   └── mongo.py
│   ├── visualization/
│   │   ├── __init__.py
│   │   └── plots.py
│   ├── __init__.py
├── main.py
├── requirements.txt
├── phones.json
└── README.markdown
```

### File Descriptions
- **src/config/settings.py**: Defines constants (e.g., URLs, user agents, proxies) and configures the environment (e.g., suppresses warnings, sets CPU limits).
- **src/scraper/fetcher.py**: Handles fetching phone links and scraping individual phone pages using asynchronous HTTP requests with `aiohttp`, incorporating user agent rotation and extended retries.
- **src/scraper/parser.py**: Parses phone specifications from HTML into structured dictionaries using `BeautifulSoup`.
- **src/data/loader.py**: Manages loading and saving phone data to/from a JSON file (`phones.json`).
- **src/data/processor.py**: Converts raw JSON data into a processed Pandas DataFrame, extracting key specifications and handling currency conversion.
- **src/data/tier_assigner.py**: Assigns price-based tiers (Budget, Mid-Range, Premium, Flagship) using KMeans clustering.
- **src/database/mongo.py**: Saves processed data to MongoDB with upsert operations to avoid duplicates.
- **src/visualization/plots.py**: Generates interactive visualizations (scatter plots, pie charts, bar charts, etc.) using Streamlit, Plotly, and Seaborn.
- **main.py**: Entry point for running the scraping and MongoDB storage processes.
- **requirements.txt**: Lists Python dependencies for the project.
- **phones.json**: Stores scraped phone data (generated during execution).
- **__init__.py files**: Empty files that make directories proper Python packages for importing modules.

## Instructions to Run

1. **Clone the Repository or Set Up the Project Structure**:
   - Ensure the folder structure matches the one shown above.
   - Make sure all Python files are correctly placed in their respective subdirectories under the `src` directory.
   - Create empty `__init__.py` files in all directories to make them proper Python packages.

2. **Install Dependencies**:
   - Ensure Python 3.8+ is installed.
   - Navigate to the project root (`WebScraping_Analysis/`) in a terminal.
   - Create a virtual environment (optional but recommended):
     ```bash
     python -m venv venv
     source venv/bin/activate  # On Windows: venv\Scripts\activate
     ```
   - Install dependencies:
     ```bash
     pip install -r requirements.txt
     ```
   - Required packages include `aiohttp`, `beautifulsoup4`, `pandas`, `scikit-learn`, `pymongo`, `streamlit`, `plotly`, `matplotlib`, `seaborn`, `tenacity`, and `pyarrow`.

3. **Configure Proxies (Optional but Recommended)**:
   - To avoid rate-limiting or IP bans, configure proxies in `src/config/settings.py` by adding a list of HTTP proxies to the `PROXIES` variable (e.g., `["http://123.456.789.012:8080", "http://987.654.321.098:8080"]`).
   - Obtain proxies from a reliable proxy provider (e.g., Bright Data, Oxylabs, or free proxy lists for testing). Ensure proxies support HTTP/HTTPS.
   - Currently, the `PROXIES` list is empty, so the scraper will use your local IP, increasing the risk of being blocked.

4. **Configure MongoDB**:
   - Replace the MongoDB connection string in `src/database/mongo.py` with your own MongoDB Atlas or local MongoDB connection string.
   - Ensure the MongoDB database (`Web_Scraping`) and collection (`Phones`) are accessible.

5. **Run the Scraper and Save to MongoDB**:
   - Execute the main script to scrape phone data and store it in MongoDB:
     ```bash
     python main.py
     ```
   - This will:
     - Fetch phone links from predefined GSMArena search URLs.
     - Scrape specifications for each phone with reduced concurrency (2 requests at a time) and delays (3–6 seconds).
     - Rotate user agents to avoid detection.
     - Save the data to `phones.json`.
     - Process the data and store it in MongoDB.
   - Monitor the console for logs, especially for HTTP 429 (Too Many Requests) errors, which indicate rate-limiting.

6. **Run Visualizations**:
   - Launch the Streamlit app to view interactive visualizations:
     ```bash
     streamlit run src/visualization/plots.py
     ```
   - Open the provided URL (typically `http://localhost:8501`) in a web browser to explore the visualizations.

## Notes
- **Modularity**: The project is split into modules (`config`, `scraper`, `data`, `database`, `visualization`) to enhance maintainability and scalability.
- **Python Package Structure**: Each directory has an `__init__.py` file to make it a proper Python package, ensuring imports work correctly regardless of how the code is run.
- **Asynchronous Scraping**: Uses `aiohttp` for asynchronous HTTP requests, with a semaphore limiting concurrent requests to 2 and random delays of 3–6 seconds to minimize server load.
- **Rate Limit Handling**: The scraper detects rate limiting (HTTP 429) and exits gracefully with summary information about the scraping session.
- **User Agent Rotation**: Rotates between multiple user agents to mimic different browsers and reduce the risk of being blocked.
- **Error Handling**: Includes comprehensive error handling for network issues, parsing errors, and rate limiting.
- **MongoDB Integration**: Stores processed data in MongoDB for structured querying and analysis.
- **Streamlit Visualization**: Provides interactive visualizations for exploring phone data and trends.
- **Data Type Handling**: Ensures all data types are compatible with PyArrow for streamlined Streamlit rendering.
- **Currency Conversion**: Fetches live currency rates from `open.er-api.com` with fallbacks for API failures.
- **Data Storage**: Scraped data is stored in `phones.json` for persistence and loaded into MongoDB for structured storage.
- **Avoiding Blocks**:
  - Rotate user agents to mimic different browsers.
  - Keep `MAX_CONCURRENT_REQUESTS` low (currently 2) to avoid overwhelming the server.
  - Ensure `REQUEST_DELAY` is sufficiently long (3–6 seconds) to mimic human-like behavior.
  - Monitor logs for 429 errors and exit gracefully if rate-limiting is detected.
  - Consider running the scraper during off-peak hours for the target website.

## Troubleshooting Common Issues

### Import Errors
If you encounter "ModuleNotFoundError: No module named X", ensure:
1. All directories have `__init__.py` files
2. The code is run from the project root directory
3. For Streamlit, the path is correctly set in `plots.py` with:
   ```python
   sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
   ```

### Data Serialization Issues
If Streamlit shows "ArrowInvalid" errors or has trouble displaying data:
1. Ensure all data types are properly converted in `processor.py`
2. Use the fallback display method in `plots.py` which handles problematic columns
3. Install the latest version of `pyarrow` with `pip install -U pyarrow`

### MongoDB Connection Issues
If MongoDB connection fails:
1. Verify your connection string and credentials
2. Ensure your IP is whitelisted in MongoDB Atlas
3. Check network connectivity and firewall settings

## Code Explanation

### Purpose
The project collects, processes, and analyzes smartphone specifications from GSMArena to provide insights into phone performance, pricing, and features. It targets phones across various price ranges, extracts key specifications (e.g., chipset, battery, display), and categorizes them into tiers (Budget, Mid-Range, Premium, Flagship) using machine learning. The processed data is visualized to help users understand trends and compare phones.

### Workflow
1. **Configuration (`src/config/settings.py`)**:
   - Defines constants such as the base URL, search URLs, user agents, and scraping parameters.
   - Sets `MAX_CONCURRENT_REQUESTS` to 2 and `REQUEST_DELAY` to 3–6 seconds to reduce request rates.

2. **Web Scraping (`src/scraper/`)**:
   - **fetcher.py**:
     - `get_phone_links`: Fetches phone links from GSMArena search pages using `aiohttp`. Rotates user agents and handles rate limiting.
     - `scrape_phone`: Scrapes individual phone pages. Limits concurrency with a semaphore and adds delays.
     - `scrape`: Orchestrates scraping by fetching links, removing duplicates, scraping phone pages, and saving data to `phones.json`.
   - **parser.py**: Parses specifications into nested dictionaries.

3. **Data Processing (`src/data/`)**:
   - **loader.py**: Loads/saves JSON data.
   - **processor.py**: Converts JSON to a Pandas DataFrame, extracts specifications, and handles currency conversion. Also ensures data types are compatible with PyArrow.
   - **tier_assigner.py**: Assigns price tiers using KMeans clustering.

4. **Database Storage (`src/database/mongo.py`)**:
   - Saves processed data to MongoDB with upsert operations.

5. **Visualization (`src/visualization/plots.py`)**:
   - Creates interactive visualizations using Streamlit and Plotly (e.g., Price vs Score, Battery vs Charge Speed, Display Types).

6. **Main Execution (`main.py`)**:
   - Runs scraping and MongoDB storage, exiting on critical errors.

### Key Features
- **Low-Impact Scraping**: Limits concurrent requests to 2, adds 3–6 second delays to avoid rate-limiting.
- **User Agent Rotation**: Rotates between different user agents to mimic different browsers.
- **Rate Limit Detection**: Detects HTTP 429 responses and exits gracefully.
- **Data Cleaning**: Extracts and cleans specifications using regex and Pandas.
- **Machine Learning**: Uses KMeans for price tier assignment.
- **Interactive Visualizations**: Provides user-friendly plots via Streamlit.
- **Database Integration**: Stores data in MongoDB with upsert to prevent duplicates.
- **Type Safety**: Ensures all data types are compatible with PyArrow for Streamlit rendering.

### Technical Details
- **Dependencies**: Key libraries include `aiohttp`, `BeautifulSoup`, `pandas`, `scikit-learn`, `pymongo`, `plotly`, `streamlit`, `pyarrow`, and `tenacity`.
- **Asynchronous Design**: Uses coroutines and semaphores for efficient concurrency management.
- **Data Imputation**: Uses group means for imputation of missing values like scores.
- **Visualization Styling**: Customizes plots with consistent colors and layouts.
- **Package Structure**: Uses `__init__.py` files to enable proper Python importing.

### Potential Improvements
- **Proxy Implementation**: Implement and utilize the currently empty `PROXIES` list to distribute requests across multiple IP addresses.
- **Adaptive Rate Limiting**: Implement dynamic delays based on response patterns.
- **Testing**: Add unit and integration tests for scraping, processing, and visualization components.
- **Dockerization**: Create a Docker container for consistent deployment.
- **API Development**: Build a REST API to expose the data for other applications.
- **Data Caching**: Add caching for processed data to improve visualization performance.

## Conclusion
This project provides a robust pipeline for scraping, processing, storing, and visualizing smartphone data while implementing strategies to reduce the risk of being blocked by GSMArena. Its modular design, proper package structure, and cautious scraping approach enhance reliability and maintainability.