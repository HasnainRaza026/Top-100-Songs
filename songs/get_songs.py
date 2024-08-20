import requests
from bs4 import BeautifulSoup
from utils.logger import logger

class Songs:
    def __init__(self, date):
        self.date = date
        self.url = f"https://www.billboard.com/charts/hot-100/{self.date}/"

    def get_100_songs(self):
        logger.info("Starting the process to scrape the top 100 songs.")

        try:
            response = self._get_html_content()
            soup = BeautifulSoup(response.content, "html.parser")
            return self._extract_song_titles(soup)
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
        except Exception as err:
            logger.error(f"An error occurred: {err}")
        return None

    def _get_html_content(self):
        logger.debug(f"Making GET request to URL: {self.url}")
        response = requests.get(self.url)
        response.raise_for_status()
        logger.info("HTML content scraped successfully.")
        return response

    def _extract_song_titles(self, soup):
        logger.debug("Extracting song titles from HTML.")
        song_titles = [
            title.find("ul").find("li").find("h3").getText().strip()
            for title in soup.findAll("li", class_="lrv-u-width-100p")
            if title.find("ul") and title.find("ul").find("li") and title.find("ul").find("li").find("h3")
        ]
        logger.info(f"Top 100 songs on {self.date} scraped successfully. Example titles: {song_titles[:3]}")
        return song_titles
