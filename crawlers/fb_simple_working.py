from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import undetected_chromedriver as uc
import time
import logging
import json
from datetime import datetime

class FacebookGroupCrawler:
    def __init__(self, group_url, email, password):
        self.group_url = group_url
        self.email = email
        self.password = password
        self.driver = None
        self.logger = self._setup_logger()
        self.driver = self._setup_driver()
        self.posts_data = []

    def _setup_logger(self):
        """Set up and return logger"""
        logger = logging.getLogger('fb_crawler')
        logger.setLevel(logging.INFO)
        fh = logging.FileHandler('fb_crawler.log')
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        return logger

    def _setup_driver(self):
        """Set up and return the Chrome WebDriver"""
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-notifications')
        
        # Use Chrome instead of Chromium
        options.binary_location = "/usr/bin/google-chrome"
        
        return uc.Chrome(options=options, browser_executable_path="/usr/bin/google-chrome")

    def handle_cookie_consent(self):
        """Handle cookie consent dialog"""
        try:
            time.sleep(3)  # Wait for dialog to appear
            
            # Try to find and click "Decline optional cookies" button
            decline_xpath = "//span[text()='Decline optional cookies']/ancestor::button"
            decline_buttons = self.driver.find_elements(By.XPATH, decline_xpath)
            
            if decline_buttons:
                decline_buttons[0].click()
                time.sleep(2)
                self.logger.info("Clicked decline optional cookies button")
                return True
                
            # If not found, try alternative text
            alt_decline_xpath = "//span[contains(text(), 'Decline')]/ancestor::button"
            alt_decline_buttons = self.driver.find_elements(By.XPATH, alt_decline_xpath)
            
            if alt_decline_buttons:
                alt_decline_buttons[0].click()
                time.sleep(2)
                self.logger.info("Clicked alternative decline button")
                return True
            
            self.logger.info("No cookie consent buttons found")
            return False
            
        except Exception as e:
            self.logger.error(f"Error handling cookie consent: {str(e)}")
            return False

    def login(self, email, password):
        """Log into Facebook"""
        try:
            self.logger.info("Attempting to log in")
            
            # Go to login page
            self.driver.get("https://www.facebook.com/login")
            time.sleep(3)
            
            # Handle cookie consent first if it appears
            self.handle_cookie_consent()
            time.sleep(2)
            
            # Wait for email field and enter email
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            email_field.clear()
            email_field.send_keys(email)
            
            # Find password field and enter password
            password_field = self.driver.find_element(By.ID, "pass")
            password_field.clear()
            password_field.send_keys(password)
            
            # Wait for login button to be clickable
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "login"))
            )
            
            # Try to click using JavaScript if normal click fails
            try:
                login_button.click()
            except:
                self.driver.execute_script("arguments[0].click();", login_button)
            
            # Wait for redirect
            time.sleep(5)
            
            # Check if login was successful
            if "login" not in self.driver.current_url.lower():
                self.logger.info("Login successful")
                return True
            else:
                self.logger.error("Login failed - still on login page")
                return False
                
        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            return False

    def extract_post_data(self, post):
        """Extract author, content, and timestamp from a post"""
        try:
            # Extract author name - look for specific author container
            author = "Unknown"
            try:
                # Try multiple author selectors
                author_selectors = [
                    "a[role='link'] > strong",
                    "h3 span[dir='auto']",
                    "h4 span[dir='auto']",
                    "span.x3nfvp2",
                    "h3, h4"  # Fallback to any header
                ]
                
                for selector in author_selectors:
                    try:
                        author_elem = post.find_element(By.CSS_SELECTOR, selector)
                        author = author_elem.text.strip()
                        if author:
                            break
                    except:
                        continue
                        
            except:
                # Last resort: try to get first line of post
                try:
                    first_line = post.text.split('\n')[0]
                    if first_line and len(first_line) < 50:  # Assume author names aren't too long
                        author = first_line
                except:
                    pass
            
            # Extract post content - try multiple selectors
            content = ""
            content_selectors = [
                "div[data-ad-comet-preview='message']",
                "div[data-ad-preview='message']",
                "div.x1iorvi4",
                "div.xdj266r",
                "div[dir='auto']",
                "div.story_body_container"
            ]
            
            for selector in content_selectors:
                try:
                    content_divs = post.find_elements(By.CSS_SELECTOR, selector)
                    for div in content_divs:
                        text = div.text.strip()
                        if text:
                            content = text
                            break
                    if content:
                        break
                except:
                    continue
            
            # If no content found through selectors, get all text
            if not content:
                content = post.text.strip()
            
            # Extract timestamp
            timestamp = ""
            try:
                # Try multiple timestamp selectors
                time_selectors = [
                    "a[role='link'][href*='/posts/'] span",
                    "span.x4k7w5x a[role='link']",
                    "a[role='link'] span.x1i10hfl",
                    "abbr",  # Facebook often uses abbr for timestamps
                    "span[title]"  # Sometimes timestamps are in title attributes
                ]
                
                for selector in time_selectors:
                    try:
                        time_elem = post.find_element(By.CSS_SELECTOR, selector)
                        text = time_elem.text.strip()
                        if text and any(unit in text.lower() for unit in ['h', 'm', 's', 'min', 'hr', 'sec', 'day', 'week']):
                            timestamp = text
                            break
                    except:
                        continue
            except:
                pass
            
            # Clean up the content
            if content:
                # Remove common UI text
                ui_elements = [
                    "Like",
                    "Reply",
                    "Share",
                    "Comment",
                    "Full Story",
                    "See More",
                    "See Less"
                ]
                for ui_text in ui_elements:
                    content = content.replace(ui_text, "")
                
                # Clean up whitespace
                content = "\n".join(line.strip() for line in content.split('\n') if line.strip())
            
            # Create post data if we have any content
            if content:
                post_data = {
                    "author": author,
                    "content": content,
                    "timestamp": timestamp,
                    "crawl_time": datetime.now().isoformat()
                }
                self.logger.info(f"Extracted post from {author}")
                return post_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting post data: {str(e)}")
            return None

    def save_to_json(self):
        """Save extracted posts to JSON file"""
        try:
            # Load existing data if file exists
            try:
                with open('facebook_data.json', 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = []
            
            # Append new posts
            existing_data.extend(self.posts_data)
            
            # Save updated data
            with open('facebook_data.json', 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Saved {len(self.posts_data)} posts to facebook_data.json")
            
        except Exception as e:
            self.logger.error(f"Error saving to JSON: {str(e)}")

    def visit_group(self):
        """Visit the Facebook group page"""
        try:
            # First try to log in
            if not self.login(self.email, self.password):
                self.logger.error("Failed to log in")
                return False
                
            self.logger.info(f"Visiting group: {self.group_url}")
            self.driver.get(self.group_url)
            time.sleep(5)  # Wait for page load
            
            # Handle cookie consent
            self.handle_cookie_consent()
            time.sleep(3)  # Wait after handling cookies
            
            # Log the current URL and page title
            self.logger.info(f"Current URL: {self.driver.current_url}")
            self.logger.info(f"Page title: {self.driver.title}")
            
            # Try to find group content
            try:
                # Wait for feed to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[role="feed"]'))
                )
                
                posts = self.driver.find_elements(By.CSS_SELECTOR, '[role="article"]')
                self.logger.info(f"Found {len(posts)} potential post elements")
                
                # Extract data from each post
                for post in posts:
                    post_data = self.extract_post_data(post)
                    if post_data:  # Only add if we have content
                        self.posts_data.append(post_data)
                
                # Save extracted data
                self.save_to_json()
                
            except TimeoutException:
                self.logger.error("Timed out waiting for feed to load")
            except Exception as e:
                self.logger.error(f"Failed to extract posts: {str(e)}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to visit group: {str(e)}")
            return False

def main():
    # Facebook group URL
    GROUP_URL = "https://www.facebook.com/groups/ilmahuvilised"
    # Email and password
    EMAIL = "silver.vapper@eki.ee"
    PASSWORD = "V6M#NpWsUH"
    
    # Create crawler instance
    crawler = FacebookGroupCrawler(GROUP_URL, EMAIL, PASSWORD)
    
    try:
        # Visit the group
        success = crawler.visit_group()
        print("Successfully visited group page" if success else "Failed to visit group page")
    finally:
        if crawler.driver:
            crawler.driver.quit()

if __name__ == "__main__":
    main()
