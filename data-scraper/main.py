import random
import time
import os
import shutil
import csv
import json
import builtins
import undetected_chromedriver as uc
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


original_print = builtins.print

def print_with_timestamp(*args, **kwargs):
    timestamp = time.strftime("[%H:%M:%S]")
    original_print(timestamp, *args, **kwargs)

builtins.print = print_with_timestamp


def init_driver():
    options = uc.ChromeOptions()
    options.page_load_strategy = 'eager'
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    driver = uc.Chrome(options=options, version_main=146)
    driver.set_page_load_timeout(45)
    return driver


def update_queue(links_list, file_path):
    links_list.pop(0)
    with open(file_path, 'w', encoding='utf-8') as f:
        for link in links_list:
            f.write(link + '\n')


def parse_fragrantica_number(text):
    text = text.lower().strip().replace(',', '')
    try:
        if 'k' in text:
            return int(float(text.replace('k', '')) * 1000)
        elif text:
            return int(text)
        else:
            return 0
    except:
        return 0


def extract_perfume_data(driver, url, first_run):
    driver.get(url)
    time.sleep(2)

    if first_run:
        try:
            WebDriverWait(driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[contains(@id, 'sp_message_iframe')]"))
            )

            accept_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[title='Zaakceptować']"))
            )
            accept_button.click()
            print("Kliknięto 'Zaakceptować'!")
            time.sleep(1.5)
            driver.switch_to.default_content()
        except:
            pass


    try:
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(0.5)
    except Exception:
        pass



    perfume_data = {
        "url": url,
        "name": "",
        "brand": "",
        "rating": 0.0,
        "votes_count": 0,
        "main_accords": {},
        "top_notes": {},
        "middle_notes": {},
        "base_notes": {},
        "longevity": {},
        "sillage": {},
        "gender_votes": {},
        "price_value": {},
        "reminds_me_of": []
    }

    h1_element = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "h1"))
    )
    full_title = h1_element.text
    perfume_data["name"] = full_title


    brand_element = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//p[@itemprop='brand']//span[@itemprop='name']"))
    )
    brand = brand_element.text
    perfume_data["brand"] = brand


    rating_element = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//span[@itemprop='ratingValue']"))
    )
    rating = float(rating_element.text)
    perfume_data["rating"] = rating

    votes_count_element = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//span[@itemprop='ratingCount']"))
    )
    votes_count = int(votes_count_element.text.replace(",", ""))
    perfume_data["votes_count"] = votes_count


    accords_bars_elements = WebDriverWait(driver, 5).until(
        EC.presence_of_all_elements_located(
            (By.XPATH, "//h6[text()='main accords']/following-sibling::div//div[contains(@style, 'width')]")),
        message="Odrzucono: Brak głównych akordów (main accords)"
    )

    for bar in accords_bars_elements:
        accord_name = bar.text.strip()

        style_text = bar.get_attribute("style")
        styles = style_text.split(';')

        for style in styles:
            if "width" in style:
                accord_width = float(style.replace("width:", "").replace("%", "").strip())

                perfume_data["main_accords"][accord_name] = accord_width



    pyramid_levels = {
        "Top": "top_notes",
        "Middle": "middle_notes",
        "Base": "base_notes"
    }

    is_pyramid_type = False

    for level_name, dict_key in pyramid_levels.items():
        xpath = f"//h4//span[contains(text(), '{level_name}')]/following::div[contains(@class, 'pyramid-level-container')][1]//span[contains(@class, 'pyramid-note-label')]"
        notes_elements = driver.find_elements(By.XPATH, xpath)

        if notes_elements:
            is_pyramid_type = True

        for note in notes_elements:
            note_name = note.text.strip()
            note_opacity = 0.0
            if note_name:
                parent_element = note.find_element(By.XPATH, "./..")
                style_text = parent_element.get_attribute("style")

                if style_text:
                    styles = style_text.split(';')
                    for style in styles:
                        if "opacity" in style:
                            note_opacity = float(style.replace("opacity:", "").replace("%", "").strip())
                perfume_data[dict_key][note_name] = note_opacity
    if not is_pyramid_type:
        xpath_linear = "//div[contains(@class, 'pyramid-level-container')]//span[contains(@class, 'pyramid-note-label')]"
        linear_notes_elements = driver.find_elements(By.XPATH, xpath_linear)
        for note in linear_notes_elements:
            note_name = note.text.strip()
            note_opacity = 0.0
            if note_name:
                parent_element = note.find_element(By.XPATH, "./..")
                style_text = parent_element.get_attribute("style")

                if style_text:
                    styles = style_text.split(';')
                    for style in styles:
                        if "opacity" in style:
                            note_opacity = float(style.replace("opacity:", "").replace("%", "").strip())
                perfume_data["top_notes"][note_name] = note_opacity
                perfume_data["middle_notes"][note_name] = note_opacity
                perfume_data["base_notes"][note_name] = note_opacity

    for i in range(20):
        try:
            longevity_header = WebDriverWait(driver, 0.5).until(
                EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'LONGEVITY')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                                  longevity_header)
            time.sleep(1.0)
            break
        except TimeoutException:
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(0.3)


    longevities = ["very weak", "weak", "moderate", "long lasting", "eternal"]

    for label in longevities:
        xpath = (
            f"//div[contains(@class, 'tw-perf-card') and .//span[contains(text(), 'LONGEVITY')]]"
            f"//span[normalize-space(text())='{label}']/parent::div/following-sibling::div[contains(@class, 'text-right')]/span"
        )
        try:
            longevity_vote_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            longevity_vote_text = longevity_vote_element.text.strip()

            if 'k' in longevity_vote_text:
                longevity_votes_count = int(float(longevity_vote_text.replace('k', '')) * 1000)
            elif longevity_vote_text:
                longevity_votes_count = int(longevity_vote_text)
            else:
                longevity_votes_count = 0
            perfume_data["longevity"][label] = longevity_votes_count
        except TimeoutException:
            perfume_data["longevity"][label] = 0



    sillages = ["intimate", "moderate", "strong", "enormous"]

    for label in sillages:
        xpath = (
            f"//div[contains(@class, 'tw-perf-card') and .//span[contains(text(), 'SILLAGE')]]"
            f"//span[normalize-space(text())='{label}']/parent::div/following-sibling::div[contains(@class, 'text-right')]/span"
        )
        try:
            sillage_vote_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            sillage_vote_text = sillage_vote_element.text.strip()

            sillage_votes_count = parse_fragrantica_number(sillage_vote_text)
            perfume_data["sillage"][label] = sillage_votes_count
        except TimeoutException:
            perfume_data["sillage"][label] = 0

    for i in range(15):
        try:
            gender_header = WebDriverWait(driver, 0.5).until(
                EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'GENDER')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                                  gender_header)
            time.sleep(1.0)
            break
        except TimeoutException:
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(0.3)


    genders = ["female", "more female", "unisex", "more male", "male"]

    for label in genders:
        xpath = (
            f"//div[contains(@class, 'tw-perf-card') and .//span[contains(text(), 'GENDER')]]"
            f"//span[normalize-space(text())='{label}']/parent::div/following-sibling::div[contains(@class, 'text-right')]/span"
        )
        try:
            gender_vote_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            gender_vote_text = gender_vote_element.text.strip()

            gender_votes_count = parse_fragrantica_number(gender_vote_text)
            perfume_data["gender_votes"][label] = gender_votes_count
        except TimeoutException:
            perfume_data["gender_votes"][label] = 0



    price_values = ["way overpriced", "overpriced", "ok", "good value", "great value"]

    for label in price_values:
        xpath = (
            f"//div[contains(@class, 'tw-perf-card') and .//span[contains(text(), 'PRICE VALUE')]]"
            f"//span[normalize-space(text())='{label}']/parent::div/following-sibling::div[contains(@class, 'text-right')]/span"
        )
        try:
            price_value_votes_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            price_value_vote_text = price_value_votes_element.text.strip()

            price_votes_count = parse_fragrantica_number(price_value_vote_text)
            perfume_data["price_value"][label] = price_votes_count
        except TimeoutException:
            perfume_data["price_value"][label] = 0


    for i in range(15):
        try:
            reminds_header = WebDriverWait(driver, 0.5).until(
                EC.presence_of_element_located((By.XPATH,
                                                "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'reminds me of')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                                  reminds_header)
            time.sleep(1.5)
            break
        except TimeoutException:
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(0.3)



    time.sleep(1)

    try:
        cards = driver.find_elements(By.CSS_SELECTOR, "div.tw-carousel-perfume-card")

        reminds_list = []

        for card in cards:
            try:
                brand = card.find_element(By.CSS_SELECTOR, "p.text-zinc-400").text.strip()
                name = card.find_element(By.CSS_SELECTOR, "p.text-sm").text.strip()
                up_text = card.find_element(By.CSS_SELECTOR, r"div.hover\:text-teal-500 span.text-xs").text
                upvotes = parse_fragrantica_number(up_text)

                down_text = card.find_element(By.CSS_SELECTOR, r"div.hover\:text-amber-500 span.text-xs").text
                downvotes = parse_fragrantica_number(down_text)

                reminds_list.append({"name": name, "brand": brand, "upvotes": upvotes, "downvotes": downvotes})

            except Exception:
                continue

            if len(reminds_list) >= 10:
                break

        perfume_data["reminds_me_of"] = reminds_list

    except Exception as e:
        print(f"Błąd podczas szukania sekcji podobnych: {e}")
        perfume_data["reminds_me_of"] = []

    if not perfume_data["top_notes"] and not perfume_data["middle_notes"] and not perfume_data["base_notes"]:
        raise ValueError("Odrzucono: Brak jakichkolwiek nut zapachowych")

    if sum(perfume_data["longevity"].values()) == 0:
        raise ValueError("Odrzucono: Brak głosów w sekcji Longevity")

    if sum(perfume_data["sillage"].values()) == 0:
        raise ValueError("Odrzucono: Brak głosów w sekcji Sillage")

    if sum(perfume_data["gender_votes"].values()) == 0:
        raise ValueError("Odrzucono: Brak głosów w sekcji Gender")

    if sum(perfume_data["price_value"].values()) == 0:
        raise ValueError("Odrzucono: Brak głosów w sekcji Price Value")

    if not perfume_data["reminds_me_of"]:
        raise ValueError("Odrzucono: Brak podobnych zapachów (Reminds me of)")

    return perfume_data





original_file = 'fragrance_links.txt'
queue_file = 'fragrance_links_queue.txt'
csv_file = 'raw_data.csv'
failed_file = 'failed_links.txt'
screenshots_dir = 'screenshots'

if not os.path.exists(queue_file):
    shutil.copy(original_file, queue_file)

with open(queue_file, 'r', encoding='utf-8') as f:
    links_to_scrape = [line.strip() for line in f if line.strip()]

print(f"Pozostało {len(links_to_scrape)} w kolejce!")

csv_columns = [
    "url",
    "name",
    "brand",
    "rating",
    "votes_count",
    "main_accords",
    "top_notes",
    "middle_notes",
    "base_notes",
    "longevity",
    "sillage",
    "gender_votes",
    "price_value",
    "reminds_me_of"
]
csv_exists = os.path.exists(csv_file)

if len(links_to_scrape) > 0:
    driver = init_driver()

    first_run = True

    success_count = 0
    consecutive_errors = 0

    while len(links_to_scrape) > 0:
        current_url = links_to_scrape[0]
        try:
            if not first_run:
                delay = random.uniform(5.5, 9.5)
                time.sleep(delay)

            extracted_data = extract_perfume_data(driver, current_url, first_run)

            first_run = False

            row_data = {}
            for key in csv_columns:
                if isinstance(extracted_data.get(key), (dict, list)):
                    row_data[key] = json.dumps(extracted_data[key], ensure_ascii=False)
                else:
                    row_data[key] = extracted_data.get(key)

            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=csv_columns)
                if not csv_exists:
                    writer.writeheader()
                    csv_exists = True
                writer.writerow(row_data)

            update_queue(links_to_scrape, queue_file)

            consecutive_errors = 0
            success_count += 1

            print(f"[Zostało: {len(links_to_scrape)}] Zapisano: {extracted_data.get('name')} ({current_url})")

            if success_count % 150 == 0:
                print(f"\nPobrano {success_count} zapachów. Robię 15 minut przerwy...")
                try:
                    driver.quit()
                except:
                    pass

                time.sleep(900)

                driver = init_driver()

                first_run = True
                print("Koniec przerwy.")

        except Exception as e:
            error_message = str(e)
            print(f"Błąd: {e}")

            with open(failed_file, 'a', encoding='utf-8') as f:
                f.write(current_url + '\n')

            update_queue(links_to_scrape, queue_file)

            if "odrzucono" in error_message.lower():
                consecutive_errors = 0
            else:
                consecutive_errors += 1

            if consecutive_errors >= 5:
                print("\nWykryto 5 błędów z rzędu, Robię 2 godziny przerwy...")

                timestamp = time.strftime("%Y%m%d_%H%M%S")
                screenshot_filename = f"error_5_in_a_row_{timestamp}.png"
                screenshot_path = os.path.join(screenshots_dir, screenshot_filename)

                try:
                    driver.save_screenshot(screenshot_path)
                    print(f"Zapisano zrzut ekranu do: {screenshot_path}")
                except Exception as ss_error:
                    print(f"Nie udało się zapisać zrzutu ekranu: {ss_error}")

                try:
                    driver.quit()
                except:
                    pass

                time.sleep(7200)
                consecutive_errors = 0
                success_count = 0

                driver = init_driver()

                first_run = True
                print("Koniec przerwy po błędach.")


            elif "invalid session id" in error_message.lower() or "read timed out" in error_message.lower() or "timeout" in error_message.lower() or "chrome not reachable" in error_message.lower() or "stacktrace" in error_message.lower() or "gethandleverifier" in error_message.lower():
                print("Zawieszenie przeglądarki, Szybki restart...")
                try:
                    driver.quit()
                except:
                    pass
                time.sleep(3)

                driver = init_driver()

                first_run = True
                print(">>> WebDriver zrestartowany.")

    print("\nKolejka jest pusta. Pobieranie zakończone pomyślnie.")
    driver.quit()
else:
    print("Kolejka jest już pusta.")
