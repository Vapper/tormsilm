import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import logging

class FacebookGroupCrawler:
    def __init__(self, group_url, email, password):
        self.group_url = group_url
        self.email = email
        self.password = password
        self.driver = None
        self.logger = self._setup_logger()
        self.driver = self._setup_driver()

    def _setup_logger(self):
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
            
            # Take screenshot for debugging
            self.driver.save_screenshot("group_page.png")
            
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
                
                for i, post in enumerate(posts[:5]):  # Log first 5 posts
                    self.logger.info(f"Post {i+1} text: {post.text[:200]}")  # First 200 chars
            except TimeoutException:
                self.logger.error("Timed out waiting for feed to load")
            except Exception as e:
                self.logger.error(f"Failed to extract posts: {str(e)}")
            
            # Save page source for analysis
            with open("group_page.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to visit group: {str(e)}")
            return False
        
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

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
        if crawler.visit_group():
            print("Successfully visited group page")
        else:
            print("Failed to visit group page")
    finally:
        crawler.close()

if __name__ == "__main__":
    main()
