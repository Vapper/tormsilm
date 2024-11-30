from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import time
import json
import logging
from datetime import datetime
import random
import os
from fake_useragent import UserAgent
import undetected_chromedriver as uc
from urllib.parse import quote
from selenium.webdriver import ActionChains
import re
import time
import random
import json
import logging
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

class StealthFacebookCrawler:
    GROUP_URL = "https://www.facebook.com/groups/ilmahuvilised"

    def __init__(self, email, password, group_id):
        """Initialize the Facebook crawler with credentials"""
        self.email = email
        self.password = password
        self.group_id = group_id
        self.logger = self._setup_logger()
        self.driver = self._setup_driver()

    def _setup_logger(self):
        """Setup logger"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        # Add file handler if not already added
        if not logger.handlers:
            fh = logging.FileHandler('fb_crawler.log')
            fh.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        return logger

    def _setup_driver(self):
        """Set up and configure the Chrome WebDriver with stealth settings."""
        options = uc.ChromeOptions()
        
        # Basic Chrome arguments
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-gpu')
        
        # Set mobile user agent
        mobile_ua = 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36'
        options.add_argument(f'user-agent={mobile_ua}')
        
        # Create and configure the driver
        driver = uc.Chrome(options=options)
        driver.set_window_size(360, 640)
        
        # Inject anti-detection script
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver

    def random_delay(self):
        """Add random delay between actions to mimic human behavior"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            delay = random.uniform(self.min_delay, self.max_delay)
            time.sleep(delay)
        self.last_request_time = time.time()

    def random_scroll(self):
        """Perform random scrolling to mimic human behavior"""
        scroll_amount = random.randint(300, 700)
        self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        self.random_delay()

    def take_debug_screenshot(self, step_name):
        """Take a screenshot for debugging purposes"""
        try:
            filename = f"debug_{step_name}_{int(time.time())}.png"
            self.driver.save_screenshot(filename)
            self.logger.info(f"Debug screenshot saved: {filename}")
            # Also save page source
            with open(f"debug_{step_name}_{int(time.time())}.html", 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
        except Exception as e:
            self.logger.error(f"Failed to take debug screenshot: {str(e)}")

    def login(self):
        """Basic Facebook login with explicit waits"""
        try:
            self.logger.info("Starting login process")
            
            # Go to Facebook login page
            self.driver.get("https://www.facebook.com")
            
            # Wait for cookie dialog and accept if present
            try:
                cookie_button = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(string(), 'Allow all cookies') or contains(string(), 'Accept all')]"))
                )
                cookie_button.click()
                time.sleep(2)
            except:
                self.logger.info("No cookie consent dialog found")
            
            # Wait for and fill email
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            email_field.clear()
            email_field.send_keys(self.email)
            time.sleep(1)
            
            # Wait for and fill password
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "pass"))
            )
            password_field.clear()
            password_field.send_keys(self.password)
            time.sleep(1)
            
            # Wait for and click login button
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "login"))
            )
            login_button.click()
            
            # Wait for navigation
            time.sleep(5)
            
            # Take screenshot for debugging
            self.driver.save_screenshot("after_login.png")
            
            # Check login status
            current_url = self.driver.current_url
            self.logger.info(f"Current URL after login: {current_url}")
            
            if "login" not in current_url.lower():
                self.logger.info("Login successful")
                return True
            else:
                self.logger.error("Login failed - still on login page")
                return False
                
        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            # Take error screenshot
            try:
                self.driver.save_screenshot("login_error.png")
            except:
                pass
            return False

    def run(self):
        """Run the crawler"""
        try:
            if self.login():
                time.sleep(random.uniform(3, 5))
                posts = self.scrape()
                
                if posts:
                    self.save_results(posts, 'facebook_data.json')
                    print(f"Saved {len(posts)} posts to facebook_data.json")
                else:
                    print("No posts found")
            else:
                print("Login failed")
        except Exception as e:
            self.logger.error(f"Error running crawler: {str(e)}")
            print("Error occurred. Check fb_crawler.log for details.")
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("Crawler closed")

    def scroll_to_load_posts(self, max_scrolls=5):
        """Scroll the page to load more posts"""
        try:
            self.logger.info("Scrolling to load more posts")
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            for i in range(max_scrolls):
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 4))  # Wait for content to load
                
                # Calculate new scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                # If no new content loaded, stop scrolling
                if new_height == last_height:
                    break
                    
                last_height = new_height
                self.logger.info(f"Completed scroll {i+1}/{max_scrolls}")
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            self.logger.error(f"Error scrolling page: {str(e)}")

    def scrape(self):
        """Main scraping function"""
        try:
            # Navigate directly to group URL
            group_url = self.GROUP_URL
            self.logger.info(f"Navigating to group: {group_url}")
            self.driver.get(group_url)
            
            # Wait for page load
            time.sleep(random.uniform(5, 7))
            
            # Extract posts
            posts = self.scrape_group(group_url)
            
            # Save posts
            if posts:
                self.save_results(posts, 'facebook_data.json')
                self.logger.info(f"Successfully saved {len(posts)} posts")
            else:
                self.logger.warning("No posts were extracted")
            
            return posts
            
        except Exception as e:
            self.logger.error(f"Error during scraping: {str(e)}")
            return []
            
        finally:
            self.cleanup()

    def scrape_group(self, group_url, max_posts=50):
        """Scrape posts from a specific Facebook group"""
        try:
            # Wait for initial load
            time.sleep(random.uniform(8, 10))
            
            # Save debug screenshot
            self.save_debug_screenshot("initial_group_load")
            
            # Check if we're on the right page
            if "login" in self.driver.current_url.lower():
                self.logger.error("Redirected to login page")
                return []
            
            # Handle any cookie/notification dialogs
            try:
                dialog_buttons = self.driver.find_elements(By.CSS_SELECTOR, "[role='button']")
                for button in dialog_buttons:
                    if any(text in button.text.lower() for text in ['accept', 'ok', 'continue', 'allow']):
                        self.driver.execute_script("arguments[0].click();", button)
                        time.sleep(random.uniform(2, 3))
            except Exception as e:
                self.logger.warning(f"Error handling dialogs: {str(e)}")
            
            # Scroll to load more posts
            self.scroll_to_load_posts()
            
            # Wait for dynamic content
            time.sleep(random.uniform(4, 6))
            
            # Extract posts
            posts = []
            
            # Try different selectors for finding posts
            post_selectors = [
                # Feed story selectors
                "div[role='article']",
                "div[data-ad-comet-preview='message']",
                "div[data-ad-preview='message']",
                
                # Content selectors
                "div.story_body_container div._5rgt",
                "div.story_body_container div._5nk5",
                "div.story_body_container div._5pbx",
                
                # Text content selectors
                "div[data-ad-preview='message'] div",
                "div[data-ad-comet-preview='message'] div",
                "div[role='article'] div[dir='auto']",
                
                # Mobile specific
                "div[data-sigil='m-feed-voice-subtitle']",
                "div._5rgt._5nk5",
                "div._5pbx.userContent",
                "div[data-sigil='story-div']"
            ]
            
            # Try each selector
            for selector in post_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    self.logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    
                    for element in elements:
                        try:
                            # Get text directly from element first
                            text = element.text.strip()
                            
                            # If no text, try to find text elements within
                            if not text:
                                text_elements = element.find_elements(By.CSS_SELECTOR, 
                                    "p, div[dir='auto'], div:not([role]):not([class*='action']):not([class*='footer']):not([class*='meta'])")
                                
                                texts = []
                                for text_elem in text_elements:
                                    try:
                                        elem_text = text_elem.text.strip()
                                        if elem_text and len(elem_text) > 10:  # Only include substantial content
                                            texts.append(elem_text)
                                    except:
                                        continue
                                
                                text = ' '.join(texts)
                            
                            if text and len(text) > 10:  # Only include substantial content
                                # Clean the text
                                text = self.clean_text(text)
                                if text:  # If text remains after cleaning
                                    # Try to get timestamp
                                    timestamp = None
                                    try:
                                        timestamp_elem = element.find_element(By.CSS_SELECTOR, 
                                            "[data-sigil='timestamp'], [data-utime], abbr[data-utime], span[title*='at']")
                                        timestamp = timestamp_elem.get_attribute('data-utime') or timestamp_elem.get_attribute('title')
                                    except:
                                        timestamp = datetime.now().isoformat()
                                    
                                    # Try to get author
                                    author = None
                                    try:
                                        author_elem = element.find_element(By.CSS_SELECTOR, 
                                            "h3 a, ._7tae a, ._52jh._5rgt a, a[data-sigil='actor']")
                                        author = author_elem.text.strip()
                                    except:
                                        pass
                                    
                                    post_data = {
                                        'text': text,
                                        'timestamp': timestamp
                                    }
                                    
                                    if author:
                                        post_data['author'] = author
                                        
                                    posts.append(post_data)
                                    self.logger.info(f"Extracted post: {text[:100]}...")
                                    
                                    if len(posts) >= max_posts:
                                        break
                                        
                        except Exception as e:
                            self.logger.warning(f"Error extracting text from element: {str(e)}")
                            continue
                            
                    if len(posts) >= max_posts:
                        break
                        
                except Exception as e:
                    self.logger.warning(f"Selector failed: {selector} - {str(e)}")
                    continue
            
            # Remove duplicates while preserving order
            seen = set()
            unique_posts = []
            for post in posts:
                if post['text'] not in seen:
                    seen.add(post['text'])
                    unique_posts.append(post)
            
            self.logger.info(f"Successfully extracted {len(unique_posts)} unique posts")
            return unique_posts
            
        except Exception as e:
            self.logger.error(f"Error extracting posts: {str(e)}")
            self.save_debug_screenshot("error_state")
            return []

    def extract_posts(self):
        """Extract posts from the loaded page"""
        try:
            self.logger.info("Extracting posts from page")
            posts = []
            
            # Wait for posts to load
            time.sleep(random.uniform(3, 5))
            
            # XPath selectors specifically for mobile Facebook
            post_selectors = [
                "//div[@data-sigil='m-story-body']",  # Main mobile story body
                "//article//div[@data-gt]",           # Article content
                "//div[contains(@class, '_5rgt')]",   # Mobile post container
                "//div[contains(@class, '_5pbx')]",   # Post text content
                "//div[@data-ft]//p",                 # Paragraphs within posts
                "//div[contains(@class, '_2pin')]//p"  # Another content location
            ]
            
            # Try each selector
            for selector in post_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    self.logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    
                    for element in elements:
                        try:
                            # Try to find the actual post text within the element
                            text_elements = element.find_elements(By.XPATH, ".//p | .//div[not(contains(@class, 'action'))]")
                            
                            texts = []
                            for text_elem in text_elements:
                                try:
                                    text = text_elem.text.strip()
                                    if text:
                                        texts.append(text)
                                except:
                                    continue
                            
                            text = ' '.join(texts)
                            
                            if text and len(text) > 10:  # Only include substantial content
                                # Clean the text
                                text = self.clean_text(text)
                                if text:  # If text remains after cleaning
                                    posts.append({
                                        'text': text,
                                        'timestamp': datetime.now().isoformat()
                                    })
                                    self.logger.info(f"Extracted post: {text[:100]}...")
                        except Exception as e:
                            self.logger.warning(f"Error extracting text from element: {str(e)}")
                            continue
                except Exception as e:
                    self.logger.warning(f"Selector failed: {selector} - {str(e)}")
                    continue
            
            # Remove duplicates while preserving order
            seen = set()
            unique_posts = []
            for post in posts:
                if post['text'] not in seen:
                    seen.add(post['text'])
                    unique_posts.append(post)
            
            self.logger.info(f"Successfully extracted {len(unique_posts)} unique posts")
            return unique_posts
            
        except Exception as e:
            self.logger.error(f"Error extracting posts: {str(e)}")
            return []

    def clean_text(self, text):
        """Clean extracted text"""
        try:
            # Remove UI elements and common clutter
            patterns = [
                r'Like$', r'Comment$', r'Share$',
                r'View \d+ more comments?',
                r'View previous comments?',
                r'See Translation',
                r'See More$',
                r'See Less$',
                r'Reply$',
                r'\d+ Replies?$',
                r'\d+ Comments?$',
                r'\d+ Shares?$',
                r'\d+[KM]? Views?$',
                r'Edited$',
                r'Top Fan$',
                r'Top Contributor$',
                r'Author$',
                r'Admin$',
                r'Moderator$',
                r'Follow$',
                r'Join Group$',
                r'Join$',
                r'Public Group$',
                r'Public$',
                r'Group$',
                r'Privacy$',
                r'Visible$',
                r'Members?$',
                r'About$',
                r'Description$',
                r'Rules$',
                r'Photos?$',
                r'Videos?$',
                r'Files?$',
                r'Events?$',
                r'More$',
                r'Menu$',
                r'Search$',
                r'Write something...$',
                r'What\'s on your mind\?$',
                r'Add a comment...$',
                r'Press Enter to post.$',
                r'Add Photo/Video$',
                r'Live Video$',
                r'Check in$',
                r'Feeling/Activity$',
                r'Tag Friends$',
                r'GIF$',
                r'Sticker$',
                r'Background Color$',
                r'Support Inbox$',
                r'Settings$',
                r'Help$',
                r'Report$',
                r'Block$',
                r'Hide$',
                r'Unfollow$',
                r'Save$',
                r'Copy link$',
                r'Turn on notifications$',
                r'Turn off notifications$',
                r'Customize notifications$',
                r'Leave group$',
                r'Invite$',
                r'Share group$',
                r'Pin post$',
                r'Edit post$',
                r'Delete post$',
                r'Move to trash$',
                r'Archive post$',
                r'Turn off commenting$',
                r'Edit privacy$',
                r'Edit audience$',
                r'Edit history$',
                r'Edit date$',
                r'Edit location$',
                r'Edit feeling/activity$',
                r'Edit tags$',
                r'Edit post$'
            ]
            
            # Compile patterns
            pattern = '|'.join(patterns)
            
            # Clean text
            lines = text.split('\n')
            cleaned_lines = []
            
            for line in lines:
                line = line.strip()
                if line and not re.search(pattern, line):
                    cleaned_lines.append(line)
            
            cleaned_text = ' '.join(cleaned_lines)
            
            # Remove extra whitespace
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
            
            return cleaned_text if len(cleaned_text) > 10 else None
            
        except Exception as e:
            self.logger.error(f"Error cleaning text: {str(e)}")
            return None

    def save_results(self, data, filename):
        """Save scraped data to JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            self.logger.info(f"Results saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving results: {str(e)}")

    def save_debug_screenshot(self, step_name):
        """Take a screenshot for debugging purposes"""
        try:
            filename = f"debug_{step_name}_{int(time.time())}.png"
            self.driver.save_screenshot(filename)
            self.logger.info(f"Debug screenshot saved: {filename}")
            # Also save page source
            with open(f"debug_{step_name}_{int(time.time())}.html", 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
        except Exception as e:
            self.logger.error(f"Failed to take debug screenshot: {str(e)}")

    def cleanup(self):
        """Cleanup after scraping"""
        try:
            self.driver.quit()
            self.logger.info("Crawler closed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")

def main():
    # Configuration
    EMAIL = "silver.vapper@eki.ee"
    PASSWORD = "V6M#NpWsUH"
    GROUP_ID = "154506787728088"  # Group ID
    
    # Initialize crawler
    crawler = StealthFacebookCrawler(EMAIL, PASSWORD, GROUP_ID)
    
    crawler.run()

if __name__ == "__main__":
    main()