import time
import os
import undetected_chromedriver as uc
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Wejście na stronę
options = uc.ChromeOptions()
driver = uc.Chrome(options=options)

# ranges = [
#     ("2024", "2026", 26),   ~810 zapachów
#     ("2020", "2023", 33),   ~1020 zapachów
#     ("2015", "2019", 30),   ~930 zapachów
#     ("2010", "2014", 30),   ~930 zapachów
#     ("2000", "2009", 30),   ~930 zapachów
#     ("1900", "1999", 25),   ~780 zapachów
#     ("1700", "1899", 1)     ~60 zapachów
# ]

start_year = 2015
end_year = 2019
clicks = 30

# Sprawdzanie, czy perfum już jest na liście
perfume_details_links = set()
if os.path.exists('fragrance_links.txt'):
    with open('fragrance_links.txt', 'r', encoding='utf-8') as f:
        for line in f:
            perfume_details_links.add(line.strip())
print(f"Wczytano {len(perfume_details_links)} linków z poprzednich sesji.")


cookies_accepted = False

url = f"https://www.fragrantica.com/search/?godina={start_year}%3A{end_year}&spol=male~unisex"
print(f"\n--- Rozpoczynam zbieranie dla lat {start_year}-{end_year} ---")

driver.get(url)
time.sleep(3)

# Akceptacja cookies
if not cookies_accepted:
    try:
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[contains(@id, 'sp_message_iframe')]"))
        )

        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[title='Zaakceptować']"))
        )
        accept_button.click()
        print("Kliknięto 'Zaakceptować'!")

        driver.switch_to.default_content()

        cookies_accepted = True
    except Exception as e:
        print("Nie znaleziono okna cookies.")
        driver.switch_to.default_content()




# Rozwinięcie listy perfum
for i in range(clicks):
    try:
        btn_show_more = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Show more results')]"))
        )

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_show_more)
        time.sleep(1)

        btn_show_more.click()
        print("Kliknięto Show more results!")

        wait_time = 5 if i < 50 else 10
        time.sleep(wait_time)
    except TimeoutException:
        print(f"Przycisk Show More zniknął po {i} kliknięciach.")
        break



# Pobranie linków do perfum
perfume_cards = WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.CLASS_NAME, "prefumeHbox"))
)
new_links_to_save = []


links_in_this_range = 0

for card in perfume_cards:
    link_el = card.find_element(By.XPATH, "ancestor-or-self::a | .//a")
    link = link_el.get_attribute("href")
    if "/perfume/" in link and link not in perfume_details_links:
        perfume_details_links.add(link)
        new_links_to_save.append(link)
        links_in_this_range += 1

print(f"Zakończono przedział {start_year}-{end_year}. Pobrano {links_in_this_range} nowych zapachów.")
print(f"Łączna liczba perfum w bazie: {len(perfume_details_links)}\n")

# Zapis do pliku
with open('fragrance_links.txt', 'a', encoding='utf-8') as f:
    for l in new_links_to_save:
        f.write(l + '\n')
        print("Link został dodany: " + l)

driver.close()
driver.quit()
