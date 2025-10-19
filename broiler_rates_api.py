from fastapi import FastAPI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import uvicorn

app = FastAPI(title="Poultry Rate Scraper API")

# Base URL template
BASE_URL = "https://poultrybaba.com/rates/history/broiler?month=Oct+2025&city={city}&productName=BROILER"


def scrape_rate_for_city(city: str):
    """Scrape today's and yesterday's rate for a given city."""
    city_formatted = city.strip().title()
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 5)
    url = BASE_URL.format(city=city_formatted)

    result = {"City": city_formatted, "Today": None, "Yesterday": None}
    try:
        driver.get(url)
        today_elem = wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//h2[contains(text(),'Today Rate of broiler')]/following::div[1]//h2[contains(text(),'Announced Rate')]")
            )
        )
        yesterday_elem = wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//h2[contains(text(),'Yesterday Rate of broiler')]/following::div[1]//h2[contains(text(),'Announced Rate')]")
            )
        )

        time.sleep(5)  # ensure content fully loaded
        result["Today"] = today_elem.text.split("Rs.")[-1].strip()
        result["Yesterday"] = yesterday_elem.text.split("Rs.")[-1].strip()
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
