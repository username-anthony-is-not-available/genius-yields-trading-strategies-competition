import logging
import re
from typing import Optional

from src.data_extraction.simple_web_scraper import SimpleWebScraper


class FearAndGreedIndexWebScraper:
    """
    A specialized web scraper for extracting the Cardano Fear and Greed Index from CFGI.io.

    This class demonstrates an implementation of a SimpleWebScraper to extract data from 
    external web sources. It specifically targets the Cardano Fear and Greed Index from 
    the CFGI.io website. This approach allows for data extraction from various online 
    sources beyond traditional APIs.

    Note:
    - Web scraping may be subject to legal and ethical considerations.
    - Always review and comply with the website's terms of service and robots.txt file.
    - Consider the impact of frequent requests on the target website's resources.
    - Web scraping can be fragile to changes in the website's structure.

    This class serves as an example of extending data sourcing capabilities beyond 
    conventional APIs, showcasing both the potential and limitations of web scraping 
    techniques in data extraction workflows.
    """
    def __init__(
        self,
        logger: logging.Logger,
    ):
        """
        Initialize the FearAndGreedIndexWebScraper.

        Args:
            logger (logging.Logger): Logger object for logging messages.
        """
        self.logger: logging.Logger = logger

    def get_value(self) -> Optional[int]:
        """
        Retrieves the current Cardano Fear and Greed Index value from CFGI.io.

        This method initializes a SimpleWebScraper with the specific URL and class selector
        for the Cardano Fear and Greed Index. It then attempts to scrape and extract the
        numeric value from the webpage.

        Returns:
            Optional[int]: The current Cardano Fear and Greed Index value as an integer.
                        Returns None if the value couldn't be retrieved or parsed.

        Raises:
            Any exceptions raised by SimpleWebScraper or the extraction process are not
            caught here and will propagate up.

        Note:
            - This method uses the `extract_number` static method to parse the scraped text.
        """
        url = 'https://cfgi.io/cardano-fear-greed-index/'
        # cspell:disable-next-line
        class_selector = 'apexcharts-datalabel-value'

        scraper = SimpleWebScraper(
            url=url,
            class_selector=class_selector,
            logger=self.logger,
            data_cleanup_func=self.extract_number
        )

        return scraper.get_value()

    @staticmethod
    def extract_number(text: str) -> Optional[int]:
        """
        Extract the numeric value from a string.

        Args:
            text (str): The string to extract the number from.

        Returns:
            Optional[int]: The extracted number as an integer, or None if no number is found.
        """
        match = re.search(r'\d+', text)
        return int(match.group()) if match else None
