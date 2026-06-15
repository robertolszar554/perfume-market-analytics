# Fragrantica Scraper Component

This folder contains the automated web scraping subsystem designed to robustly extract comprehensive perfume profiles, consumer votes, and accord data. Built using **Selenium**, the scraper mimics human behavior to handle dynamic JavaScript-heavy content and navigate around strict anti-bot systems.

## Directory Structure & Component Breakdown

Based on the core files in this module, the scraping process is split into distinct stages for optimization and fault tolerance:

* **`create_fragrance_list.py`**: The initial discovery script. It crawls catalog pages, handles pagination, and collects target perfume URLs using Selenium, saving them directly to `fragrance_links.txt`.
* **`main.py`**: The primary execution engine. It loops through the extracted URLs, interacts with the dynamic page elements (tabs, hidden metrics), extracts voter distributions via DOM manipulation, and dumps the structured records into `raw_data.csv`.
* **`fragrance_links_queue.txt`**: Acts as a state-preserving queue. It tracks which links are pending or processed, ensuring the scraper can safely resume from the exact same spot if interrupted.
* **`failed_links.txt`**: A dedicated error-logging mechanism that isolates broken links, incomplete perfume data sets or timeouts for targeted retries, preventing data loss.
* **`/screenshots`**: An automated debugging directory where the system captures page states upon encountering unexpected errors or Cloudflare blocks.

---

## Key Technical Features

### 1. Robust State Management & Resiliency
Scraping over 5,000 deep web pages takes time. By utilizing a file-based queue system, the scraper is pretty stateless and resilient.

### 3. Dynamic Content & Anti-Bot Bypassing
*   **Asynchronous Content:** Handled dynamic tabs and "Show More" buttons using Selenium's Explicit Waits.
*   **Human Mimicry:** Integrated randomized request delays, custom User-Agent rotation, and window sizing to minimize triggering automated Cloudflare/Incapsula challenges.
