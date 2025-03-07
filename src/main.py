import sys
import os
import random
import json
import re
import argparse

# Add the src directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from browser import HandshakeBrowser
from utils import setup_logging, load_config, random_wait
from constants import APPLICATIONS_LOG_PATH  # Import the specific constant

def extract_job_id(url):
    """Extract the job ID from a Handshake job URL"""
    match = re.search(r'/jobs/(\d+)', url)
    if match:
        return match.group(1)
    return None

def load_applied_jobs():
    """Load previously applied job IDs from applications_log.json"""
    applied_job_ids = set()
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", APPLICATIONS_LOG_PATH)
    
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r') as f:
                log_data = json.load(f)
                for entry in log_data:
                    if 'url' in entry:
                        job_id = extract_job_id(entry['url'])
                        if job_id:
                            applied_job_ids.add(job_id)
        except json.JSONDecodeError:
            # Handle empty or invalid JSON file
            pass
    
    return applied_job_ids

def process_job_results(browser, max_pages=3):
    """Process job results for the current page and subsequent pages"""
    # Set up logging
    logger = setup_logging()
    config = load_config()
    verbose_logging = config.get('settings', {}).get('verbose_logging', True)
    
    # Load previously applied jobs
    applied_job_ids = load_applied_jobs()
    logger.info(f"Loaded {len(applied_job_ids)} previously applied jobs")
    
    total_jobs_processed = 0
    page_number = 1
    
    while page_number <= max_pages:
        if verbose_logging:
            logger.info(f"Processing page {page_number}")
        page_url = browser.driver.current_url
        
        # Get all job URLs from the current page
        job_urls = browser.get_job_urls()
        
        if not job_urls:
            logger.error("No job URLs found. Stopping.")
            break
            
        logger.info(f"Found {len(job_urls)} job URLs on page {page_number}")
        
        # Process each job URL
        for job_url in job_urls:
            total_jobs_processed += 1
            
            # Extract job ID and skip if already applied
            job_id = extract_job_id(job_url)
            if job_id and job_id in applied_job_ids:
                if verbose_logging:
                    logger.info(f"Already processed job ID: {job_id}. Skipping.")
                else:
                    logger.info(f"Job #{total_jobs_processed}: ⏭️  already processed")
                continue
            
            # Navigate to the job URL
            browser.driver.get(job_url)
            random_wait(1, 2)
            
            # Apply to the job
            application_successful, status = browser.apply_to_job()
            
            if not verbose_logging:
                logger.info(f"Job #{total_jobs_processed}: {status}")
            
            if application_successful and job_id:
                applied_job_ids.add(job_id)
            
            # Wait before processing the next job URL
            random_wait(2, 3)
        
        # Try to navigate to the next page
        if browser.navigate_to_next_page(page_url):
            page_number += 1
        else:
            if verbose_logging:
                logger.info("No more pages available")
            break
    
    return total_jobs_processed

def run_bot(use_existing_driver=False, debug_port=9222):
    # Set up logging
    logger = setup_logging()
    logger.info("Starting Handshake Job Bot")
    
    try:
        # Initialize browser with existing driver if specified
        if use_existing_driver:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.common.exceptions import WebDriverException
            
            try:
                options = Options()
                options.debugger_address = f"127.0.0.1:{debug_port}"
                driver = webdriver.Chrome(options=options)
                browser = HandshakeBrowser(existing_driver=driver)
                logger.info(f"Connected to existing Chrome session on port {debug_port}")
            except WebDriverException as e:
                logger.error(f"Failed to connect to Chrome on port {debug_port}")
                print(f"\nERROR: Could not connect to Chrome on port {debug_port}.")
                print("Please make sure Chrome is running with remote debugging enabled.")
                print("\nTo start Chrome correctly:")
                print("1. Close all Chrome windows")
                print(f"2. Run: chrome.exe --remote-debugging-port={debug_port} --incognito")
                print("3. Log into Handshake and set your filters")
                print(f"4. Run this script again with --use-existing --port={debug_port}\n")
                return
        else:
            browser = HandshakeBrowser()
            
        config = load_config()
        verbose_logging = config.get('settings', {}).get('verbose_logging', True)
        logger.info(f"Verbose logging: {verbose_logging}")
        
        # Login and navigate to jobs only if not using existing driver
        if not use_existing_driver:
            # Login to Handshake
            login_successful = browser.login()
            
            if not login_successful:
                logger.error("Login failed. Exiting...")
                browser.close()
                return
                
            logger.info("Login successful")
            
            # Step 2: Navigate to the jobs page
            jobs_navigation_successful = browser.navigate_to_jobs()
            
            if not jobs_navigation_successful:
                logger.error("Failed to navigate to jobs page. Exiting...")
                browser.close()
                return
        
        # Step 3: Apply to jobs
        job_titles = config['job_search']['titles']
        
        if use_existing_driver:
            # For existing driver, just process the current page
            process_job_results(browser)
        else:
            # For normal flow, search for each job title
            for job_title in job_titles:
                logger.info(f"Searching for job title: {job_title}")
                
                # Search for the job title
                search_successful = browser.search_job(job_title)
                
                if not search_successful:
                    logger.error(f"Failed to search for job title: {job_title}. Skipping to next job title.")
                    continue
                
                # Process job results
                process_job_results(browser)
                
                # Wait before processing the next job title
                random_wait(3, 5)
        
        # Close the browser when done (only if we created it)
        if not use_existing_driver:
            browser.close()
            logger.info("Browser closed. Bot finished.")
        else:
            logger.info("Bot finished. Browser left open.")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")

# Main execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Handshake Job Bot')
    parser.add_argument('--use-existing', action='store_true', help='Use existing Chrome session')
    parser.add_argument('--port', type=int, default=9222, help='Remote debugging port for Chrome')
    
    args = parser.parse_args()
    
    if args.use_existing:
        # Instructions for connecting to existing Chrome
        print(f"Please start Chrome with: chrome.exe --remote-debugging-port={args.port} --incognito")
        print("Log into Handshake and set your filters")
        input("Press Enter when ready...")
        
        run_bot(use_existing_driver=True, debug_port=args.port)
    else:
        # Original flow
        run_bot(use_existing_driver=False)