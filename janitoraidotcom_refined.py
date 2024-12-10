import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
from datetime import datetime
import logging

# ------------------------
# Janitorai.com Web Scraper
# ------------------------

# WebDriver initialisation v1.0
def initialise_webdriver_v1(browser="safari"):
    """
    Initializes the WebDriver based on the specified browser.
    
    Args:
        browser (str): Browser to use ("safari", "chrome", or "firefox").
        
    Returns:
        WebDriver: A Selenium WebDriver instance for the specified browser.
        
    Raises:
        ValueError: If an unsupported browser is specified.
        Exception: For any WebDriver initialization errors.
    """
    try:
        if browser.lower() == "chrome":
            return webdriver.Chrome()
        elif browser.lower() == "firefox":
            return webdriver.Firefox()
        elif browser.lower() == "safari":
            return webdriver.Safari()
        else:
            raise ValueError(f"Unsupported browser: {browser}")
    except Exception as e:
        raise Exception(f"Failed to initialise WebDriver: {str(e)}")

# WebDriver initialisation v2.0
def initialise_driver_v2(browser="safari"):
    try:
        if browser.lower() == "chrome":
            driver = webdriver.Chrome()
        elif browser.lower() == "firefox":
            driver = webdriver.Firefox()
        else:  # Default to Safari
            driver = webdriver.Safari()
        return driver
    except Exception as e:
        logging.error(f"Failed to initialize WebDriver: {e}")
        return None

def get_specialty(url="https://www.technoyuga.com/blog/janitor-ai/#What_is_Janitor_AI.com", browser="safari"):
    """Fetch specialty text from the provided URL."""
    try:
        # Initialize the WebDriver (modularized for browser flexibility)
        driver = initialise_webdriver_v1(browser)
        driver.get(url)

        # Wait for the target element to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/section[1]/div/div/div/section/div/div[1]/div/div[5]/div/p[5]"))
        )

        # Find the target <p> tag
        target_p_tag = driver.find_element(By.XPATH, "/html/body/div[2]/div/section[1]/div/div/div/section/div/div[1]/div/div[5]/div/p[5]")

        # Use BeautifulSoup for cleaner sibling navigation and processing
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        target_element = soup.find(text=target_p_tag.text).parent

        # Get the next 5 sibling elements
        sibling_elements = []
        current = target_element.find_next_sibling()
        while current and len(sibling_elements) < 5:
            sibling_elements.append(current.get_text(strip=True))
            current = current.find_next_sibling()

        # Combine all specialty text
        specialty_text = "\n".join(sibling_elements)

        # Return the formatted dictionary
        return {"specialty": specialty_text}

    except TimeoutException:
        return {"error": "Timeout: Unable to locate the target element within the specified wait time."}
    except NoSuchElementException:
        return {"error": "No such element: Unable to locate the target <p> tag or its siblings."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}
    finally:
        # Ensure the driver quits no matter what
        driver.quit()

def get_nsfw_policy():
    """
    Scrapes policy documents from given URLs to determine their NSFW-related policies.
    :return: A dictionary summarizing NSFW policy categories and their descriptions.
    """
    # URLs for Privacy Policy and related documents
    policy_urls = {
        "privacy_policy": "https://janitorai.com/policy",
        "terms_of_service": "https://janitorai.com/term",
        "faqs": "https://janitorai.com/faq",
        "community_guidelines": "https://janitorai.com/community"
    }
    
    # NSFW-related keyword categories
    categories = {
        "Advertised": ["explicit content", "nsfw content", "adult content", "nudity"],
        "Allowed but not advertised": ["content moderation", "user responsibility", "user-generated content"],
        "Prohibited": ["prohibited content", "restricted content", "no adult content", "banned"]
    }
    
    # Initialize results
    policies = {}

    for name, url in policy_urls.items():
        try:
            # Send GET request to fetch the policy page
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
            
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            policy_text = soup.get_text(separator=" ").lower()  # Get clean, normalized text

            # Match policy text to NSFW categories
            nsfw_category = "Unknown"
            for category, keywords in categories.items():
                if any(keyword in policy_text for keyword in keywords):
                    nsfw_category = category
                    break
            
            # Store result for the current policy document
            policies[name] = {
                "url": url,
                "nsfw_policy_category": nsfw_category,
                "summary": (
                    f"Policy mentions NSFW-related terms under '{nsfw_category}' category."
                    if nsfw_category != "Unknown" else
                    "No specific NSFW policy details found."
                )
            }
        except requests.exceptions.RequestException as e:
            # Handle network-related errors
            policies[name] = {
                "url": url,
                "nsfw_policy_category": "Error",
                "summary": f"Error fetching policy: {str(e)}"
            }
        except Exception as e:
            # Handle unexpected parsing or other errors
            policies[name] = {
                "url": url,
                "nsfw_policy_category": "Error",
                "summary": f"An unexpected error occurred: {str(e)}"
            }

    return {"nsfw_policy": policies}

# Get pricing information function
def get_pricing_info(search_query="janitorai pricing", browser="safari"):
    """
    Searches Google for the pricing information and retrieves the relevant snippet.

    :param search_query: The query to search for pricing information.
    :param browser: The browser to use (default: Safari).
    :return: Dictionary containing the pricing information or an error message.
    """
    driver = initialise_driver_v2(browser)
    if not driver:
        return {"error": "WebDriver initialization failed."}
    
    url = "https://www.google.com/"
    try:
        driver.get(url)
        
        # Find the search input field
        input_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "q"))
        )
        input_field.send_keys(search_query)
        input_field.send_keys(Keys.RETURN)  # Simulates hitting the 'Enter' key

        # Wait for search results to load
        search_results = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.VwiC3b"))
        )
        
        # Extract the text from the first relevant search result
        pricing_info = search_results[0].text  # Assumes the first result is relevant

        # Log the extracted information
        logging.info(f"Pricing Info Extracted: {pricing_info}")
    
    except Exception as e:
        logging.error(f"An error occurred while retrieving pricing info: {e}")
        pricing_info = f"Error occurred: {str(e)}"
    
    finally:
        driver.quit()

    return {"pricing": pricing_info}

def get_useful_links():
    """
    Returns a dictionary of useful links, ensuring all URLs are valid and reachable.
    """
    links = {
        "privacy_policy": "https://janitorai.com/policy",
        "terms_of_service": "https://janitorai.com/term",
        "faqs": "https://janitorai.com/faq",
        "guidelines": "https://janitorai.com/community",
        "janitorai_updates": "https://janitorai.com/updates",
        "janitorai_twitter_profile": "https://twitter.com/janitoraicom",
        "janitorai_subreddit": "https://www.reddit.com/r/JanitorAI_Official/"
    }

    # Validate URLs
    validated_links = {}
    for name, url in links.items():
        try:
            # Make a request to check if the URL is accessible
            response = requests.get(url, timeout=5)
            response.raise_for_status()  # Will raise an error for 4xx or 5xx status codes
            
            validated_links[name] = {
                "url": url,
                "status": "valid",
                "status_code": response.status_code
            }
        except requests.exceptions.RequestException as e:
            # Handle connection errors and invalid URLs
            validated_links[name] = {
                "url": url,
                "status": "invalid",
                "error_message": str(e)
            }

    return {"useful_links": validated_links}

def get_server_status():
    # Initialize the Selenium WebDriver (using Safari in this example)
    options = webdriver.Safari()  # Adjust options or use Chrome/Firefox for other setups
    driver = webdriver.Safari(options=options)
    
    status_url = "https://www.isitdownrightnow.com/downorjustme.php"
    target_url = "https://www.janitorai.com"
    
    try:
        # Record the start time for the first check
        first_checked = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Open the status-checking URL
        driver.get(status_url)
        
        # Wait for the input field to be available
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "url"))
        )
        
        # Find the input element and type the target URL
        input_field = driver.find_element(By.NAME, "url")
        input_field.clear()
        input_field.send_keys(target_url)
        
        # Record the submission start time
        submit_time_start = time.time()
        
        # Submit the form
        input_field.send_keys(Keys.RETURN)
        
        # Wait for the result to load (max 10 seconds wait)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "statusup"))
        )
        
        # Extract the server status message
        try:
            status_message = driver.find_element(By.CLASS_NAME, "statusup").text.strip()
        except:
            # Fallback to "statusdown" class if "statusup" is not found
            status_message = driver.find_element(By.CLASS_NAME, "statusdown").text.strip()
        
        # Calculate response time
        response_time = round(time.time() - submit_time_start, 3)
        
        # Record the last checked time
        last_checked = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Return the successful result
        return {
            "server_status": {
                "url": target_url,
                "first_checked": first_checked,
                "status": f"{status_message} ({status_url})",
                "response_time": response_time,
                "error": None,
                "last_checked": last_checked
            }
        }
    
    except Exception as e:
        # Handle errors gracefully and provide details
        last_checked = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return {
            "server_status": {
                "url": target_url,
                "first_checked": first_checked,
                "status": f"Error ({status_url})",
                "response_time": 0,
                "error": str(e),
                "last_checked": last_checked
            }
        }
    
    finally:
        # Ensure the WebDriver is closed after use
        driver.quit()

def get_language_support():
    url = "https://www.pompanobeachhigh.com/default/what-languages-does-janitor-ai-chat-support"

    # Initialize WebDriver
    options = webdriver.Safari()  # You can configure other browser options here
    try:
        driver = webdriver.Safari(options=options)
        driver.get(url)

        # Wait for the page to load completely
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "markdown.prose.w-full.break-words"))
        )

        # Get the page source for parsing
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Locate the target container
        article_body = soup.select_one('div.markdown.prose.w-full.break-words')
        if not article_body:
            return {"error": "Article body not found"}

        # Locate the specific header with 'Broad' in text
        header = article_body.find('p', string=lambda text: text and 'Broad' in text)
        if not header:
            return {"error": "Header with specified text not found"}

        # Locate the next <p> tag after the header
        next_element = header.find_next('p')
        if not next_element:
            return {"error": "No paragraph found after the header"}

        # Extract and clean the text
        language_support = next_element.text.strip()

    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}
    finally:
        # Quit the driver to free resources
        driver.quit()

    return {"languages_supported": language_support}

# ------------------------
# Save Data to JSON
# ------------------------

def save_to_json(data, filename="janitorai_dot_com_data.json"):
    with open(f"./{filename}", "w") as json_file:
        json.dump(data, json_file, indent=4)

# ------------------------
# Main Program
# ------------------------

def main():
    data = {}

    data.update(get_specialty())
    # print(data)

    data.update(get_nsfw_policy())
    # print(data["nsfw_policy"])

    data.update(get_pricing_info())
    # print(data["pricing"])

    data.update(get_useful_links())
    # print(data["useful_links"])

    data.update(get_server_status())
    # print(data["server_status"])

    data.update(get_language_support())
    # print(data["languages_supported"])
    
    save_to_json(data)

if __name__ == "__main__":
    main()