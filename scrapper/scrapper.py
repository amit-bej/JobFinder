from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
import time
import os

def scrape_naukri(role="python developer", location="hyderabad-secunderabad", experience=None, page_start=1):
    chromelocation = r"C:\\Users\\Amith Ranjan Bej\\Desktop\\Projects\\JobFinder\\drivers\\chromedriver.exe"
    service = Service(executable_path=chromelocation)
    driver = webdriver.Chrome(service=service)

    clean_loc = location.lower().strip()
    location_map = {
        "hyderabad": "hyderabad-secunderabad",
        "bangalore": "bengaluru",
        "gurgaon": "gurugram"
    }
    
    if clean_loc in location_map:
        location_slug = location_map[clean_loc]
    else:
        location_slug = clean_loc.replace(" ", "-")

    role_slug = role.lower().strip().replace(" ", "-")
    base_url = f"https://www.naukri.com/{role_slug}-jobs-in-{location_slug}"

    job_details = []
    seen_links = set()
    page_count = 0
    i = page_start
    
    max_pages = 10
    
    print(f"Starting scrape for {role} in {location} with experience {experience}")

    try:
        while i < page_start + max_pages:
            page_count += 1
            if i == 1:
                url = base_url
            else:
                url = f"{base_url}-{i}"
            
            if experience is not None:
                url += f"?experience={experience}"
            
            print(f"Scraping page {i}: {url}")
            driver.get(url)

            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//div[contains(@class,'srp-jobtuple-wrapper')] | //article[contains(@class,'jobTuple')]")
                    )
                )
            except Exception as e:
                print(f"Error waiting for elements on page {i}: {e}")
                break

            cards = driver.find_elements(By.XPATH, "//div[contains(@class,'srp-jobtuple-wrapper')] | //article[contains(@class,'jobTuple')]")
            print(f"Found {len(cards)} cards on page {i}.")
            
            if not cards:
                print("No cards found. Exiting loop.")
                break

            for c in cards:
                try:
                    title_elem = c.find_element(By.CSS_SELECTOR, ".title")
                    title = title_elem.get_attribute("innerText")
                    link = title_elem.get_attribute("href")
                except:
                    title = "NA"
                    link = "NA"
                
                try:
                    company = c.find_element(By.CSS_SELECTOR, ".subTitle").get_attribute("innerText")
                except:
                    try:
                        company = c.find_element(By.CSS_SELECTOR, ".comp-name").get_attribute("innerText")
                    except:
                        company = "NA"

                try:
                    tags = c.find_elements(By.CSS_SELECTOR, "ul.tags-gt li")
                    if not tags:
                        tags = c.find_elements(By.CSS_SELECTOR, "ul.tags li")
                    skill = ", ".join([tag.get_attribute("innerText") for tag in tags])
                except Exception:
                    skill = "NA"
                    
                try:
                    experience_elem = c.find_element(By.CSS_SELECTOR, ".expwdth").get_attribute("innerText")
                except:
                    experience_elem = "NA"

                if link != "NA" and link not in seen_links:
                    seen_links.add(link)
                    job_details.append({
                        "Company Name": company,
                        "Title": title,
                        "Skill": skill,
                        "Link": link,
                        "Experience": experience_elem
                    })
                elif link == "NA":
                     job_details.append({
                        "Company Name": company,
                        "Title": title,
                        "Skill": skill,
                        "Link": link,
                        "Experience": experience_elem
                    })
            
            time.sleep(2)
            i+=1

    except Exception as e:
        print(f"An error occurred during scraping: {e}")
    finally:
        driver.quit()

    df = pd.DataFrame(job_details, columns=["Company Name", "Title", "Skill", "Link", "Experience"])
    output_file = "naukri_jobs.csv"
    df.to_csv(output_file, index=False)
    print(f"Saved {len(df)} jobs to {output_file}")
    
    return df
