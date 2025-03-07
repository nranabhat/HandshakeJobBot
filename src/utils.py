import json
import logging
import os
import random
import time
from datetime import datetime
from selenium.webdriver.common.by import By

from dotenv import load_dotenv
from constants import *  # Make sure to import constants

# Load environment variables
load_dotenv()

def load_config():
    """Load configuration from config file."""
    with open('config/config.json', 'r') as f:
        return json.load(f)

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('handshake_job_bot')

def random_wait(min_seconds=None, max_seconds=None):
    """Wait for a random amount of time between min and max seconds."""
    config = load_config()
    min_wait = min_seconds if min_seconds is not None else config['settings']['min_wait_time']
    max_wait = max_seconds if max_seconds is not None else config['settings']['max_wait_time']
    
    wait_time = random.uniform(min_wait, max_wait)
    time.sleep(wait_time)
    return wait_time

def log_application(driver, verbose_logging=False, fallback=False, status="applied"):
    """Save details of job application to a file."""
    logger = logging.getLogger('handshake_job_bot')
    try:
        # Create directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        if not fallback:
            try:
                # Try multiple possible selectors for job title
                job_title = None
                for selector in JOB_TITLE_SELECTORS:
                    try:
                        job_title = driver.find_element(By.CSS_SELECTOR, selector).text
                        if job_title:
                            break
                    except:
                        continue
                
                # Try multiple possible selectors for employer name
                employer = None
                for selector in EMPLOYER_NAME_SELECTORS:
                    try:
                        employer = driver.find_element(By.CSS_SELECTOR, selector).text
                        if employer:
                            break
                    except:
                        continue
                
                # Get all div.sc-bESXSR.jmWGwS elements
                # Use a more robust approach that doesn't rely on specific class names
                location = None
                employment_type = None
                
                # Look for divs that contain SVGs with specific path patterns
                # This approach will work regardless of the class names
                all_divs = driver.find_elements(By.CSS_SELECTOR, "div")
                
                for div in all_divs:
                    try:
                        # Check if this div contains an SVG
                        svg_elements = div.find_elements(By.TAG_NAME, "svg")
                        if not svg_elements:
                            continue
                            
                        svg = svg_elements[0]
                        path_elements = svg.find_elements(By.TAG_NAME, "path")
                        if not path_elements:
                            continue
                            
                        path_d = path_elements[0].get_attribute("d")
                        
                        # Location SVG path starts with "M12 21.75"
                        if path_d and path_d.startswith("M12 21.75"):
                            # Find the text within this div structure
                            # Look for any div that might contain the location text
                            inner_divs = div.find_elements(By.TAG_NAME, "div")
                            for inner_div in inner_divs:
                                if "onsite" in inner_div.text.lower() or "remote" in inner_div.text.lower() or "hybrid" in inner_div.text.lower() or "united states" in inner_div.text.lower():
                                    location = inner_div.text
                                    if verbose_logging:
                                        logger.info(f"Found location: {location}")
                                    break
                        
                        # Job type SVG path starts with "M8.50029 16.75"
                        elif path_d and path_d.startswith("M8.50029 16.75"):
                            # Find the text within this div structure
                            inner_divs = div.find_elements(By.TAG_NAME, "div")
                            for inner_div in inner_divs:
                                if "full-time" in inner_div.text.lower() or "part-time" in inner_div.text.lower() or "internship" in inner_div.text.lower():
                                    employment_type = inner_div.text
                                    if verbose_logging:
                                        logger.info(f"Found employment type: {employment_type}")
                                    break
                    except Exception as e:
                        if verbose_logging:
                            logger.info(f"Error processing div: {str(e)}")
                        continue
                
                # Format the data
                application_data = {
                    "timestamp": timestamp,
                    "url": driver.current_url,
                    "status": status
                }
                
                if job_title:
                    application_data["job_title"] = job_title
                if employer:
                    application_data["employer"] = employer
                if location:
                    application_data["location"] = location
                if employment_type:
                    application_data["employment_type"] = employment_type
                    
            except Exception as e:
                logger.warning(f"Could not extract job details: {str(e)}")
                application_data = {
                    "timestamp": timestamp,
                    "url": driver.current_url,
                    "status": status
                }
        else:
            # Just save the URL if we can't get other details
            application_data = {
                "timestamp": timestamp,
                "url": driver.current_url,
                "status": status
            }
        
        # Save to a single file, appending new applications
        filename = APPLICATIONS_LOG_PATH
        
        # Load existing data if file exists
        existing_data = []
        if os.path.exists(filename):
            try:
                with open(filename, "r") as f:
                    existing_data = json.load(f)
            except:
                existing_data = []
        
        # Append new application data
        existing_data.append(application_data)
        
        # Write back to file
        with open(filename, "w") as f:
            json.dump(existing_data, f, indent=4)
        
        if verbose_logging:
            logger.info(f"Added application details to {filename}")
        
    except Exception as e:
        logger.error(f"Failed to save application details: {str(e)}")