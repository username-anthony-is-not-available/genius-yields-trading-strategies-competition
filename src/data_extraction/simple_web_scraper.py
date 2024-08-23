import logging
import time
from typing import Callable, Optional

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


class ScraperException(Exception):
    """Custom exception for scraper-related errors."""


class SimpleWebScraper:
    """
    A simple web scraper using Selenium WebDriver and BeautifulSoup with caching support.

    This class provides functionality to scrape data from a specified URL
    using a given CSS class selector, with an option for caching the results.

    Attributes:
        url (str): The URL of the page to scrape.
        class_selector (str): The CSS class selector for the target element.
        web_driver_wait_default_timeout (int): Default timeout for WebDriverWait.
        cache_timeout (int): Timeout for caching the result in seconds.
    """

    WEB_DRIVER_WAIT_DEFAULT_TIMEOUT: int = 15

    def __init__(
        self,
        url: str,
        class_selector: str,
        logger: logging.Logger,
        web_driver_wait_timeout: Optional[int] = None,
        cache_timeout: int = 3600,
        data_cleanup_func: Optional[Callable[[str], Optional[int]]] = None
    ):
        """
        Initialize the SimpleWebScraper.

        Args:
            url (str): The URL of the page to scrape.
            class_selector (str): The CSS class selector for the target element.
            logger (logging.Logger): Logger object for logging messages.
            web_driver_wait_timeout (Optional[int]): 
                Timeout for WebDriverWait. Defaults to WEB_DRIVER_WAIT_DEFAULT_TIMEOUT.
            cache_timeout (int): Timeout for caching the result in seconds. Defaults to 3600 seconds (1 hour).
            data_cleanup_func (Optional[Callable[[str], Optional[int]]]): 
                A function to clean up the extracted data. Defaults to a function that extracts numbers.
        """
        self.url: str = url
        self.class_selector: str = class_selector
        self.logger: logging.Logger = logger
        self.element_value: Optional[str] = None
        self.cache_timeout: int = cache_timeout
        self.cache_timestamp: Optional[float] = None
        self.web_driver_wait_timeout: int = web_driver_wait_timeout or self.WEB_DRIVER_WAIT_DEFAULT_TIMEOUT
        self.data_cleanup_func: Callable[[str], Optional[int]] = data_cleanup_func or self.default_data_cleanup
        self.logger.info("[SimpleWebScraper] Initializing WebDriver...")
        self.driver: webdriver.Chrome = self._init_driver()
        self.logger.info("[SimpleWebScraper] WebDriver initialized.")

    def _init_driver(self) -> webdriver.Chrome:
        """
        Initialize and return a Chrome WebDriver.

        Returns:
            webdriver.Chrome: An instance of Chrome WebDriver.
        """
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    @staticmethod
    def default_data_cleanup(text: str) -> Optional[any]:
        """
        Default data cleanup function that do nothing.

        It is recommended to provide a function for processing the extracted data.

        Args:
            text (str): The string to extract the information from.

        Returns:
            Optional[any]: The extracted information, or None if no information is found.
        """
        return text

    def fetch_page_content(self) -> str:
        """
        Fetch the page content from the URL.

        Returns:
            str: The HTML content of the page.

        Raises:
            ScraperException: If there's an error fetching the page content.
        """
        try:
            self.driver.get(self.url)
            WebDriverWait(self.driver, self.web_driver_wait_timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, self.class_selector))
            )
            return self.driver.page_source
        except Exception as e:
            self.logger.error(f"Error fetching page content: {e}")
            raise ScraperException(f"Failed to fetch page content: {e}") from e

    def parse_element_value(self, html_content: str) -> None:
        """
        Parse the value from the HTML content based on the specified class selector.

        Args:
            html_content (str): The HTML content to parse.

        Raises:
            ScraperException: If there's an error parsing the HTML content or if the target element is not found.
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            target_element = soup.find(class_=self.class_selector)
            if target_element:
                self.element_value = target_element.get_text(strip=True)
                self.logger.info(f"Successfully parsed element value: {self.element_value}")
            else:
                raise ScraperException("Could not find the target element on the page.")
        except Exception as e:
            self.logger.error(f"Error parsing HTML content: {e}")
            raise ScraperException(f"Failed to parse HTML content: {e}") from e

    def get_value(self) -> Optional[int]:
        """
        Get the processed value from the target element, with caching.

        Returns:
            Optional[int]: The processed value, or None if the value couldn't be retrieved.
        """
        current_time = time.time()
        if self.cache_timestamp and (current_time - self.cache_timestamp < self.cache_timeout):
            self.logger.info("Returning cached value.")
            return self.data_cleanup_func(self.element_value) if self.element_value else None

        try:
            with self.driver:
                html_content = self.fetch_page_content()
                if html_content:
                    self.parse_element_value(html_content)
                    self.cache_timestamp = current_time
                return self.data_cleanup_func(self.element_value) if self.element_value else None
        except ScraperException as e:
            self.logger.error(f"Scraper error: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()
