"""
Constants for the Handshake Job Bot.
Contains all selectors used for interacting with the Handshake website.
"""

# CSS Selectors
# Login related
BUTTON_CLOSE_MODAL_CSS = "button[aria-label='Close modal'][data-hook='close-bootstrapping-follows-modal']"

# Navigation
BUTTON_FILTER_CSS = "button[data-hook='button'][aria-label='Filter by']"
INPUT_JOBS_SEARCH_CSS = "input[aria-label='Jobs or employers']"

# Job cards
DIV_JOB_CARDS_CONTAINER_CSS = "div.style__cards___hgLkO"
JOB_CARD_LINK_CSS = "a.style__card___LCqKH"

# Application log selectors
APPLICATIONS_LOG_PATH = "logs/applications_log.json"

# Job title selectors
JOB_TITLE_SELECTORS = [
    "h1.style__job-title__3jVD1", 
    "h1[data-testid='job-title']", 
    "h1.job-title", 
    "h1"
]

# Employer name selectors
EMPLOYER_NAME_SELECTORS = [
    "span.style__employer-name__VeAXU", 
    "span[data-testid='employer-name']", 
    "a.employer-name", 
    "div.employer-info span",
    "div.sc-carhra a div.sc-cIUgcF",
    "a[href*='/stu/employers/'] div"
]

# Application
# DIV_APPLICATION_FORM_CSS = "div.style__application-form__1Mz_K"
# DIV_SUCCESS_CARD_CSS = "div.style__success-card__1aTrY"
DIV_REQUIRED_FIELD_CSS = "div.style__required__1Xkbq"
SELECT_DROPDOWN_CSS = "select"
INPUT_TEXT_CSS = "input[type='text']"
INPUT_RADIO_CSS = "input[type='radio']"
INPUT_CHECKBOX_CSS = "input[type='checkbox']"
# BUTTON_DISMISS_CSS = "button.style__dismiss___Zotdc"

# ID Selectors
# ID_SCHOOL_LOGIN_SELECT = "s2id_school-login-select"
ID_USERNAME = "j_username"
ID_PASSWORD = "j_password"

# Name Selectors
NAME_LOGIN_BUTTON = "_eventId_proceed"

# XPath Selectors
XPATH_NETID_LOGIN = "//a[contains(@title, 'Log in with your NetId')]"
XPATH_APPLY_BUTTON = "//span[text()='Apply']"
XPATH_APPLY_EXTERNALLY_BUTTON = "//span[contains(text(), 'Apply Externally')]"
XPATH_SUBMIT_APPLICATION_BUTTON = "//button//span[text()='Submit Application']"
XPATH_RESUME_BUTTON = "//button[contains(@aria-label, 'nicolas-ranabhat-resume.pdf')]"
XPATH_COVERLETTER_BUTTON = "//button[contains(@aria-label, 'coverletter')]"
XPATH_TRANSCRIPT_BUTTON = "//button[contains(@aria-label, 'transcript.pdf')]"

# Tag Name Selectors
TAG_OPTION = "option"

# Modal content selector
APPLY_MODAL_CONTENT_CSS = "span[data-hook='apply-modal-content']" 