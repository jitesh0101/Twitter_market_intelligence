"""
Anti-detection utilities for web scraping.
Implements stealth techniques to avoid bot detection.
"""

import random
from typing import Optional

import undetected_chromedriver as uc
from fake_useragent import UserAgent
from selenium.webdriver.chrome.options import Options


class StealthDriver:
    """Selenium driver with anti-detection capabilities."""
    
    # Common screen resolutions
    SCREEN_RESOLUTIONS = [
        "1920,1080",
        "1366,768",
        "1536,864",
        "1440,900",
        "1280,720",
    ]
    
    # Languages
    LANGUAGES = [
        "en-US,en;q=0.9",
        "en-GB,en;q=0.9",
        "en-IN,en;q=0.9,hi;q=0.8",
    ]
    
    def __init__(
        self,
        headless: bool = True,
        user_agent_rotation: bool = True,
        window_size: Optional[str] = None,
        logger = None
    ):
        """
        Initialize stealth driver configuration.
        
        Args:
            headless: Run browser in headless mode
            user_agent_rotation: Rotate user agents
            window_size: Browser window size (e.g., "1920,1080")
            logger: Logger instance
        """
        self.headless = headless
        self.user_agent_rotation = user_agent_rotation
        self.window_size = window_size or random.choice(self.SCREEN_RESOLUTIONS)
        self.driver: Optional[uc.Chrome] = None
        self.logger = logger
    
    def create_driver(self) -> uc.Chrome:
        """
        Create and configure an undetected Chrome driver.
        
        Returns:
            Configured Chrome WebDriver instance
        """
        options = self._get_chrome_options()
        
        try:
            # Use undetected-chromedriver with auto version detection
            self.driver = uc.Chrome(
                options=options,
                driver_executable_path=None,  # Auto-download correct version
                browser_executable_path=None,  # Auto-detect Chrome installation
                use_subprocess=True,
                version_main=None  # Auto-detect Chrome version
            )
        except Exception as e:
            # If auto-detection fails, try without version specification
            if self.logger:
                self.logger.warning(f"First attempt failed: {e}, trying alternative method...")
            self.driver = uc.Chrome(
                options=options,
                use_subprocess=False
            )
        
        # Additional stealth configurations
        self._apply_stealth_scripts()
        
        return self.driver
    
    def _get_chrome_options(self) -> Options:
        """
        Configure Chrome options for stealth.
        
        Returns:
            Configured ChromeOptions
        """
        options = uc.ChromeOptions()
        
        # Basic options
        if self.headless:
            options.add_argument('--headless=new')
        
        options.add_argument(f'--window-size={self.window_size}')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # User agent
        if self.user_agent_rotation:
            ua = UserAgent()
            user_agent = ua.random
            options.add_argument(f'user-agent={user_agent}')
        
        # Language
        language = random.choice(self.LANGUAGES)
        options.add_argument(f'--lang={language.split(",")[0]}')
        
        # Note: experimental options removed for compatibility
        # undetected-chromedriver handles anti-detection automatically
        
        return options
    
    def _apply_stealth_scripts(self):
        """Apply JavaScript stealth scripts to hide automation."""
        if not self.driver:
            return
        
        try:
            # Override navigator.webdriver
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                '''
            })
        except Exception as e:
            # CDP commands may not work in older Chrome versions
            # undetected-chromedriver handles this internally
            pass
    
    def close(self):
        """Close the driver."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass


class HumanBehavior:
    """Simulate human-like browsing behavior."""
    
    @staticmethod
    def random_scroll(driver, scroll_pause_min: float = 1.0, scroll_pause_max: float = 3.0):
        """
        Perform random scrolling to simulate human behavior.
        
        Args:
            driver: Selenium WebDriver instance
            scroll_pause_min: Minimum pause between scrolls
            scroll_pause_max: Maximum pause between scrolls
        """
        import time
        
        # Get current scroll position
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        # Random scroll amount (not always to bottom)
        scroll_amount = random.randint(300, 800)
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        
        # Random pause
        pause_time = random.uniform(scroll_pause_min, scroll_pause_max)
        time.sleep(pause_time)
        
        return driver.execute_script("return document.body.scrollHeight") != last_height
    
    @staticmethod
    def random_mouse_movement(driver):
        """
        Simulate random mouse movements (limited in headless mode).
        
        Args:
            driver: Selenium WebDriver instance
        """
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            
            actions = ActionChains(driver)
            
            # Random movements
            for _ in range(random.randint(2, 5)):
                x_offset = random.randint(-100, 100)
                y_offset = random.randint(-100, 100)
                actions.move_by_offset(x_offset, y_offset)
            
            actions.perform()
        except Exception:
            pass  # Ignore if fails (e.g., in headless mode)
    
    @staticmethod
    def random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0):
        """
        Random delay between actions.
        
        Args:
            min_seconds: Minimum delay
            max_seconds: Maximum delay
        """
        import time
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    @staticmethod
    def gradual_scroll_to_bottom(driver, scroll_pause_min: float = 1.0, scroll_pause_max: float = 2.0):
        """
        Gradually scroll to bottom of page.
        
        Args:
            driver: Selenium WebDriver instance
            scroll_pause_min: Minimum pause between scrolls
            scroll_pause_max: Maximum pause between scrolls
            
        Returns:
            True if reached bottom, False otherwise
        """
        import time
        
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        # Scroll in increments
        for _ in range(random.randint(3, 6)):
            HumanBehavior.random_scroll(driver, scroll_pause_min, scroll_pause_max)
        
        # Check if we've reached the bottom
        new_height = driver.execute_script("return document.body.scrollHeight")
        return new_height == last_height


def get_random_user_agent() -> str:
    """
    Get a random user agent string.
    
    Returns:
        Random user agent
    """
    ua = UserAgent()
    return ua.random
