import time
import uuid
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.proxy import Proxy, ProxyType
from pymongo import MongoClient
import pickle,base64,json

def setup_driver(PROXYMESH_AUTH,gui=False):
    chrome_options = Options()
    if not gui:
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    # Proxy configuration
    proxy = Proxy()
    proxy.proxy_type = ProxyType.MANUAL
    proxy.http_proxy = "rotating.proxymesh.com:31280"  # Use rotating proxy endpoint
    proxy.ssl_proxy = "rotating.proxymesh.com:31280"

    # Launch ChromeDriver with proxy and credentials
    service = Service("./chromedriver.exe")  # Replace with the correct path to ChromeDriver
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Add proxy authentication
    auth_str = PROXYMESH_AUTH  # Replace with your ProxyMesh credentials
    auth_encoded = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
    driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {
        "headers": {
            "Proxy-Authorization": f"Basic {auth_encoded}"
        }
    })

    return driver


# Function to log in to Twitter
def login_to_twitter(driver,TWITTER_MOBILE,TWITTER_EMAIL,TWITTER_PASSWORD):
    driver.get("https://twitter.com/login")
    time.sleep(2)  # Wait for the login page to load

    try:
        # Load cookies if available
        try:
            with open("twitter_cookies.pkl", "rb") as cookies_file:
                cookies = pickle.load(cookies_file)
                for cookie in cookies:
                    driver.add_cookie(cookie)
            driver.refresh()
            time.sleep(2)
        except FileNotFoundError:
            print("No cookies found, proceeding with manual login.")

        # Check if login is still required
        if "login" in driver.current_url:
            username_field = driver.find_element(By.NAME, "text")
            username_field.send_keys(TWITTER_MOBILE)  # Replace with your Twitter username or email
            username_field.send_keys(Keys.RETURN)
            time.sleep(2)

            try:
                usercheck_span = driver.find_element(By.NAME, "text")
                usercheck_span.send_keys(TWITTER_EMAIL)
                usercheck_span.send_keys(Keys.RETURN)
                time.sleep(2)
            except Exception as e:
                print(e,"Error ")
            


            password_field = driver.find_element(By.NAME, "password")
            password_field.send_keys(TWITTER_PASSWORD)  # Replace with your Twitter password
            password_field.send_keys(Keys.RETURN)
            time.sleep(2)

            # Save cookies for future use
            with open("twitter_cookies.pkl", "wb") as cookies_file:
                pickle.dump(driver.get_cookies(), cookies_file)

    except Exception as e:
        print("Error during login:", e)

# Function to fetch trending topics
def fetch_trending_topics(driver):
    driver.get("https://twitter.com")
    # time.sleep(1)  # Wait for the page to load fully
    top_trends = []
    attempt=0
    parent_div=None
    try:
        while attempt < 3:
            try:
                # Try to find the parent div
                parent_div = driver.find_elements(By.XPATH, '//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div[2]/div/div[2]/div/div/div/div[4]/section/div/div')
                
                # If found, break out of the loop
                if parent_div:
                    print("Parent div found!")
                    break
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
            
            # Wait for 3 seconds before retrying
            attempt += 1
            time.sleep(3)
        if parent_div is None:
            print("Failed to find parent div after maximum retries.")
            return None
        time.sleep(3)
        for trend in parent_div:
            try:
                # span_elements = trend.find_elements(By.XPATH, './/span[starts-with(text(), "#")]')
                span_elements = trend.find_elements(By.XPATH, './/div[contains(@class, "r-a023e6")]/span')
                # Iterate through each span element and print the text
                for span in span_elements:
                    print(span.text)
                    if span.text!="Show more":
                        top_trends.append(span.text)
            except Exception as e:
                print(f"Could not extract spans: {e}")
        
        # print(trends)
        # top_trends = [trend.text for trend in trends if trend.text][:5]
    except Exception as e:
        print("Error fetching trends:", e)

    return top_trends

# Function to store data in MongoDB
def store_in_mongo(data,MONGO_URI,DB_NAME,COLLECTION_NAME):
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    collection.insert_one(data)
    print("Data successfully stored in MongoDB")

def print_current_ip(driver):
    try:
        driver.get("https://httpbin.org/ip")  # External service to check IP
        body_text = driver.find_element("tag name", "body").text  # Extract the response text
        ip_data = json.loads(body_text)  # Parse the JSON response
        print("Current IP Address:", ip_data["origin"])
        if ip_data["origin"] is not None:
            return ip_data["origin"]
        else :
            return "Failed to get IP"
    except Exception as e:
        print("Error fetching IP:", e)
        return "Failed to get IP"

# Main function
def main():
    unique_id = str(uuid.uuid4())
    # notify id to user
    driver = setup_driver()

    try:
        login_to_twitter(driver)
        top_trends = fetch_trending_topics(driver)
        ip_address = print_current_ip(driver)
        
        if top_trends:
            data = {
                "unique_id": unique_id,
                "trend1": top_trends[0] if len(top_trends) > 0 else None,
                "trend2": top_trends[1] if len(top_trends) > 1 else None,
                "trend3": top_trends[2] if len(top_trends) > 2 else None,
                "trend4": top_trends[3] if len(top_trends) > 3 else None,
                "trend5": top_trends[4] if len(top_trends) > 4 else None,
                "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ip_address": ip_address,
            }
            store_in_mongo(data)
        else:
            print("No trends found.")

    except Exception as e:
        print("An error occurred:", e)

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
