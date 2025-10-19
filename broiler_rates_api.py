from fastapi import FastAPI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import time
import uvicorn

app = FastAPI(title="Poultry Rate Scraper API")

# Base URL template
BASE_URL = "https://poultrybaba.com/rates/history/broiler?month=Oct+2025&city={city}&productName=BROILER"

CITIES = [
    "Hasilpur", "Rahim yar Khan", "FortAbbas", "Chishtian", "Bahawalpur",
    "Larkana", "Baddin", "Dadu", "Taunsa", "Layyah", "Rajanpur", "Dera Ghazi Khan",
    "Muzaffir Garh", "Kot Addu", "Jhang", "Chiniot", "Faisalabad", "Toba Tek Sing",
    "Hafizabad", "Sialkot", "Gujranwala", "Wazirabad", "Gujrat", "Karachi", "Lahore",
    "Mirpur khas", "Vehari", "Burewala", "Khanewal", "Attock", "Talagang", "Chakwal",
    "Kahuta", "Rawalpindi", "Pakpattan", "Chichawatni", "Okara", "Sahiwal", "Arifwala",
    "Mianwali", "Sargodha", "Bakkar", "Nawab Shah", "Shikarpur", "Sukker"
]

def wait_for_non_na_text(driver, xpath, timeout=120):
    """
    Wait until the text content of an element (given by xpath)
    is not empty and not 'N/A'.
    """
    wait = WebDriverWait(driver, timeout)

    def text_not_na(d):
        try:
            elem = d.find_element(By.XPATH, xpath)
            txt = elem.text.split("Rs.")[-1].strip().lower()
            # return element if text is not n/a or empty
            return elem if txt and txt not in ["n/a", "na", "-"] else False
        except Exception:
            return False

    return wait.until(text_not_na)


def scrape_rate_for_city(city: str):
    """Scrape today's and yesterday's rate for a given city."""
    city_formatted = city.strip().title()
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    url = BASE_URL.format(city=city_formatted)

    result = {"City": city_formatted, "Today": None, "Yesterday": None}
    try:
        driver.get(url)

        # Wait for the "Today Rate" element to appear with actual number (not N/A)
        today_xpath = "//h2[contains(text(),'Today Rate of broiler')]/following::div[1]//h2[contains(text(),'Announced Rate')]"
        yesterday_xpath = "//h2[contains(text(),'Yesterday Rate of broiler')]/following::div[1]//h2[contains(text(),'Announced Rate')]"

        # Conditional wait: only apply wait-until-not-N/A to selected cities
        if city_formatted in CITIES:
            today_elem = wait_for_non_na_text(driver, today_xpath)
            yesterday_elem = wait_for_non_na_text(driver, yesterday_xpath)
        else:
            wait = WebDriverWait(driver, 5)
            today_elem = wait.until(EC.presence_of_element_located((By.XPATH, today_xpath)))
            yesterday_elem = wait.until(EC.presence_of_element_located((By.XPATH, yesterday_xpath)))

        # Extract the numbers cleanly
        result["Today"] = today_elem.text.split("Rs.")[-1].strip()
        result["Yesterday"] = yesterday_elem.text.split("Rs.")[-1].strip()

    except TimeoutException:
        result["Error"] = f"Timed out waiting for non-N/A values for {city_formatted}."
    except Exception as e:
        result["Error"] = str(e)
    finally:
        driver.quit()

    return result


@app.get("/")
def home():
    """Root endpoint: shows basic info."""
    return {
        "message": "Welcome to the Poultry Rate Scraper API",
        "usage": "Use /rates/{city} to fetch data for any city.",
        "example": "/rates/Lahore"
    }


@app.get("/rates/{city}")
def get_city_rate(city: str):
    """Fetch broiler rates for a given city."""
    data = scrape_rate_for_city(city)
    return data


# ==========================================================
# 🚀 AUTO-START SERVER WHEN SCRIPT RUNS
# ==========================================================
if __name__ == "__main__":
    print("🌐 Starting Poultry Rate Scraper API Server...")
    print("✅ Visit: http://127.0.0.1:8000/")
    uvicorn.run("broiler_rates_api:app", host="0.0.0.0", port=8000, reload=True)
