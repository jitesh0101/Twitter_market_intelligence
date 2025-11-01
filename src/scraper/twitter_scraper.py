# """
# Twitter/X scraper using Selenium with anti-detection measures.
# Scrapes tweets based on hashtags without using paid APIs.
# """

# import json
# import time
# from datetime import datetime
# from pathlib import Path
# from typing import Dict, List, Optional, Set

# from bs4 import BeautifulSoup
# from selenium.common.exceptions import (
#     NoSuchElementException,
#     TimeoutException,
#     WebDriverException
# )
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.support.ui import WebDriverWait

# from ..utils import (
#     Logger,
#     human_delay,
#     generate_hash,
#     is_valid_tweet_content,
#     ProgressTracker
# )
# from .anti_detection import StealthDriver, HumanBehavior


# class TwitterScraper:
#     """Scrapes Twitter/X for market intelligence data."""
    
#     TWITTER_SEARCH_URL = "https://twitter.com/search"
    
#     def __init__(self, config: dict, logger: Optional[Logger] = None):
#         """
#         Initialize Twitter scraper.
        
#         Args:
#             config: Configuration dictionary
#             logger: Logger instance
#         """
#         self.config = config
#         self.logger = logger or Logger.get_logger("TwitterScraper")
        
#         # Extract configuration
#         self.scraper_config = config.get("scraper", {})
#         self.browser_config = self.scraper_config.get("browser", {})
#         self.anti_detection_config = self.scraper_config.get("anti_detection", {})
#         self.rate_limit_config = self.scraper_config.get("rate_limit", {})
#         self.checkpoint_config = self.scraper_config.get("checkpoint", {})
        
#         # Initialize driver
#         self.stealth_driver = StealthDriver(
#             headless=self.browser_config.get("headless", True),
#             user_agent_rotation=self.browser_config.get("user_agent_rotation", True),
#             window_size=self.browser_config.get("window_size", "1920,1080")
#         )
#         self.driver = None
        
#         # Tracking
#         self.collected_tweets: List[Dict] = []
#         self.seen_tweet_ids: Set[str] = set()
#         self.request_count = 0
#         self.last_request_time = time.time()
        
#         self.logger.info("TwitterScraper initialized")
    
#     def initialize_driver(self):
#         """Initialize the Selenium driver."""
#         try:
#             self.logger.info("Initializing Selenium driver...")
#             self.driver = self.stealth_driver.create_driver()
#             self.logger.info("Driver initialized successfully")
#         except Exception as e:
#             self.logger.error(f"Failed to initialize driver: {e}")
#             raise
    
#     def scrape_hashtags(
#         self,
#         hashtags: List[str],
#         target_count: int = 2000,
#         time_window_hours: int = 24
#     ) -> List[Dict]:
#         """
#         Scrape tweets for given hashtags.
        
#         Args:
#             hashtags: List of hashtags to search
#             target_count: Target number of tweets to collect
#             time_window_hours: Time window in hours to search
            
#         Returns:
#             List of tweet dictionaries
#         """
#         self.logger.info(f"Starting scrape for {len(hashtags)} hashtags, target: {target_count} tweets")
        
#         if not self.driver:
#             self.initialize_driver()
        
#         tweets_per_hashtag = target_count // len(hashtags)
        
#         for hashtag in hashtags:
#             self.logger.info(f"Scraping hashtag: {hashtag}")
            
#             try:
#                 hashtag_tweets = self._scrape_single_hashtag(
#                     hashtag,
#                     target_count=tweets_per_hashtag,
#                     time_window_hours=time_window_hours
#                 )
                
#                 self.logger.info(f"Collected {len(hashtag_tweets)} tweets for {hashtag}")
                
#                 # Save checkpoint
#                 if self.checkpoint_config.get("enabled", True):
#                     self._save_checkpoint()
                
#                 # Check if we've reached target
#                 if len(self.collected_tweets) >= target_count:
#                     self.logger.info(f"Reached target count: {len(self.collected_tweets)}")
#                     break
                
#             except Exception as e:
#                 self.logger.error(f"Error scraping {hashtag}: {e}", exc_info=True)
#                 continue
        
#         self.logger.info(f"Scraping complete. Total tweets collected: {len(self.collected_tweets)}")
#         return self.collected_tweets
    
#     def _scrape_single_hashtag(
#         self,
#         hashtag: str,
#         target_count: int,
#         time_window_hours: int
#     ) -> List[Dict]:
#         """
#         Scrape tweets for a single hashtag.
        
#         Args:
#             hashtag: Hashtag to search (with or without #)
#             target_count: Target number of tweets
#             time_window_hours: Time window in hours
            
#         Returns:
#             List of tweet dictionaries
#         """
#         # Clean hashtag
#         search_term = hashtag.strip().lstrip('#')
        
#         # Build search URL with filters
#         # Using advanced search: recent tweets, not retweets
#         search_query = f"{search_term} -filter:retweets"
#         search_url = f"{self.TWITTER_SEARCH_URL}?q={search_query}&src=typed_query&f=live"
        
#         self.logger.info(f"Navigating to: {search_url}")
        
#         try:
#             self.driver.get(search_url)
#             human_delay(3, 5)  # Wait for page load
            
#             # Handle any popups/login prompts
#             self._handle_popups()
            
#             # Scroll and collect tweets
#             tweets_collected = 0
#             scroll_attempts = 0
#             max_scroll_attempts = self.rate_limit_config.get("max_continuous_scrolls", 50)
            
#             while tweets_collected < target_count and scroll_attempts < max_scroll_attempts:
#                 # Extract tweets from current page
#                 new_tweets = self._extract_tweets_from_page()
                
#                 if new_tweets:
#                     tweets_collected += len(new_tweets)
#                     self.logger.debug(f"Extracted {len(new_tweets)} new tweets. Total: {tweets_collected}/{target_count}")
                
#                 # Scroll down
#                 has_more = HumanBehavior.random_scroll(
#                     self.driver,
#                     scroll_pause_min=self.anti_detection_config.get("scroll_pause", {}).get("min", 1),
#                     scroll_pause_max=self.anti_detection_config.get("scroll_pause", {}).get("max", 3)
#                 )
                
#                 scroll_attempts += 1
                
#                 # Rate limiting
#                 self._enforce_rate_limit()
                
#                 # Check if we're stuck
#                 if scroll_attempts % 10 == 0:
#                     self.logger.info(f"Progress: {tweets_collected}/{target_count} tweets, scroll attempt {scroll_attempts}")
                
#                 # Break if no more content
#                 if not has_more and scroll_attempts > 5:
#                     self.logger.warning("No more content available")
#                     break
            
#             return [t for t in self.collected_tweets if hashtag.lower() in t.get('hashtags_lower', [])]
            
#         except Exception as e:
#             self.logger.error(f"Error during scraping: {e}", exc_info=True)
#             return []
    
#     def _extract_tweets_from_page(self) -> List[Dict]:
#         """
#         Extract tweets from the current page.
        
#         Returns:
#             List of newly extracted tweets
#         """
#         new_tweets = []
        
#         try:
#             # Get page HTML
#             html = self.driver.page_source
#             soup = BeautifulSoup(html, 'lxml')
            
#             # Find tweet articles (Twitter's structure uses article tags for tweets)
#             articles = soup.find_all('article', attrs={'data-testid': 'tweet'})
            
#             if not articles:
#                 # Fallback: try finding by role
#                 articles = soup.find_all('article', role='article')
            
#             self.logger.debug(f"Found {len(articles)} article elements")
            
#             for article in articles:
#                 try:
#                     tweet_data = self._parse_tweet_element(article)
                    
#                     if tweet_data and self._is_new_tweet(tweet_data):
#                         self.collected_tweets.append(tweet_data)
#                         new_tweets.append(tweet_data)
#                         self.seen_tweet_ids.add(tweet_data['tweet_id'])
                        
#                 except Exception as e:
#                     self.logger.debug(f"Error parsing tweet: {e}")
#                     continue
            
#         except Exception as e:
#             self.logger.error(f"Error extracting tweets: {e}")
        
#         return new_tweets
    
#     def _parse_tweet_element(self, article) -> Optional[Dict]:
#         """
#         Parse a single tweet article element.
        
#         Args:
#             article: BeautifulSoup article element
            
#         Returns:
#             Tweet dictionary or None
#         """
#         try:
#             # Extract username
#             username = None
#             username_elem = article.find('div', attrs={'data-testid': 'User-Name'})
#             if username_elem:
#                 username_link = username_elem.find('a')
#                 if username_link and 'href' in username_link.attrs:
#                     username = username_link['href'].strip('/').split('/')[0]
            
#             # Extract tweet text
#             content = None
#             tweet_text_elem = article.find('div', attrs={'data-testid': 'tweetText'})
#             if tweet_text_elem:
#                 content = tweet_text_elem.get_text(strip=True)
            
#             # Validate content
#             if not is_valid_tweet_content(content):
#                 return None
            
#             # Extract timestamp
#             timestamp = None
#             time_elem = article.find('time')
#             if time_elem and 'datetime' in time_elem.attrs:
#                 timestamp = time_elem['datetime']
            
#             # Extract engagement metrics
#             engagement = self._extract_engagement_metrics(article)
            
#             # Extract hashtags and mentions
#             hashtags = self._extract_hashtags(tweet_text_elem) if tweet_text_elem else []
#             mentions = self._extract_mentions(tweet_text_elem) if tweet_text_elem else []
            
#             # Generate unique ID
#             tweet_id = generate_hash(f"{username}_{content}_{timestamp}")
            
#             tweet_data = {
#                 'tweet_id': tweet_id,
#                 'username': username or 'unknown',
#                 'timestamp': timestamp or datetime.now().isoformat(),
#                 'content': content,
#                 'hashtags': hashtags,
#                 'hashtags_lower': [h.lower() for h in hashtags],
#                 'mentions': mentions,
#                 'likes': engagement.get('likes', 0),
#                 'retweets': engagement.get('retweets', 0),
#                 'replies': engagement.get('replies', 0),
#                 'views': engagement.get('views', 0),
#                 'scraped_at': datetime.now().isoformat()
#             }
            
#             return tweet_data
            
#         except Exception as e:
#             self.logger.debug(f"Error parsing tweet element: {e}")
#             return None
    
#     def _extract_engagement_metrics(self, article) -> Dict[str, int]:
#         """Extract engagement metrics from tweet article."""
#         from ..utils.helpers import parse_engagement_count
        
#         metrics = {
#             'likes': 0,
#             'retweets': 0,
#             'replies': 0,
#             'views': 0
#         }
        
#         try:
#             # Find all buttons/spans with aria-label containing numbers
#             buttons = article.find_all(['button', 'span', 'div'], attrs={'aria-label': True})
            
#             for button in buttons:
#                 label = button.get('aria-label', '').lower()
                
#                 if 'like' in label or 'likes' in label:
#                     metrics['likes'] = parse_engagement_count(button.get_text())
#                 elif 'retweet' in label or 'repost' in label:
#                     metrics['retweets'] = parse_engagement_count(button.get_text())
#                 elif 'repl' in label:
#                     metrics['replies'] = parse_engagement_count(button.get_text())
#                 elif 'view' in label:
#                     metrics['views'] = parse_engagement_count(button.get_text())
        
#         except Exception:
#             pass
        
#         return metrics
    
#     def _extract_hashtags(self, element) -> List[str]:
#         """Extract hashtags from tweet element."""
#         hashtags = []
#         try:
#             hashtag_links = element.find_all('a', href=lambda x: x and '/hashtag/' in x)
#             for link in hashtag_links:
#                 hashtag = link.get_text(strip=True)
#                 if hashtag.startswith('#'):
#                     hashtags.append(hashtag)
#         except Exception:
#             pass
#         return hashtags
    
#     def _extract_mentions(self, element) -> List[str]:
#         """Extract mentions from tweet element."""
#         mentions = []
#         try:
#             mention_links = element.find_all('a', href=lambda x: x and x.startswith('/') and not '/hashtag/' in x)
#             for link in mention_links:
#                 mention = link.get_text(strip=True)
#                 if mention.startswith('@'):
#                     mentions.append(mention)
#         except Exception:
#             pass
#         return mentions
    
#     def _is_new_tweet(self, tweet_data: Dict) -> bool:
#         """Check if tweet is new (not already collected)."""
#         return tweet_data['tweet_id'] not in self.seen_tweet_ids
    
#     def _handle_popups(self):
#         """Handle any popups or modals that appear."""
#         try:
#             # Try to close login popup if it appears
#             close_buttons = self.driver.find_elements(By.CSS_SELECTOR, '[aria-label="Close"]')
#             for button in close_buttons:
#                 try:
#                     button.click()
#                     human_delay(0.5, 1)
#                 except Exception:
#                     pass
#         except Exception:
#             pass
    
#     def _enforce_rate_limit(self):
#         """Enforce rate limiting to avoid detection."""
#         current_time = time.time()
#         time_since_last = current_time - self.last_request_time
        
#         min_delay = 60.0 / self.rate_limit_config.get("requests_per_minute", 30)
        
#         if time_since_last < min_delay:
#             sleep_time = min_delay - time_since_last
#             time.sleep(sleep_time)
        
#         self.last_request_time = time.time()
#         self.request_count += 1
    
#     def _save_checkpoint(self):
#         """Save current progress to checkpoint file."""
#         if not self.checkpoint_config.get("enabled", True):
#             return
        
#         try:
#             checkpoint_dir = Path(self.checkpoint_config.get("save_path", "data/raw/checkpoints"))
#             checkpoint_dir.mkdir(parents=True, exist_ok=True)
            
#             checkpoint_file = checkpoint_dir / f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
#             with open(checkpoint_file, 'w', encoding='utf-8') as f:
#                 json.dump({
#                     'tweets': self.collected_tweets,
#                     'seen_ids': list(self.seen_tweet_ids),
#                     'count': len(self.collected_tweets),
#                     'timestamp': datetime.now().isoformat()
#                 }, f, ensure_ascii=False, indent=2)
            
#             self.logger.info(f"Checkpoint saved: {checkpoint_file}")
            
#         except Exception as e:
#             self.logger.error(f"Error saving checkpoint: {e}")
    
#     def close(self):
#         """Close the scraper and cleanup resources."""
#         self.logger.info("Closing scraper...")
#         if self.driver:
#             self.stealth_driver.close()
#         self.logger.info("Scraper closed")
    
#     def __enter__(self):
#         """Context manager entry."""
#         self.initialize_driver()
#         return self
    
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         """Context manager exit."""
#         self.close()




"""
Twitter/X scraper using Selenium with anti-detection measures.
Scrapes tweets based on hashtags without using paid APIs.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# if you want automatic driver matching, uncomment these:
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager

from ..utils import (
    Logger,
    human_delay,
    generate_hash,
    is_valid_tweet_content,
    ProgressTracker
)
# we still import this if you are using some of its helpers,
# but we are NOT going to use StealthDriver.create_driver() anymore
# from .anti_detection import StealthDriver, HumanBehavior
from .anti_detection import HumanBehavior  # keep HumanBehavior only


class TwitterScraper:
    """Scrapes Twitter/X for market intelligence data."""

    TWITTER_SEARCH_URL = "https://twitter.com/search"

    def __init__(self, config: dict, logger: Optional[Logger] = None):
        """
        Initialize Twitter scraper.

        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or Logger.get_logger("TwitterScraper")

        # Extract configuration
        self.scraper_config = config.get("scraper", {})
        self.browser_config = self.scraper_config.get("browser", {})
        self.anti_detection_config = self.scraper_config.get("anti_detection", {})
        self.rate_limit_config = self.scraper_config.get("rate_limit", {})
        self.checkpoint_config = self.scraper_config.get("checkpoint", {})

        # we will NOT create StealthDriver here anymore
        # self.stealth_driver = StealthDriver(...)
        self.driver = None

        # Tracking
        self.collected_tweets: List[Dict] = []
        self.seen_tweet_ids: Set[str] = set()
        self.request_count = 0
        self.last_request_time = time.time()

        self.logger.info("TwitterScraper initialized")

    # ---------------------------------------------------------------------
    # NEW: driver setup method you wanted to use
    # ---------------------------------------------------------------------
    def setup_driver(self):
        """Setup Chrome driver with optimized options"""
        chrome_options = Options()

        # you said you wanted headless — leave it on, can toggle from config
        # Remove headless for debugging - you can add it back later
        # if self.browser_config.get("headless", True):
        # chrome_options.add_argument("--headless")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36"
        )

        try:
            # simplest: use system chromedriver
            driver = webdriver.Chrome(options=chrome_options)

            # if your Chrome/ChromeDriver mismatch keeps happening,
            # uncomment this block and comment the line above:
            #
            # service = Service(ChromeDriverManager().install())
            # driver = webdriver.Chrome(service=service, options=chrome_options)

            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            return driver
        except Exception as e:
            self.logger.error(f"Error setting up driver: {e}")
            raise

    def initialize_driver(self):
        """Initialize the Selenium driver."""
        try:
            self.logger.info("Initializing Selenium driver...")
            # OLD (problematic) way:
            # self.driver = self.stealth_driver.create_driver()

            # NEW way: use the setup_driver you provided
            self.driver = self.setup_driver()
            self.logger.info("Driver initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize driver: {e}")
            raise

    # ---------------------------------------------------------------------
    # scraping logic BELOW stays almost the same
    # ---------------------------------------------------------------------
    def scrape_hashtags(
        self,
        hashtags: List[str],
        target_count: int = 2000,
        time_window_hours: int = 24
    ) -> List[Dict]:
        """
        Scrape tweets for given hashtags.
        """
        self.logger.info(
            f"Starting scrape for {len(hashtags)} hashtags, target: {target_count} tweets"
        )

        if not self.driver:
            self.initialize_driver()

        tweets_per_hashtag = target_count // len(hashtags)

        for hashtag in hashtags:
            self.logger.info(f"Scraping hashtag: {hashtag}")

            try:
                hashtag_tweets = self._scrape_single_hashtag(
                    hashtag,
                    target_count=tweets_per_hashtag,
                    time_window_hours=time_window_hours
                )

                self.logger.info(
                    f"Collected {len(hashtag_tweets)} tweets for {hashtag}"
                )

                # Save checkpoint
                if self.checkpoint_config.get("enabled", True):
                    self._save_checkpoint()

                # Check if we've reached target
                if len(self.collected_tweets) >= target_count:
                    self.logger.info(
                        f"Reached target count: {len(self.collected_tweets)}"
                    )
                    break

            except Exception as e:
                self.logger.error(f"Error scraping {hashtag}: {e}", exc_info=True)
                continue

        self.logger.info(
            f"Scraping complete. Total tweets collected: {len(self.collected_tweets)}"
        )
        return self.collected_tweets

    def _scrape_single_hashtag(
        self,
        hashtag: str,
        target_count: int,
        time_window_hours: int
    ) -> List[Dict]:
        """Scrape tweets for a single hashtag."""
        search_term = hashtag.strip().lstrip('#')

        # Using advanced search: recent tweets, not retweets
        search_query = f"{search_term} -filter:retweets"
        search_url = (
            f"{self.TWITTER_SEARCH_URL}?q={search_query}&src=typed_query&f=live"
        )

        self.logger.info(f"Navigating to: {search_url}")

        try:
            self.driver.get(search_url)
            human_delay(3, 5)  # Wait for page load

            # Handle any popups/login prompts
            self._handle_popups()

            # Scroll and collect tweets
            tweets_collected = 0
            scroll_attempts = 0
            max_scroll_attempts = self.rate_limit_config.get(
                "max_continuous_scrolls", 50
            )

            while tweets_collected < target_count and scroll_attempts < max_scroll_attempts:
                # Extract tweets from current page
                new_tweets = self._extract_tweets_from_page()

                if new_tweets:
                    tweets_collected += len(new_tweets)
                    self.logger.debug(
                        f"Extracted {len(new_tweets)} new tweets. "
                        f"Total: {tweets_collected}/{target_count}"
                    )

                # Scroll down (we kept HumanBehavior from your anti_detection)
                has_more = HumanBehavior.random_scroll(
                    self.driver,
                    scroll_pause_min=self.anti_detection_config
                    .get("scroll_pause", {})
                    .get("min", 1),
                    scroll_pause_max=self.anti_detection_config
                    .get("scroll_pause", {})
                    .get("max", 3)
                )

                scroll_attempts += 1

                # Rate limiting
                self._enforce_rate_limit()

                if scroll_attempts % 10 == 0:
                    self.logger.info(
                        f"Progress: {tweets_collected}/{target_count} tweets, "
                        f"scroll attempt {scroll_attempts}"
                    )

                # Break if no more content
                if not has_more and scroll_attempts > 5:
                    self.logger.warning("No more content available")
                    break

            # filter the ones for this hashtag
            return [
                t for t in self.collected_tweets
                if hashtag.lower() in t.get('hashtags_lower', [])
            ]

        except Exception as e:
            self.logger.error(f"Error during scraping: {e}", exc_info=True)
            return []

    def _extract_tweets_from_page(self) -> List[Dict]:
        """Extract tweets from the current page."""
        new_tweets = []

        try:
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'lxml')

            # Find tweet articles
            articles = soup.find_all('article', attrs={'data-testid': 'tweet'})
            if not articles:
                articles = soup.find_all('article', role='article')

            self.logger.debug(f"Found {len(articles)} article elements")

            for article in articles:
                try:
                    tweet_data = self._parse_tweet_element(article)

                    if tweet_data and self._is_new_tweet(tweet_data):
                        self.collected_tweets.append(tweet_data)
                        new_tweets.append(tweet_data)
                        self.seen_tweet_ids.add(tweet_data['tweet_id'])

                except Exception as e:
                    self.logger.debug(f"Error parsing tweet: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error extracting tweets: {e}")

        return new_tweets

    def _parse_tweet_element(self, article) -> Optional[Dict]:
        """Parse a single tweet article element."""
        try:
            # Extract username
            username = None
            username_elem = article.find('div', attrs={'data-testid': 'User-Name'})
            if username_elem:
                username_link = username_elem.find('a')
                if username_link and 'href' in username_link.attrs:
                    username = username_link['href'].strip('/').split('/')[0]

            # Extract tweet text
            content = None
            tweet_text_elem = article.find('div', attrs={'data-testid': 'tweetText'})
            if tweet_text_elem:
                content = tweet_text_elem.get_text(strip=True)

            # Validate content
            if not is_valid_tweet_content(content):
                return None

            # Extract timestamp
            timestamp = None
            time_elem = article.find('time')
            if time_elem and 'datetime' in time_elem.attrs:
                timestamp = time_elem['datetime']

            # Extract engagement metrics
            engagement = self._extract_engagement_metrics(article)

            # Extract hashtags and mentions
            hashtags = self._extract_hashtags(tweet_text_elem) if tweet_text_elem else []
            mentions = self._extract_mentions(tweet_text_elem) if tweet_text_elem else []

            # Generate unique ID
            tweet_id = generate_hash(f"{username}_{content}_{timestamp}")

            tweet_data = {
                'tweet_id': tweet_id,
                'username': username or 'unknown',
                'timestamp': timestamp or datetime.now().isoformat(),
                'content': content,
                'hashtags': hashtags,
                'hashtags_lower': [h.lower() for h in hashtags],
                'mentions': mentions,
                'likes': engagement.get('likes', 0),
                'retweets': engagement.get('retweets', 0),
                'replies': engagement.get('replies', 0),
                'views': engagement.get('views', 0),
                'scraped_at': datetime.now().isoformat()
            }

            return tweet_data

        except Exception as e:
            self.logger.debug(f"Error parsing tweet element: {e}")
            return None

    def _extract_engagement_metrics(self, article) -> Dict[str, int]:
        """Extract engagement metrics from tweet article."""
        from ..utils.helpers import parse_engagement_count

        metrics = {
            'likes': 0,
            'retweets': 0,
            'replies': 0,
            'views': 0
        }

        try:
            buttons = article.find_all(['button', 'span', 'div'], attrs={'aria-label': True})

            for button in buttons:
                label = button.get('aria-label', '').lower()

                if 'like' in label or 'likes' in label:
                    metrics['likes'] = parse_engagement_count(button.get_text())
                elif 'retweet' in label or 'repost' in label:
                    metrics['retweets'] = parse_engagement_count(button.get_text())
                elif 'repl' in label:
                    metrics['replies'] = parse_engagement_count(button.get_text())
                elif 'view' in label:
                    metrics['views'] = parse_engagement_count(button.get_text())

        except Exception:
            pass

        return metrics

    def _extract_hashtags(self, element) -> List[str]:
        """Extract hashtags from tweet element."""
        hashtags = []
        try:
            hashtag_links = element.find_all('a', href=lambda x: x and '/hashtag/' in x)
            for link in hashtag_links:
                hashtag = link.get_text(strip=True)
                if hashtag.startswith('#'):
                    hashtags.append(hashtag)
        except Exception:
            pass
        return hashtags

    def _extract_mentions(self, element) -> List[str]:
        """Extract mentions from tweet element."""
        mentions = []
        try:
            mention_links = element.find_all(
                'a',
                href=lambda x: x and x.startswith('/') and '/hashtag/' not in x
            )
            for link in mention_links:
                mention = link.get_text(strip=True)
                if mention.startswith('@'):
                    mentions.append(mention)
        except Exception:
            pass
        return mentions

    def _is_new_tweet(self, tweet_data: Dict) -> bool:
        """Check if tweet is new (not already collected)."""
        return tweet_data['tweet_id'] not in self.seen_tweet_ids

    def _handle_popups(self):
        """Handle any popups or modals that appear."""
        try:
            close_buttons = self.driver.find_elements(By.CSS_SELECTOR, '[aria-label="Close"]')
            for button in close_buttons:
                try:
                    button.click()
                    human_delay(0.5, 1)
                except Exception:
                    pass
        except Exception:
            pass

    def _enforce_rate_limit(self):
        """Enforce rate limiting to avoid detection."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        min_delay = 60.0 / self.rate_limit_config.get("requests_per_minute", 30)

        if time_since_last < min_delay:
            sleep_time = min_delay - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()
        self.request_count += 1

    def _save_checkpoint(self):
        """Save current progress to checkpoint file."""
        if not self.checkpoint_config.get("enabled", True):
            return

        try:
            checkpoint_dir = Path(self.checkpoint_config.get("save_path", "data/raw/checkpoints"))
            checkpoint_dir.mkdir(parents=True, exist_ok=True)

            checkpoint_file = checkpoint_dir / f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'tweets': self.collected_tweets,
                    'seen_ids': list(self.seen_tweet_ids),
                    'count': len(self.collected_tweets),
                    'timestamp': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Checkpoint saved: {checkpoint_file}")

        except Exception as e:
            self.logger.error(f"Error saving checkpoint: {e}")

    def close(self):
        """Close the scraper and cleanup resources."""
        self.logger.info("Closing scraper...")
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
        self.logger.info("Scraper closed")

    def __enter__(self):
        """Context manager entry."""
        self.initialize_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
