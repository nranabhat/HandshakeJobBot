import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
import pickle
from datetime import datetime
import json 

from utils import load_config, random_wait, log_application
from constants import *

logger = logging.getLogger('handshake_job_bot')

class HandshakeBrowser:
    def __init__(self, existing_driver=None):
        self.config = load_config()
        self.driver = existing_driver if existing_driver else self._setup_driver()
        self.verbose_logging = self.config.get('settings', {}).get('verbose_logging', True)
        
        # If using existing driver, check if already logged in
        if existing_driver:
            logger.info("Using existing Chrome session")
            # Check if we're already on Handshake
            if "handshake.com" not in self.driver.current_url:
                logger.warning("Existing session not on Handshake. User should navigate to Handshake first.")
                logger.warning("Current URL: " + self.driver.current_url)
        
    def _setup_driver(self):
        """Set up and configure Chrome WebDriver."""
        chrome_options = Options()
        # Uncomment these lines if you want to run headless
        # chrome_options.add_argument("--headless")
        # chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--no-sandbox")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    
    def login(self):
        """Login to Handshake using UW NetID."""
        logger.info("Logging into Handshake...")
        
        try:
            # Navigate to login page
            self.driver.get(self.config['handshake']['login_url'])
            random_wait()
            
            # Click "Sign in with NetID" button
            netid_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, XPATH_NETID_LOGIN))
            )
            netid_button.click()
            
            # Random wait for NetID login page
            random_wait()
            
            # Enter NetID credentials
            netid_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, ID_USERNAME))
            )
            netid_input.send_keys(os.environ.get('HANDSHAKE_NETID'))
            
            password_input = self.driver.find_element(By.ID, ID_PASSWORD)
            password_input.send_keys(os.environ.get('HANDSHAKE_PASSWORD'))
            
            # Random wait between actions
            random_wait()
            
            # Click login button
            login_button = self.driver.find_element(By.NAME, NAME_LOGIN_BUTTON)
            login_button.click()
            
            # Wait for redirection to Handshake
            random_wait(3, 5)  # Give some time for redirection
            
            # Check for and close modal that might appear after login
            try:
                close_modal = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, BUTTON_CLOSE_MODAL_CSS))
                )
                close_modal.click()
            except Exception as e:
                logger.info("No post-login modal detected or error closing modal")
            
        except Exception as e:
            logger.error(f"Failed to login: {str(e)}")
            return False

        return True
    
    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()
            
    def navigate_to_jobs(self):
        """Navigate to the jobs page by directly accessing the URL."""
        try:
            # Navigate to filtered search for full-time jobs
            target_url = self.config['handshake']['filtered_search_url']
            logger.info(f"Navigating to {target_url}")
            self.driver.get(target_url)
            
            # Wait to see if we can access the page
            random_wait(1, 2)
            
            # Wait for the jobs page to load
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, BUTTON_FILTER_CSS))
            )
            
            # Log the current URL
            current_url = self.driver.current_url
            
            if "postings" in current_url.lower():
                logger.info("Successfully navigated to job postings page")
                return True
            else:
                logger.warning(f"Navigation may have failed, current URL: {current_url}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to navigate to jobs page: {str(e)}")
            return False
    
    def search_job(self, job_title):
        """Search for a job title in the search bar."""
        if self.verbose_logging:
            logger.info(f"Searching for job: {job_title}")
        try:
            # Find the search input field
            search_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, INPUT_JOBS_SEARCH_CSS))
            )
            
            # Clear any existing text using a more robust approach
            search_input.clear()
            # Select all text (Ctrl+A) and delete it
            search_input.send_keys(Keys.CONTROL + "a")
            search_input.send_keys(Keys.DELETE)
            random_wait(1, 2)
            
            # Type the job title character by character with random delays
            for char in job_title:
                search_input.send_keys(char)
                random_wait(0.05, 0.15)
            
            # Press Enter to submit the search
            search_input.send_keys(Keys.ENTER)
            if self.verbose_logging:
                logger.info("Pressed Enter to submit the search")
            
            # Wait for search results to load
            random_wait(2, 3)
            
            if self.verbose_logging:
                logger.info(f"Successfully searched for job: {job_title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to search for job: {str(e)}")
            return False
    
    def get_job_urls(self):
        """Get URLs of all job cards in the search results."""
        if self.verbose_logging:
            logger.info("Retrieving URLs for all job cards on the current page")
        try:
            # Wait for job cards to be present
            random_wait(2, 3)
            
            # Find all job cards - using constants
            job_cards_container = self.driver.find_element(By.CSS_SELECTOR, DIV_JOB_CARDS_CONTAINER_CSS)
            job_links = job_cards_container.find_elements(By.CSS_SELECTOR, JOB_CARD_LINK_CSS)
            
            if not job_links:
                logger.warning("No job cards found")
                return []
            
            # Extract URLs from all job cards
            job_urls = []
            for link in job_links:
                url = link.get_attribute('href')
                if url:
                    job_urls.append(url)
            
            if self.verbose_logging:
                logger.info(f"Successfully retrieved {len(job_urls)} job URLs")
            return job_urls
            
        except Exception as e:
            logger.error(f"Failed to retrieve job URLs: {str(e)}")
            return []
    
    def apply_to_job(self):
        """Apply to the job."""
        try:
            # Check for "Apply Externally" button
            try:
                external_button = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, XPATH_APPLY_EXTERNALLY_BUTTON))
                )
                if self.verbose_logging:
                    logger.info("External application required - skipping 🔗")
                log_application(self.driver, self.verbose_logging, status="external application")
                return False, "🔗 external application"
            except:
                pass
                
            # Check if there's no Apply button which indicates we've already applied
            try:
                # Try to find the Apply button with a short timeout
                apply_button = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, XPATH_APPLY_BUTTON))
                )
            except:
                # If no Apply button is found, we've likely already applied
                log_application(self.driver, self.verbose_logging, status="already applied")
                if self.verbose_logging:
                    logger.info("No Apply button found - already applied to this job - skipping")
                return True, "🏎️  already applied"
            
            # If we get here, the Apply button exists
            
            random_wait(0,1)
            
            apply_button.click()
            if self.verbose_logging:
                logger.info("Clicked Apply button")
            
            random_wait(1, 2)
            
            # Fill out the application form
            self._fill_application_form()
            
            # Submit the application
            submit_button = WebDriverWait(self.driver, 4).until(
                EC.element_to_be_clickable((By.XPATH, XPATH_SUBMIT_APPLICATION_BUTTON))
            )
            
            # Random wait before clicking
            random_wait()
            
            submit_button.click()
            if self.verbose_logging:
                logger.info("Clicked Submit Application button")
            
            random_wait(1, 2)

            try:
                # Check if the apply modal is no longer present, which indicates success
                try:
                    WebDriverWait(self.driver, 5).until_not(
                        EC.presence_of_element_located((By.CSS_SELECTOR, APPLY_MODAL_CONTENT_CSS))
                    )
                    if self.verbose_logging:
                        logger.info("Application successful - apply modal closed")
                    log_application(self.driver, self.verbose_logging, status="applied")
                    return True, "✅ applied"
                except:
                    if self.verbose_logging:
                        logger.info("Apply modal still present - application may not have completed")
                    log_application(self.driver, self.verbose_logging, status="unanswered application questions")
                    return False, "❌ unanswered questions"
            except:
                if self.verbose_logging:
                    logger.info("No withdraw application button found.")
                # Fallback: just log the URL
                log_application(self.driver, self.verbose_logging, fallback=True, status="applied")
                return True, "✅ applied"
            
        except Exception as e:
            logger.error(f"Failed to apply to job")
            return False, "❌ error"
    
    def _fill_application_form(self):
        """Fill out the application form."""
        if self.verbose_logging:
            logger.info("Filling out application form")
        try:
            # Upload resume if needed
            try:
                resume_button = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, XPATH_RESUME_BUTTON))
                )
                resume_button.click()
                if self.verbose_logging:
                    logger.info("Selected resume")
            except:
                if self.verbose_logging:
                    logger.info("No resume selection needed or already selected")
            
            # Upload cover letter if needed
            try:
                coverletter_button = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, XPATH_COVERLETTER_BUTTON))
                )
                coverletter_button.click()
                if self.verbose_logging:
                    logger.info("Selected cover letter")
            except:
                if self.verbose_logging:
                    logger.info("No cover letter selection needed or already selected")
            
            # Upload transcript if needed
            try:
                transcript_button = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, XPATH_TRANSCRIPT_BUTTON))
                )
                transcript_button.click()
                if self.verbose_logging:
                    logger.info("Selected transcript")
            except:
                if self.verbose_logging:
                    logger.info("No transcript selection needed or already selected")
            
            # Find and fill required fields
            required_fields = self.driver.find_elements(By.CSS_SELECTOR, DIV_REQUIRED_FIELD_CSS)
            
            for field in required_fields:
                # Check for dropdowns
                dropdowns = field.find_elements(By.CSS_SELECTOR, SELECT_DROPDOWN_CSS)
                if dropdowns:
                    for dropdown in dropdowns:
                        # Select the second option (index 1) to avoid the default "Select an option"
                        options = dropdown.find_elements(By.TAG_NAME, TAG_OPTION)
                        if len(options) > 1:
                            options[1].click()
                            if self.verbose_logging:
                                logger.info("Selected dropdown option")
                
                # Check for text inputs
                text_inputs = field.find_elements(By.CSS_SELECTOR, INPUT_TEXT_CSS)
                if text_inputs:
                    for text_input in text_inputs:
                        if text_input.get_attribute("value") == "":
                            text_input.send_keys("Yes")
                            if self.verbose_logging:
                                logger.info("Filled text input")
                
                # Check for radio buttons
                radio_buttons = field.find_elements(By.CSS_SELECTOR, INPUT_RADIO_CSS)
                if radio_buttons:
                    # Click the first radio button
                    radio_buttons[0].click()
                    if self.verbose_logging:
                        logger.info("Selected radio button")
                
                # Check for checkboxes
                checkboxes = field.find_elements(By.CSS_SELECTOR, INPUT_CHECKBOX_CSS)
                if checkboxes:
                    # Click the checkbox
                    checkboxes[0].click()
                    if self.verbose_logging:
                        logger.info("Selected checkbox")
            
            if self.verbose_logging:
                logger.info("Completed filling out application form")
            return True
            
        except Exception as e:
            logger.error(f"Failed to fill application form: {str(e)}")
            return False

    def navigate_to_next_page(self, current_url):
        """Navigate to the next page of job results."""
        if self.verbose_logging:
            logger.info("Navigating to the next page of job results")
        try:
            # Check if there's a page parameter
            if "page=" in current_url:
                # Extract current page number
                current_page = int(current_url.split("page=")[1].split("&")[0])
                # Create URL for next page
                next_page = current_page + 1
                next_url = current_url.replace(f"page={current_page}", f"page={next_page}")
            else:
                # If no page parameter exists, add it
                if "?" in current_url:
                    next_url = current_url + "&page=2"
                else:
                    next_url = current_url + "?page=2"
            
            # Navigate to next page
            logger.info(f"Navigating to next page: {next_url}")
            self.driver.get(next_url)
            
            # Wait for page to load
            random_wait(2, 3)
            
            # Check if there are job cards on this page
            try:
                job_cards_container = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, DIV_JOB_CARDS_CONTAINER_CSS))
                )
                job_links = job_cards_container.find_elements(By.CSS_SELECTOR, JOB_CARD_LINK_CSS)
                
                if job_links:
                    logger.info(f"Successfully navigated to next page with {len(job_links)} job cards")
                    return True
                else:
                    logger.info("No job cards found on next page")
                    return False
            except:
                logger.info("No job cards found on next page")
                return False
            
        except Exception as e:
            logger.error(f"Failed to navigate to next page: {str(e)}")
            return False
