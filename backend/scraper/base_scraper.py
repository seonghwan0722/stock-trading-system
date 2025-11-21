"""
Base Scraper Class
Provides common functionality for all web scrapers
"""
import requests
from bs4 import BeautifulSoup
import time
import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseScraper:
    """Base class for all scrapers"""

    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }

    def get_page(self, url: str, params: Optional[Dict] = None) -> Optional[BeautifulSoup]:
        """
        Fetch a webpage and return BeautifulSoup object

        Args:
            url: Target URL
            params: Query parameters

        Returns:
            BeautifulSoup object or None if error
        """
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()

            # Rate limiting
            time.sleep(1)

            return BeautifulSoup(response.content, 'html.parser')

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def get_json(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Fetch JSON data from API endpoint

        Args:
            url: API endpoint URL
            params: Query parameters

        Returns:
            JSON data as dict or None if error
        """
        try:
            logger.info(f"Fetching JSON: {url}")
            response = self.session.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()

            # Rate limiting
            time.sleep(1)

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching JSON from {url}: {e}")
            return None

    def close(self):
        """Close the session"""
        self.session.close()
