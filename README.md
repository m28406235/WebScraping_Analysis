# Smartphone Specs Analysis

## Project Idea

We will scrape smartphone specifications from https://www.gsmarena.com for all phones released in 2024-2025, clean and process the data, analyze trends, visualize results, and store them in a database. The goal is to study trends like 5G adoption, camera advancements, and price-performance relationships.

**Team**: \[A_M_O\]

## Data Description

- **Website**: GSMArena.com
- **Scope**: All phones released in 2024-2025
- **Format**: JSON
- **Sample** (Samsung Galaxy A56):
  - Name: "Samsung Galaxy A56"
  - Release: "2025, March 02"
  - Network: GSM, HSPA, LTE, 5G
  - Display: 6.7" Super AMOLED
  - Hardware: Exynos 1580, 6-12GB RAM
  - Camera: 50MP main, 12MP ultrawide
  - Battery: 5000 mAh
  - Price: $399.99
  - Benchmarks: AnTuTu 908689

## Approach

1. **Data Extraction**:

   - Scrape GSMArena using `BeautifulSoup` and `requests`, running the script multiple times with different search URLs to cover all 2024-2025 phones.
   - Extract specs (e.g., network, display, hardware), handling duplicates and errors.
   - Use rate-limiting and a VPN to manage occasional server blocks.
   - Save raw data as JSON with progress tracking (`tqdm`).

2. **Data Cleaning & Processing**:

   - Remove duplicates and handle missing values.
   - Use regex to:
     - Extract dates (e.g., "2025, March 02" → "2025-03-02").
     - Parse prices (e.g., "$ 399.99 / € 429.00").
     - Clean camera specs (e.g., "50 MP, f/1.8").
   - Tools: `pandas`, `re`.

3. **Data Analysis**:

   - Calculate stats for price, battery, etc.
   - Study 5G adoption, camera types, price vs. performance.
   - Tools: `pandas`, `numpy`.

4. **Data Visualization**:

   - Create bar charts (price by brand), scatter plots (price vs. benchmarks).
   - Tools: `matplotlib`, `seaborn`.

5. **Data Storage**:

   - Store in MongoDB using `pymongo`.
   - One document per phone.