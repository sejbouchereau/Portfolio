from pprint import pprint
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple
import pandas as pd
import json
import time
import requests
import csv

CENTRIS = "https://www.centris.ca/fr/propriete~a-vendre~laval?view=Thumbnail"
DUPROPRIO = "https://duproprio.com/fr/rechercher/liste?search=true&regions%5B0%5D=13&cities%5B0%5D=101&cities%5B1%5D=1019&cities%5B2%5D=108&cities%5B3%5D=1179&cities%5B4%5D=1198&cities%5B5%5D=1281&cities%5B6%5D=1445&cities%5B7%5D=1660&cities%5B8%5D=1666&cities%5B9%5D=17684&cities%5B10%5D=18329&cities%5B11%5D=25530&cities%5B12%5D=25531&cities%5B13%5D=25532&cities%5B14%5D=25533&cities%5B15%5D=25534&cities%5B16%5D=25535&cities%5B17%5D=460&cities%5B18%5D=573&cities%5B19%5D=677&cities%5B20%5D=702&cities%5B21%5D=9892&min_price=100000&max_price=2000000&lot_dimension_sq_feet=8000~50000&parent=1&pageNumber=1&sort=-published_at"
INFO_REGLEMENTS = "https://info-reglements.laval.ca/recherche/"
VILLES = ["Blainville", "Terrebonne", "Mirabel", "Mascouche", "Saint-Eustache", "Boisbriand", "Sainte-Thérèse"]
MIN_AREA = "8000"
MAX_AREA = "50000"
MIN_PRICE = "100000"
MAX_PRICE = "2000000"
MAX_CENTRIS_PAGES = 5
MAX_DUPROPRIO_PAGES = 5
CENTRIS_MAX_WORKERS = 3
INFO_MAX_WORKERS = 2
SLEEP = 2
CENTRIS_PRICES = {"100000": 9, "200000": 13, "300000": 17, "400000": 21, "500000": 25, "600000": 27, "700000": 29,
                  "800000": 31, "900000": 33, "1000000": 35, "1250000": 36, "1500000": 37, "1750000": 38, "2000000": 39,
                  "3000000": 40, "4000000": 41, "5000000": 42, "7500000": 43, "10000000": 44, "15000000": 45,
                  "20000000": 46}
EXCEL_FILE = "new_properties.xlsx"
JSON_FILE = "new_properties.json"
ADDRESSES_FILE = "adresses.txt"
CSV_FILE = "csv_properties.csv"
ALL_PROPERTY_TABLE = "https://api.airtable.com/v0/appiK6NVCpDFrdDv5/Listings"
WATCHLIST_TABLE = "Watchlist"
LISTINGS_TABLE = "Listings"

options = Options()
options.add_experimental_option("detach", True)
options.add_argument("--incognito")

# driver = webdriver.Chrome(options=options)    Source d’erreur depuis la dernière mise-à-jour


# Fonctions principales du scraper
def wait():
    time.sleep(SLEEP)
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '/html/body')))
    except:
        pass


def centris_enter(driver):
    wait()
    driver.maximize_window()
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "didomi-notice-learn-more-button")))
    notice = driver.find_element(By.ID, "didomi-notice-learn-more-button")
    notice.click()
    wait()
    refuse_all = driver.find_element(By.ID, "didomi-radio-option-disagree-to-all")
    refuse_all.click()
    wait()
    save = driver.find_element(By.XPATH,
                               '//button[contains(@class, "didomi-components-button didomi-button") and @aria-label="Enregistrer: Sauvegarder vos préférences et fermer"]')
    save.click()
    wait()


def info_urban_enter(driver):
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div/div[3]/div/div/div[1]/div[2]/button[1]')))
    time.sleep(15)
    notice = driver.find_element(By.XPATH, '/html/body/div/div[3]/div/div/div[1]/div[2]/button[1]')
    notice.click()


def get_cities(cities: List, driver):
    WebDriverWait(driver, 20).until(EC.presence_of_element_located(("css selector", "input.select2-search__field")))
    for city in cities:
        input_element = driver.find_element("css selector", "input.select2-search__field")
        time.sleep(0.5)
        input_element.send_keys(city)
        input_element.send_keys(" ")
        time.sleep(1)
        input_element.send_keys(Keys.ENTER)
        time.sleep(3)


def get_price_range(driver):
    WebDriverWait(driver, 20).until(EC.presence_of_element_located(("id", "SalePrice-button")))
    sale_price_button = driver.find_element("id", "SalePrice-button")
    sale_price_button.click()
    wait()
    min_handle = driver.find_element(By.CSS_SELECTOR, ".min-slider-handle")  # Localiser les poignées du slider
    max_handle = driver.find_element(By.CSS_SELECTOR, ".max-slider-handle")
    min_value_target = CENTRIS_PRICES[MIN_PRICE]  # Valeurs souhaitées pour prix min et max
    max_value_target = CENTRIS_PRICES[MAX_PRICE]
    min_value_now = int(min_handle.get_attribute('aria-valuenow'))  # Obtenir les valeurs actuelles
    max_value_now = int(max_handle.get_attribute('aria-valuenow'))
    min_steps = min_value_target - min_value_now  # Calculer les déplacements nécessaires
    max_steps = max_value_now - max_value_target
    min_handle.click()  # Déplacer le min vers la valeur souhaitée
    for _ in range(min_steps):
        min_handle.send_keys(Keys.ARROW_RIGHT)
        time.sleep(0.1)
    wait()
    max_handle.click()  # Déplacer le max vers la valeur souhaitée
    for _ in range(max_steps):
        max_handle.send_keys(Keys.ARROW_LEFT)
        time.sleep(0.1)
    wait()
    apply_changes = driver.find_element("class name", "btn-search")
    apply_changes.click()


def get_land_area(driver):
    wait()
    filter_button = driver.find_element("id", "filter-search")
    filter_button.click()
    wait()
    more_button = driver.find_element("css selector", 'button[data-target="#OtherCriteriaSection-secondary"]')
    more_button.click()
    wait()
    min_area_bar = driver.find_element("id", "LandArea-min")
    min_area_bar.send_keys(MIN_AREA)
    max_area_bar = driver.find_element("id", "LandArea-max")
    max_area_bar.send_keys(MAX_AREA)
    wait()
    apply_changes = driver.find_element("css selector", "button.btn.btn-primary.btn-search.js-trigger-search")
    apply_changes.click()
    wait()


def get_most_recent(driver):
    wait()
    drop_down_menu = driver.find_element("id", "dropdownSort")
    drop_down_menu.click()
    wait()
    most_recent = driver.find_element("css selector", "a.dropdown-item.option[data-option-value='3']")
    most_recent.click()
    wait()


def get_commercial_listings(driver):
    wait()
    drop_down_menu = driver.find_element(By.XPATH,
                                         "/html/body/main/div[8]/div/div/div/div/div[1]/div/div/div[2]/div[1]/div/div/span[1]/span[1]")
    drop_down_menu.click()
    wait()
    most_recent = driver.find_element(By.XPATH,
                                      "/html/body/main/div[8]/div/div/div/div/div[1]/div/div/div[2]/div[1]/div/div/span[2]/span/span[2]/ul/li[2]")
    most_recent.click()
    wait()


def extract_all_pages(driver) -> List[Dict]:
    wait()
    pager_current_element = driver.find_element(By.CSS_SELECTOR, 'li.pager-current').text
    parts = pager_current_element.split('/')  # Diviser les numéros en utilisant la barre oblique comme séparateur
    max_pages = int(parts[1].strip())  # Convertir en entier et enlever les espaces
    # max_pages = MAX_CENTRIS_PAGES  # Indique le nombre maximal de pages à scraper
    all_properties = []
    current_page = 1  # Compteur pour suivre le nombre de pages parcourues

    while True:  # Boucle pour extraire les propriétés sur chaque page
        properties = extract_single_page_thumbnails(driver)
        unique_properties = get_unique_properties(get_airtable_data(LISTINGS_TABLE), properties)
        all_properties.extend(unique_properties)
        if max_pages is not None and current_page >= max_pages:
            break

        try:
            next_page_button = driver.find_element(By.CSS_SELECTOR, 'li.next > a')
            next_page_button.click()
            current_page += 1
            wait()
        except:
            break

    return all_properties


def extract_all_new_pages(driver) -> List[Dict]:
    wait()
    pager_current_element = driver.find_element(By.CSS_SELECTOR, 'li.pager-current').text
    parts = pager_current_element.split('/')  # Diviser les numéros en utilisant la barre oblique comme séparateur
    #  max_pages = int(parts[1].strip())  # Convertir en entier et enlever les espaces
    max_pages = MAX_CENTRIS_PAGES  # Indique le nombre maximal de pages à scraper
    all_properties = []
    current_page = 1  # Compteur pour suivre le nombre de pages parcourues

    while True:  # Boucle pour extraire les propriétés uniques sur chaque page
        properties = extract_single_page_thumbnails(driver)
        unique_properties = get_unique_properties(get_airtable_data(LISTINGS_TABLE), properties)
        all_properties.extend(unique_properties)
        if max_pages is not None and current_page >= max_pages:
            break

        try:
            next_page_button = driver.find_element(By.CSS_SELECTOR, 'li.next > a')
            next_page_button.click()
            current_page += 1
            wait()
        except:
            break

    return all_properties


def extract_all_pages_blind(driver) -> List[Dict]:
    wait()
    pager_current_element = driver.find_element(By.CSS_SELECTOR, 'li.pager-current').text
    parts = pager_current_element.split('/')  # Diviser les numéros en utilisant la barre oblique comme séparateur
    max_pages = int(parts[1].strip())  # Convertir en entier et enlever les espaces
    # max_pages = MAX_CENTRIS_PAGES  # Indique le nombre maximal de pages à scraper
    all_properties = []
    current_page = 1  # Compteur pour suivre le nombre de pages parcourues

    while True:  # Boucle pour extraire les propriétés sur chaque page
        properties = extract_single_page_thumbnails(driver)
        all_properties.extend(properties)
        if max_pages is not None and current_page >= max_pages:
            break

        try:
            next_page_button = driver.find_element(By.CSS_SELECTOR, 'li.next > a')
            next_page_button.click()
            current_page += 1
            wait()
        except:
            break

    return all_properties


def extract_single_page_thumbnails(driver) -> List[Dict]:
    wait()
    property_elements = driver.find_elements(By.CSS_SELECTOR, 'div.property-thumbnail-item.thumbnailItem')
    properties = []

    for element in property_elements:  # Parcourir chaque élément de propriété
        property_info = {
            'Url': element.find_element(By.CSS_SELECTOR, 'a.property-thumbnail-summary-link').get_attribute(
                'href')}
        try:
            banner = element.find_element(By.CSS_SELECTOR, 'div.banner')
            property_info['Bannière'] = banner.text
        except Exception:
            property_info['Bannière'] = ""

        category_element = element.find_element(By.CSS_SELECTOR, 'span.category > div')
        property_info['Nom'] = category_element.text

        number_meta = element.find_element(By.CSS_SELECTOR, 'meta[itemprop="sku"]')
        property_info['# Centris'] = number_meta.get_attribute('content')

        price_meta = element.find_element(By.CSS_SELECTOR, 'div.price > meta[itemprop="price"]')
        property_info['Prix'] = int(price_meta.get_attribute('content'))

        address_element = element.find_element(By.CSS_SELECTOR, 'span.address > div:first-child')
        property_info['Adresse'] = address_element.text

        city_element = element.find_element(By.CSS_SELECTOR, 'span.address > div:nth-child(2)')
        property_info['Ville'] = city_element.text

        try:
            neighborhood_element = element.find_element(By.CSS_SELECTOR, 'span.address > div:nth-child(3)')
            property_info['Quartier'] = neighborhood_element.text
        except Exception:
            property_info['Quartier'] = ""

        properties.append(property_info)

    return properties


def scrape_one_property(url: str, property_info: Dict):
    if property_info.get("# Centris"):  # Pour les listings Centris avec un #Centris
        options = Options()  # Initialisation du driver pour chaque propriété
        options.add_experimental_option("detach", True)
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        wait()

        try:
            popup = driver.find_element(By.ID, "didomi-notice-agree-button")
            popup.click()
            wait()
        except Exception:
            pass

        try:
            description = driver.find_element(By.CSS_SELECTOR, 'div[itemprop="description"]').text
            property_info['Description'] = description
        except Exception:
            property_info['Description'] = "N/A"

        carac_containers = driver.find_elements(By.CSS_SELECTOR, 'div.carac-container')

        try:
            year_element = None
            for container in carac_containers:
                title_element = container.find_element(By.CSS_SELECTOR, 'div.carac-title').text
                if title_element == "Année de construction":
                    year_element = container.find_element(By.CSS_SELECTOR, 'div.carac-value span').text
                    break
            property_info['Année'] = year_element
        except Exception:
            property_info['Année'] = "N/A"

        try:
            area_element = None
            for container in carac_containers:
                title_element = container.find_element(By.CSS_SELECTOR, 'div.carac-title').text
                if title_element == "Superficie du terrain":
                    area_element = container.find_element(By.CSS_SELECTOR, 'div.carac-value span').text
                    break

            # Supprimer les espaces et l'unité de mesure (pc) pour obtenir uniquement le nombre
            area_numeric_str = area_element.replace(" ", "").replace("pc", "")
            property_info['Superficie (pi²)'] = area_numeric_str
        except Exception:
            property_info['Superficie (pi²)'] = "N/A"
        driver.quit()

    else:  # Pour les listings DuProprio sans #Centris
        options = Options()
        options.add_experimental_option("detach", True)
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        wait()

        try:
            popup = driver.find_element(By.ID, "onetrust-accept-btn-handler")
            popup.click()
            wait()
        except Exception:
            pass

        try:
            description = driver.find_element(By.CSS_SELECTOR, 'div.listing-owners-comments__description').text
            property_info['Description'] = description
        except Exception:
            property_info['Description'] = "N/A"

        carac_containers = driver.find_elements(By.CSS_SELECTOR, 'div.carac-container')

        try:
            year_container = driver.find_element(By.XPATH,
                                                 '//div[@class="listing-box__dotted-row" and div[1]="Année de construction"]')
            year_elements = year_container.find_elements(By.XPATH, './div')
            year = None
            for element in year_elements:
                if element.text.isdigit():
                    year = element.text
                    break

            if year:
                property_info['Année'] = year
        except Exception:
            property_info['Année'] = "N/A"

        area_elements = driver.find_elements(By.CSS_SELECTOR, 'span.listing-main-characteristics__number--dimensions')
        try:

            if len(area_elements) >= 2:  # Si au moins 2 éléments ont été trouvés, récupérer le texte du 2e élément
                property_info['Superficie (pi²)'] = area_elements[1].text.strip()
            else:
                property_info['Superficie (pi²)'] = area_elements[0].text.strip()
        except Exception:
            property_info['Superficie (pi²)'] = "N/A"
        driver.quit()

    return property_info


def scrape_all_properties(properties: List[Dict], laval_properties: List[Dict]):
    all_properties = []

    # Première étape : Récupérer les informations de base de toutes les propriétés
    with ThreadPoolExecutor(max_workers=CENTRIS_MAX_WORKERS) as executor:
        futures = []
        for property_info in properties:
            url = property_info['Url']
            future = executor.submit(scrape_one_property, url, property_info)
            futures.append(future)

        for future in as_completed(futures):
            try:
                property_data = future.result()  # Récupérer le dictionnaire de propriété à partir du Future
                all_properties.append(property_data)
                if "Laval" not in property_data["Ville"]:
                    post_new_property([property_data], get_airtable_data(WATCHLIST_TABLE))
                if "Laval" in property_data["Ville"] and all(not char.isdigit() for char in property_data["Adresse"]):
                    post_new_property([property_data], get_airtable_data(WATCHLIST_TABLE))
            except TimeoutException:
                pass

    # Deuxième étape : Mettre à jour les informations des propriétés de Laval
    with ThreadPoolExecutor(max_workers=INFO_MAX_WORKERS) as executor:
        laval_futures = []
        for property_info in laval_properties:
            address = property_info["Adresse"]
            if any(char.isdigit() for char in property_info.get('Adresse', '')):
                future = executor.submit(scrape_one_laval_property, address, property_info)
                laval_futures.append(future)

        for future in as_completed(laval_futures):
            try:
                laval_property_data = future.result()
                for existing_property_info in all_properties:
                    if existing_property_info.get("Adresse") == laval_property_data.get("Adresse"):
                        existing_property_info.update(laval_property_data)  # Ajoute les informations d’urbanisme
                        post_new_property([existing_property_info], get_airtable_data(WATCHLIST_TABLE))
                        break
            except TimeoutException:
                pass

    return all_properties


def scrape_one_laval_property(laval_address: str, property_info: Dict):
    options = Options()
    options.add_experimental_option("detach", True)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(INFO_REGLEMENTS)
    wait()
    info_urban_enter(driver)
    fields_to_extract = {  # Initialisation des champs à extraire et de leurs indices en tuples
        "Marge avant (m)": (1, 2),
        "Marge avant secondaire (m)": (1, 2),
        "Marge latérale (m)": (1, 2),
        "Marge arrière (m)": (1, 2),
        "Front bâti sur rue (%)": (1, 2),
        "Emprise au sol du bâtiment (%)": (1, 2),
        "4 logements ou plus": (1, 2, 3),
        "Isolé": (1, 2),
        "Jumelé": (1, 2),
        "Superficie de plancher (m2)": (1, 2),
        "Nombre d’étages": (1, 2),
        "Hauteur d'un bâtiment (m)": (1, 2),
        "Hauteur d’un étage (m)": (1, 2, 3),
        "Hauteur du plancher du rez-de-chaussée (m)": (1, 2, 3),
        "Largeur d'un plan de façade principale (m)": (1, 2),
        "Proportion d'un terrain en surface végétale (%)": (1, 2),
        "Proportion d’une cour avant ou avant secondaire en surface végétale (%)": (1, 2),
        "Proportion d’un terrain en surface carrossable (%)": (1, 2),
        "Largeur de l’entrée charretière (m)": (1, 2),
        "Par logement": (1,)
    }
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH,
                                            '/html/body/div/div[1]/div[2]/div/div/div/div/div[2]/div/div/div/div[1]/div[2]/input')))
        input_element = driver.find_element(By.XPATH,
                                            '/html/body/div/div[1]/div[2]/div/div/div/div/div[2]/div/div/div/div[1]/div[2]/input')
        if not laval_address.isdigit():
            input_element.send_keys(laval_address)
            wait()
            input_element.send_keys(" ")
        else:
            for char in laval_address:
                input_element.send_keys(char)
                time.sleep(0.2)
            wait()
        wait()
        time.sleep(2)
        input_element.send_keys(Keys.ENTER)
        wait()
        time.sleep(8)
    except Exception as e:
        pass  # Gérer les erreurs de saisie de l'adresse

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH,
                                            "/html/body/div/div[1]/div[2]/div/div[2]/div/div[2]/div[1]/div[2]/span")))
        lot_element = driver.find_element(By.XPATH,
                                          "/html/body/div/div[1]/div[2]/div/div[2]/div/div[2]/div[1]/div[2]/span").text
        property_info["Numéro(s) de lot"] = lot_element
    except Exception as e:
        property_info["Numéro(s) de lot"] = "-"

    try:
        sector_element = driver.find_element(By.XPATH,
                                             "/html/body/div/div[1]/div[2]/div/div[2]/div/div[2]/div[1]/div[3]/span").text
        property_info["Zone(s)"] = sector_element
    except Exception as e:
        property_info["Zone(s)"] = "-"

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH,
                                            '/html/body/div/div[1]/div[2]/div/div[2]/div/div[2]/div[2]/button')))
        more_details_button = driver.find_element(By.XPATH,
                                                  '/html/body/div/div[1]/div[2]/div/div[2]/div/div[2]/div[2]/button')
        more_details_button.click()
    except Exception as e:
        pass  # Gérer les erreurs de clic sur le bouton pour plus de détails

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH,
                                            "/html/body/div/div[1]/section/section/section/div/div[1]/div[2]/div/a/div/span[4]")))
        current_url = driver.current_url
        property_info["Lien zonage"] = str(current_url)
        zone_affected = driver.find_element(By.XPATH,
                                            "/html/body/div/div[1]/section/section/section/div/div[1]/div[2]/div/a/div/span[4]").text
        zone_parts = zone_affected.split()
        property_info["Zone affectée"] = f"{zone_parts[3]} m² {zone_parts[5]}"
    except Exception as e:
        property_info["Lien zonage"] = "-"
        property_info["Zone affectée"] = "-"

    try:
        piia_xpath = '/html/body/div/div[1]/section/section/div[3]/div[1]/div/section'
        element = driver.find_element(By.XPATH, piia_xpath)
        phrase_to_find = "Votre propriété est visée par un plan d'implantation et d'intégration architecturale (PIIA)."
        property_info["PIIA Grande artère applicable"] = True if phrase_to_find in element.text else False
    except Exception as e:
        property_info["PIIA Grande artère applicable"] = False

    try:
        positions = []
        rows = driver.find_elements(By.TAG_NAME, 'tr')

        for row in rows:  # Parcourir toutes les lignes (<tr>)
            cells = row.find_elements(By.TAG_NAME, 'td')  # Trouver tous les éléments <td> dans la ligne

            for i in range(len(cells)):  # Parcourir les cellules de la ligne
                cell_text = cells[i].text
                for field, indices in fields_to_extract.items():  # Vérifier chaque champ à extraire
                    if field in cell_text:
                        if field == "4 logements ou plus":
                            for index, cell in enumerate(cells):  # Pour "4 logements ou plus", vérifier la présence de "●"
                                if '●' in cell.text:  # Si "●" est trouvé, ajouter l’indice ajusté à la liste des positions
                                    adjusted_index = index + 1 - 3  # Ajustement des indices pour correspondre à 1, 2, 3
                                    positions.append(adjusted_index)
                            if len(positions) == 1:
                                adjusted_positions = [str("●") for pos in positions]
                                property_info[
                                    "4 propriétés ou plus"] = f'Isolé: {adjusted_positions[0]} | Jumelé: - | Contigu: -'
                            elif len(positions) == 2:
                                adjusted_positions = [str("●") for pos in positions]
                                property_info[
                                    "4 propriétés ou plus"] = f'Isolé: {adjusted_positions[0]} | Jumelé: {adjusted_positions[1]} | Contigu: -'
                            elif len(positions) == 3:
                                adjusted_positions = [str("●") for pos in positions]
                                property_info[
                                    "4 propriétés ou plus"] = f'Isolé: {adjusted_positions[0]} | Jumelé: {adjusted_positions[1]} | Contigu: {adjusted_positions[2]}'
                            else:
                                property_info[
                                    "4 propriétés ou plus"] = 'Isolé: - | Jumelé: - | Contigu: -'
                        else:  # Pour les autres champs, extraire les valeurs minimum et maximum
                            if len(indices) == 1:
                                min_value = cells[i + indices[0]].text if i + indices[0] < len(cells) else "-"
                                property_info[field] = f"{min_value.replace("\n", " ")}"
                            elif len(indices) == 2:
                                min_value = cells[i + indices[0]].text if i + indices[0] < len(cells) else "-"
                                max_value = cells[i + indices[1]].text if i + indices[1] < len(cells) else "-"
                                property_info[field] = f"{min_value.replace("\n", " ")} | {max_value.replace("\n", " ")}"
                            elif len(indices) == 3:
                                min_value = cells[i + indices[0]].text if i + indices[0] < len(cells) else None
                                max_value = cells[i + indices[1]].text if i + indices[1] < len(cells) else "-"
                                other_value = cells[i + indices[2]].text if i + indices[2] < len(cells) else "-"
                                if min_value is None:
                                    property_info[
                                        field] = f"{max_value.replace("\n", " ")} | {other_value.replace("\n", " ")}"
                                else:
                                    property_info[
                                        field] = f"{min_value.replace("\n", " ")} | {max_value.replace("\n", " ")} | {other_value.replace("\n", " ")}"

                if all(key in property_info for key in fields_to_extract):
                    break  # Sortir de la boucle si toutes les informations ont été extraites
    except Exception as e:
        print(f"Error extracting property fields: {e}")

    data = scrape_one_laval_PIIA(driver, property_info)  # Ajoute les informations de la carte interactive
    return data


def scrape_one_laval_PIIA(driver, laval_address: Dict):
    time.sleep(2)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH,
                                        '/html/body/div/div[1]/section/section/section/div/div[2]/a/button')))
    map_details_button = driver.find_element(By.XPATH,
                                             '/html/body/div/div[1]/section/section/section/div/div[2]/a/button')
    map_details_button.click()
    time.sleep(10)
    handles = driver.window_handles
    driver.switch_to.window(handles[-1])
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="widgets_Splash_Widget_14"]/div[2]/div[2]/div[2]/button')))
    clear_notice = driver.find_element(By.XPATH, '//*[@id="widgets_Splash_Widget_14"]/div[2]/div[2]/div[2]/button')
    clear_notice.click()
    wait()
    clear_info_box = driver.find_element(By.XPATH,
                                         '/html/body/div[2]/div[2]/div[1]/div[1]/div[3]/div[1]/div[1]/div/div[6]')
    clear_info_box.click()
    wait()
    more_filters_options = driver.find_element(By.XPATH,
                                               '/html/body/div[2]/div[2]/div[1]/div[12]/div[2]/div/div/div/div[3]/div/div[1]/div/div[1]')
    more_filters_options.click()
    wait()
    turn_off_all_filters = driver.find_element(By.XPATH,
                                               '/html/body/div[2]/div[2]/div[1]/div[12]/div[2]/div/div/div/div[3]/div/div[1]/div/div[3]/div[2]')
    turn_off_all_filters.click()
    wait()
    turn_on_main_layer = driver.find_element(By.XPATH,
                                             '/html/body/div[2]/div[2]/div[1]/div[12]/div[2]/div/div/div/div[3]/div/table/tbody[1]/tr[3]/td[1]/div[2]/div/div[1]')
    turn_on_main_layer.click()
    wait()
    box_1 = driver.find_element(By.XPATH,
                                '/html/body/div[2]/div[2]/div[1]/div[12]/div[2]/div/div/div/div[3]/div/table/tbody[1]/tr[4]/td/table/tr[1]/td[1]/div[3]/div/div[1]')
    box_1.click()
    box_2 = driver.find_element(By.XPATH,
                                '/html/body/div[2]/div[2]/div[1]/div[12]/div[2]/div/div/div/div[3]/div/table/tbody[1]/tr[4]/td/table/tr[3]/td[1]/div[3]/div/div[1]')
    box_2.click()
    box_3 = driver.find_element(By.XPATH,
                                '/html/body/div[2]/div[2]/div[1]/div[12]/div[2]/div/div/div/div[3]/div/table/tbody[1]/tr[4]/td/table/tr[5]/td[1]/div[3]/div/div[1]')
    box_3.click()
    box_4 = driver.find_element(By.XPATH,
                                '/html/body/div[2]/div[2]/div[1]/div[12]/div[2]/div/div/div/div[3]/div/table/tbody[1]/tr[4]/td/table/tr[7]/td[1]/div[3]/div/div[1]')
    box_4.click()
    box_5 = driver.find_element(By.XPATH,
                                '/html/body/div[2]/div[2]/div[1]/div[12]/div[2]/div/div/div/div[3]/div/table/tbody[1]/tr[4]/td/table/tr[9]/td[1]/div[3]/div/div[1]')
    box_5.click()
    wait()
    width = driver.execute_script('return window.innerWidth')  # Obtenir les dimensions de la fenêtre
    height = driver.execute_script('return window.innerHeight')

    mid_x = width // 2  # Calculer les coordonnées du milieu de la page
    mid_y = height // 2

    action = ActionChains(driver)  # Créer un objet ActionChains
    action.move_by_offset(mid_x, mid_y).click().perform()  # Déplacer la souris au milieu de la page et cliquer
    time.sleep(2)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH,
                                        '/html/body/div[2]/div[2]/div[1]/div[1]/div[3]/div[1]/div[2]/div/div[1]/div[2]/div[3]/table/tr[4]')))
    piia_cv = driver.find_element(By.XPATH,
                                  '/html/body/div[2]/div[2]/div[1]/div[1]/div[3]/div[1]/div[2]/div/div[1]/div[2]/div[3]/table/tr[4]/td[2]').text
    laval_address['PIIA Centre-Ville'] = piia_cv.capitalize()
    piia_tp = driver.find_element(By.XPATH,
                                  '/html/body/div[2]/div[2]/div[1]/div[1]/div[3]/div[1]/div[2]/div/div[1]/div[2]/div[3]/table/tr[5]/td[2]').text
    laval_address['PIIA territoire patrimonial'] = piia_tp.capitalize()
    piia_ga = driver.find_element(By.XPATH,
                                  '/html/body/div[2]/div[2]/div[1]/div[1]/div[3]/div[1]/div[2]/div/div[1]/div[2]/div[3]/table/tr[6]/td[2]').text
    laval_address['PIIA Grande artère'] = piia_ga.capitalize()
    piia_eb = driver.find_element(By.XPATH,
                                  '/html/body/div[2]/div[2]/div[1]/div[1]/div[3]/div[1]/div[2]/div/div[1]/div[2]/div[3]/table/tr[7]/td[2]').text
    laval_address["PIIA Ensemble bâti d'intérêt"] = piia_eb.capitalize()
    piia_nom = driver.find_element(By.XPATH,
                                   '/html/body/div[2]/div[2]/div[1]/div[1]/div[3]/div[1]/div[2]/div/div[1]/div[2]/div[3]/table/tr[10]/td[2]').text
    laval_address["Nom du territoire patrimonial"] = piia_nom

    driver.close()
    driver.switch_to.window(handles[0])
    driver.close()

    return laval_address


def duproprio_enter(driver):
    wait()
    driver.maximize_window()
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div[10]/div[2]/div/div[1]/div/div[2]/div/button[1]")))
    notice = driver.find_element(By.XPATH, "/html/body/div[10]/div[2]/div/div[1]/div/div[2]/div/button[1]")
    notice.click()
    wait()
    refuse_all = driver.find_element(By.XPATH, "/html/body/div[10]/div[3]/div/div[3]/div[1]/button[1]")
    refuse_all.click()
    wait()


def extract_all_duproprio_pages(driver) -> List[Dict]:
    wait()
    all_properties = []
    current_page = 1  # Compteur pour suivre le nombre de pages parcourues
    max_pages = MAX_DUPROPRIO_PAGES

    while True:  # Boucle pour extraire les propriétés sur chaque page
        properties = extract_single_duproprio_page_thumbnails(driver)
        unique_properties = get_unique_properties(get_airtable_data(LISTINGS_TABLE), properties)
        all_properties.extend(unique_properties)

        if max_pages is not None and current_page >= max_pages:
            break

        try:
            next_page_button = driver.find_element(By.XPATH,
                                                   '/html/body/main/div[2]/div[1]/div/div[3]/div/nav/div[2]/a')
            next_page_button.click()
            wait()
            current_page += 1
        except:
            break

    driver.close()

    return all_properties


def extract_all_duproprio_pages_blind(driver, max_pages) -> List[Dict]:
    wait()
    all_properties = []
    current_page = 1  # Compteur pour suivre le nombre de pages parcourues

    while True:  # Boucle pour extraire les propriétés sur chaque page
        properties = extract_single_duproprio_page_thumbnails(driver)
        all_properties.extend(properties)

        if max_pages is not None and current_page >= max_pages:
            break

        try:
            next_page_button = driver.find_element(By.XPATH,
                                                   '/html/body/main/div[2]/div[1]/div/div[3]/div/nav/div[2]/a')
            next_page_button.click()
            wait()
            current_page += 1
        except:
            break

    driver.close()

    return all_properties


def extract_single_duproprio_page_thumbnails(driver) -> List[Dict]:
    try:
        wait()
        property_elements = driver.find_elements(By.CSS_SELECTOR, 'li.search-results-listings-list__item')
        properties = []

        for element in property_elements:
            property_info = {}  # Dictionnaire pour stocker les informations d'une propriété
            try:
                tag_elements = element.find_elements(By.CSS_SELECTOR, 'div.search-results-listings-list__tags div')
                texts = []  # Initialise une liste pour stocker les textes des éléments

                for tag_element in tag_elements:  # Parcours chaque élément et récupère son texte
                    text = tag_element.text.strip()
                    if text:
                        texts.append(text)

                concatenated_text = ", ".join(texts)
                property_info['Bannière'] = concatenated_text.capitalize()
            except Exception:
                property_info['Bannière'] = ""

            try:
                price_element = element.find_element(By.CSS_SELECTOR,
                                                     'div.search-results-listings-list__item-description__price > h2').text
                price_digits = price_element.replace('\xa0', '').replace('$', '').replace(' ',
                                                                                          '')  # Supprimer les espaces insécables
                property_info['Prix'] = int(price_digits)
            except Exception:
                property_info['Prix'] = 0

            try:
                address_element = element.find_element(By.CSS_SELECTOR,
                                                       'div.search-results-listings-list__item-description__address')
                property_info['Adresse'] = address_element.text.strip()
            except Exception:
                property_info['Adresse'] = ""

            try:
                city_element = element.find_element(By.CSS_SELECTOR,
                                                    'h3.search-results-listings-list__item-description__city > span')
                property_info['Ville'] = city_element.text.strip()
            except Exception:
                property_info['Ville'] = ""

            try:
                url_element = element.find_element(By.CSS_SELECTOR, 'a.search-results-listings-list__item-image-link')
                url = url_element.get_attribute('href')
                property_info['Url'] = url
            except Exception:
                property_info['Url'] = ""

            if property_info['Prix'] != 0:
                properties.append(property_info)
        return properties
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
        return []


def get_duproprio_laval_properties(data: List[Dict]) -> List[Dict]:
    allowed_suburbs = [
        'Chomedey', 'Duvernay', 'Laval-des-Rapides', 'Laval-Ouest',
        'Pont-Viau', 'Ste-Rose', 'Auteuil', 'Fabreville',
        'Îles-Laval', 'Laval-sur-le-Lac', 'Ste-Dorothée',
        'St-François', 'St-Vincent-de-Paul', 'Vimont', 'Laval'
    ]
    laval_properties = []
    for property_info in data:
        if (
                property_info
                and property_info.get('Ville')
                and any(suburb in property_info['Ville'] for suburb in allowed_suburbs)
        ):
            for suburb in allowed_suburbs:
                if suburb in property_info['Ville'] and any(char.isdigit() for char in property_info["Adresse"]):
                    property_info['Ville'] = f"Laval ({suburb})"
                    break
            laval_properties.append(property_info)
    return laval_properties


# Fonctions secondaires du scraper
def get_recent_centris_thumbnails(driver):
    driver.get(CENTRIS)
    time.sleep(0.5)
    centris_enter(driver)
    wait()
    get_cities(VILLES, driver)
    wait()
    get_price_range(driver)
    wait()
    get_land_area(driver)
    wait()
    get_most_recent(driver)
    wait()
    data = extract_all_pages_blind(driver)
    wait()
    get_commercial_listings(driver)
    wait()
    commercial = extract_all_pages_blind(driver)
    for property_info in commercial:
        property_info['Nom'] += " *"
    time.sleep(1)
    full_data = data + commercial
    driver.close()
    return full_data


def get_recent_new_centris_thumbnails(driver):
    driver.get(CENTRIS)
    time.sleep(0.5)
    centris_enter(driver)
    wait()
    get_cities(VILLES, driver)
    wait()
    get_price_range(driver)
    wait()
    get_land_area(driver)
    wait()
    get_most_recent(driver)
    wait()
    data = extract_all_new_pages(driver)
    wait()
    get_commercial_listings(driver)
    wait()
    commercial = extract_all_new_pages(driver)
    for property_info in commercial:
        property_info['Nom'] += " *"
    time.sleep(1)
    full_data = data + commercial
    driver.close()
    return full_data


def get_all_duproprio_thumbnails(driver, max_pages):
    driver.get(DUPROPRIO)
    wait()
    duproprio_enter(driver)
    time.sleep(2)
    data = extract_all_duproprio_pages_blind(driver, max_pages)
    return data


def get_recent_new_duproprio_thumbnails(driver):
    driver.get(DUPROPRIO)
    wait()
    duproprio_enter(driver)
    time.sleep(2)
    data = extract_all_duproprio_pages(driver)
    return data


def get_all_recent_thumbnails(centris_driver, duproprio_driver, max_pages):
    centris_properties = get_recent_centris_thumbnails(centris_driver)
    duproprio_properties = get_all_duproprio_thumbnails(duproprio_driver, max_pages)
    unique_duproprio_properties = [
        duproprio_property
        for duproprio_property in duproprio_properties
        if duproprio_property not in centris_properties
    ]
    all_properties = centris_properties + unique_duproprio_properties
    return all_properties


def get_all_new_recent_thumbnails(centris_driver, duproprio_driver):
    centris_properties = get_recent_new_centris_thumbnails(centris_driver)
    duproprio_properties = get_recent_new_duproprio_thumbnails(duproprio_driver)
    unique_duproprio_properties = [
        duproprio_property
        for duproprio_property in duproprio_properties
        if duproprio_property not in centris_properties
    ]
    all_properties = centris_properties + unique_duproprio_properties
    return all_properties


def update_properties(max_pages):
    unique_properties = get_all_recent_thumbnails(webdriver.Chrome(options=options),
                                                  webdriver.Chrome(options=options), max_pages)
    return unique_properties


def update_new_properties():
    unique_properties = get_all_new_recent_thumbnails(webdriver.Chrome(options=options),
                                                      webdriver.Chrome(options=options))
    if unique_properties:
        full_data = scrape_all_properties(unique_properties, get_duproprio_laval_properties(unique_properties))
    else:
        print("Aucune nouvelle propriété n'a été trouvée.")


def post_to_airtable(data_list: List[Dict], table: str):
    auth_token = "patiRXKAfyeamyMoM.bfd7d533a0dd3da722b676fda42554e93ca568aa4547603c0359c2cb0a5fc990"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

    base_url = "https://api.airtable.com/v0/appiK6NVCpDFrdDv5"

    for idx, record in enumerate(data_list):
        if idx >= 5:
            print("Maximum number of records processed. Exiting loop.")
            break
        response = requests.post(f"{base_url}/{table}", headers=headers, json={"fields": record})
        if response.status_code == 200:
            print(f"Success: Record added to Airtable. Response: {response.json()}")
        else:
            print(
                f"Error: Failed to add record to Airtable. Status code: {response.status_code}. Response: {response.json()}")

        time.sleep(2)  # Attente de 2 secondes entre chaque requête


def get_airtable_data(table: str) -> List[Dict]:
    auth_token = "patiRXKAfyeamyMoM.bfd7d533a0dd3da722b676fda42554e93ca568aa4547603c0359c2cb0a5fc990"
    headers = {
        "Authorization": f"Bearer {auth_token}",
    }
    all_records = []
    offset = None
    url = "https://api.airtable.com/v0/appiK6NVCpDFrdDv5/Listings"
    base_url = url.rsplit('/', 1)[0]

    while True:
        params = {"offset": offset} if offset else {}
        response = requests.get(f"{base_url}/{table}", headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            records = data.get('records', [])
            all_records.extend(record['fields'] for record in records)
            offset = data.get('offset')
            if not offset:
                break
        else:
            print(
                f"Error: Failed to fetch data from Airtable. Status code: {response.status_code}. Response: {response.text}")
            break

    return all_records


def post_new_property(new_properties: List[Dict], watchlist: List[Dict]):
    for prop in new_properties:
        addr = prop.get('Adresse')
        banner = prop.get('Bannière', '')
        modified = False  # Indicateur pour savoir si la bannière a été modifiée
        for watch_prop in watchlist:
            if watch_prop.get('Adresse') == addr:
                watch_banner = watch_prop.get('Bannière', '')
                if banner != watch_banner:
                    prop['Bannière'] = f"*** {banner} ***"
                    modified = True
                break  # Sortir de la boucle dès que la propriété correspondante est trouvée
        if not modified:
            prop['Bannière'] = banner  # Conserver la bannière actuelle si elle n'a pas été modifiée
        post_to_airtable([prop], LISTINGS_TABLE)


def get_unique_properties(all_properties: List[Dict], new_properties: List[Dict]) -> List[Dict]:
    all_properties_addresses = {normalize_address(prop.get('Adresse')) for prop in all_properties}
    unique_properties = []

    for prop in new_properties:
        addr = normalize_address(prop.get('Adresse'))
        if addr and addr not in all_properties_addresses:
            unique_properties.append(prop)
            all_properties_addresses.add(addr)
    print(len(unique_properties))
    return unique_properties


def normalize_address(address: str) -> str:
    # Normalise l'adresse en supprimant les espaces superflus et en mettant en minuscules
    return address.strip().lower() if address else ''


def read_addresses_from_file(filename: str) -> List[Dict[str, str]]:
    all_properties = []
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()  # Supprime les espaces inutiles, y compris les retours à la ligne
            if line.startswith("http") or line.startswith("www"):
                property_dict = {"Url": line}
                all_properties.append(property_dict)
            else:
                property_dict = {"Adresse": line, "Ville": "Laval"}
                all_properties.append(property_dict)
    pprint(all_properties)
    print()
    return all_properties


def convert_to_excel(data: List[Dict], filename: str):
    df = pd.DataFrame(data)  # Crée un DataFrame à partir de la liste de dictionnaires
    df.to_excel(filename, index=False)  # Écrit le DataFrame dans un fichier Excel
    print(f"Fichier {filename} mis-à-jour avec succès")


def convert_to_json(data: List[Dict], filename: str):
    with open(filename, 'w') as f:  # Écrit la liste de dictionnaires dans un fichier JSON
        json.dump(data, f)
    print(f"Fichier {filename} mis-à-jour avec succès")


def read_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)  # Charger le fichier JSON en tant que liste de dictionnaires
            all_keys = []  # Collecter toutes les clés uniques des dictionnaires dans l'ordre
            for d in data:
                all_keys.extend(d.keys())
            all_keys = list(dict.fromkeys(all_keys))

            df = pd.DataFrame(data,
                              columns=all_keys)  # Convertir le dictionnaire en DataFrame en spécifiant les noms de colonnes
            df = df.where(pd.notnull(df), None)  # Remplacer les valeurs nulles par None
        return df
    except FileNotFoundError:
        print(f"Fichier non trouvé : {file_path}")
        return pd.DataFrame()
    except json.JSONDecodeError as e:
        print(f"Erreur lors de la lecture du fichier JSON : {e}")
        return pd.DataFrame()


def export_to_csv(data_list, file_path):
    keys = data_list[0].keys() if data_list else []
    with open(file_path, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data_list)


def dataframe_to_dict_list(df) -> List[Dict]:
    if not isinstance(df, pd.DataFrame):
        raise ValueError("L'entrée doit être un DataFrame pandas.")

    dict_list = df.to_dict(orient='records')  # Convertir le DataFrame en une liste de dictionnaires

    return dict_list


# Fonctions du scraper avec adresses spécifiques
def scrape_one_custom_property(url: str, property_info: Dict):
    options = Options()
    options.add_experimental_option("detach", True)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)
    wait()

    try:
        popup = driver.find_element(By.ID, "didomi-notice-agree-button")
        popup.click()
        wait()
    except Exception:
        pass

    property_info = {
        'Url': url}
    try:
        banner = driver.find_element(By.CSS_SELECTOR, 'div.banner')
        property_info['Bannière'] = banner.text
    except Exception:
        property_info['Bannière'] = ""

    category_element = driver.find_element(By.CSS_SELECTOR, 'span[data-id="PageTitle"]')
    property_info['Nom'] = category_element.text

    number_meta = driver.find_element(By.CSS_SELECTOR, 'span#ListingDisplayId')
    property_info['# Centris'] = number_meta.text

    price_meta = driver.find_element(By.CSS_SELECTOR, 'span#BuyPrice').text
    property_info['Prix'] = int(price_meta.replace(" ", "").replace("$", ""))

    address_element = driver.find_element(By.CSS_SELECTOR, 'h2[itemprop="address"]')
    address_text = address_element.text.strip()

    address_parts = address_text.split(',')
    property_info['Adresse'] = address_parts[0].strip() + ", " + address_parts[
        1].strip()  # Première partie est l'adresse

    if len(address_parts) >= 2:
        city_parts = address_parts[2].strip().split('(')  # Séparer la ville et le quartier
        property_info['Ville'] = city_parts[0].strip()  # La deuxième partie est la ville

    try:
        description = driver.find_element(By.CSS_SELECTOR, 'div[itemprop="description"]').text
        property_info['Description'] = description
    except Exception:
        property_info['Description'] = "N/A"

    carac_containers = driver.find_elements(By.CSS_SELECTOR, 'div.carac-container')

    try:
        year_element = None

        for container in carac_containers:
            title_element = container.find_element(By.CSS_SELECTOR, 'div.carac-title').text

            if title_element == "Année de construction":
                year_element = container.find_element(By.CSS_SELECTOR, 'div.carac-value span').text
                break
        property_info['Année'] = year_element
    except Exception:
        property_info['Année'] = "N/A"

    try:
        area_element = None

        for container in carac_containers:
            # Récupérer le texte du titre
            title_element = container.find_element(By.CSS_SELECTOR, 'div.carac-title').text

            if title_element == "Superficie du terrain":
                area_element = container.find_element(By.CSS_SELECTOR, 'div.carac-value span').text
                break

        # Supprimer les espaces et l'unité de mesure (pc) pour obtenir uniquement le nombre
        area_numeric_str = area_element.replace(" ", "").replace("pc", "")

        property_info['Superficie (pi²)'] = area_numeric_str
    except Exception:
        property_info['Superficie (pi²)'] = "N/A"

    driver.quit()

    return property_info


def scrape_all_custom_properties(properties: List[Dict]):
    all_properties = []
    centris_prop = [property_info for property_info in properties if 'Url' in property_info]
    laval_prop = get_all_custom_laval_properties(properties)

    with ThreadPoolExecutor(max_workers=CENTRIS_MAX_WORKERS) as executor:
        futures = [executor.submit(scrape_one_custom_property, property_info['Url'], property_info) for property_info in
                   centris_prop]

        for future in as_completed(futures):
            try:
                property_data = future.result()
                all_properties.append(property_data)
                if "Laval" not in property_data["Ville"]:
                    post_new_property([property_data], get_airtable_data(WATCHLIST_TABLE))
                elif "Laval" in property_data["Ville"] and all(not char.isdigit() for char in property_data["Adresse"]):
                    post_new_property([property_data], get_airtable_data(WATCHLIST_TABLE))
                else:
                    laval_prop.append(property_data)
            except TimeoutError:
                pass

    # Deuxième étape : Mettre à jour les informations des propriétés de Laval
    with ThreadPoolExecutor(max_workers=INFO_MAX_WORKERS) as executor:
        laval_futures = []
        for property_info in laval_prop:
            address = property_info["Adresse"]
            if any(char.isdigit() for char in property_info.get('Adresse', '')):
                future = executor.submit(scrape_one_laval_property, address, property_info)
                laval_futures.append(future)

        for future in as_completed(laval_futures):
            try:
                laval_property_data = future.result()
                for existing_property_info in all_properties:
                    if existing_property_info.get("Adresse") == laval_property_data.get("Adresse"):
                        existing_property_info.update(laval_property_data)  # Ajoute les informations d’urbanisme
                        post_to_airtable([existing_property_info], LISTINGS_TABLE)
                        break
                else:
                    post_to_airtable([laval_property_data], LISTINGS_TABLE)
            except TimeoutError:
                pass

    return all_properties


def get_all_custom_laval_properties(data: List[Dict]):
    laval_properties = []
    for i in data:
        if i and i.get('Ville') and 'Laval' in i['Ville']:
            laval_properties.append(i)
    return laval_properties


def find_duplicates(data: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen_addresses = {}
    duplicates = []

    for entry in data:
        address = entry.get("Adresse")
        if address:
            if address in seen_addresses:
                duplicates.append(entry)
            else:
                seen_addresses[address] = entry

    return duplicates


def scrape_custom_addresses():
    addresses = read_addresses_from_file(ADDRESSES_FILE)
    full_addresses = scrape_all_custom_properties(addresses)
    return full_addresses


def check_watchlist_in_update_properties(max_pages):
    watchlist = get_airtable_data(WATCHLIST_TABLE)
    properties = update_properties(max_pages)
    gone_properties = get_unique_properties(properties, watchlist)
    get_updated_watchlist_properties(properties, watchlist)
    for item in watchlist:
        if item in gone_properties:
            print(f"La propriété {item['Adresse']} est désormais hors-marché.")


def get_updated_watchlist_properties(properties: List[Dict], watchlist: List[Dict]) -> List[Dict]:
    updated_properties = []
    watchlist_dict = {item['Adresse']: item for item in watchlist}
    seen_addresses = set()

    for prop in properties:
        prop_id = prop['Adresse']
        if prop_id in watchlist_dict:
            if prop.get('Prix') != watchlist_dict[prop_id].get('Prix'):
                if prop_id not in seen_addresses:
                    updated_properties.append(prop)
                    print(f"Le prix de la propriété {prop['Adresse']} a été modifié: ${watchlist_dict[prop_id].get('Prix'):,} -> ${prop.get('Prix'):,}")
                    seen_addresses.add(prop_id)

    return updated_properties


def is_airtable_overflow(data: List[Dict]) -> bool:
    print("\nVérification de l'espace Airtable...")
    listings_length = len(data)
    if listings_length >= 950:
        print(f"\nVotre table Airtable a atteint sa capacité maximale: {listings_length}/1000")
        print("Pour procéder, ne conservez que les 300 enregistrements les plus récents (http://bit.ly/3SU6Jwy)")
        time.sleep(8)
        return True
    elif listings_length >= 850:
        print(f"\nVotre table Airtable approche de sa capacité maximale: {listings_length}/1000")
        print(
            "Pour un fonctionnement optimal, il est recommandé de ne conserver que les 300 enregistrements les plus récents (http://bit.ly/3SU6Jwy)")
        time.sleep(8)
        return False
    else:
        print(f"Enregistrements restants disponibles: {1000 - listings_length}")
        time.sleep(2)
        return False


def main():
    print("-------------------------------------------------")
    print("  Système Automatisé Multi-plateformes (S.A.M.)  ")
    print("-------------------------------------------------")
    time.sleep(1)
    while True:
        user_choice = input(
            f"\n[1] Récupérer les plus récentes propriétés\n[2] Récupérer des propriétés spécifiques\n[3] Vérifier l'état des propriétés sauvegardées\n[q] Quitter \t[h] Help\n-> ")
        if user_choice.lower() == "q":
            print("\nFermeture du programme...")
            break
        elif user_choice.lower() == "h":
            print("\n------------------------")
            print("  Manuel d'utilisateur  ")
            print("------------------------\n")

            print("Option 1:")
            pprint(
                "Récupère les 200 listings résidentiels et commerciaux les plus récents (100 résidentiels, 100 commerciaux) ainsi que les 50 dernières annonces sur DUPROPRIO. Ensuite, elle compare ces listings avec ceux déjà présents dans Airtable et ne conserve que les propriétés uniques. Le programme ajoute ensuite les nouvelles propriétés une par une dans le tableau Airtable.")

            print("\nOption 2:")
            pprint(
                "Lit les lignes du fichier 'adresses.txt' et récupère ensuite toutes les informations nécessaires. Les adresses, les numéros de lot ou URLs doivent être séparés par un retour à la ligne. Tout comme pour l'option 1, le programme demandera de supprimer des enregistrements dans Airtable si la table est saturée.")

            print("\nOption 3:")
            pprint(
                "Vérifie si l'une des propriétés sauvegardées dans la watchlist n'est pas hors-marché ou n'a pas changé de prix. Ce programme requiert de naviguer sur toutes les pages de propriétés pertinentes. Le nombre de pages maximal sur le site DUPROPRIO doit être entré manuellement. Vous pouvez retrouver le nombre total de pages à scraper ici: https://bit.ly/3YQ51jN")

            print("\nInstructions générales:\n")
            pprint(
                "Laissez le programme s'exécuter jusqu'à la fin, notamment pour les données d'urbanisme qui peuvent ne pas être trouvées immédiatement par la barre de recherche.")
            pprint(
                "Il est recommandé de maintenir le curseur de la souris sur la barre de démarrage pour éviter toute interférence avec le programme.")
            pprint(
                "Vous pouvez interrompre l'exécution du programme à tout moment en appuyant sur les touches Ctrl+C et en fermant le terminal.")
            pprint(
                "Il est fortement déconseillé d'ajouter ou de supprimer des colonnes dans les tableaux Airtable et Zapier, afin de garantir le bon déroulement de l'extraction des données.")
            pprint(
                "Les autres manipulations telles que la suppression ou l'ajout de listings, l'application de filtres ou l'ajout de commentaires sont permises.")

            input("\nAppuyez sur [Entrée] pour retourner au menu principal.")
        elif user_choice == "1":
            overflow = is_airtable_overflow(get_airtable_data(LISTINGS_TABLE))
            if overflow is True:
                continue
            else:
                print("\nLancement du programme 1, veuillez patienter...")
                print("(Ctrl+C pour interrompre à tout moment)\n")
                time.sleep(1)
                update_new_properties()
                print("\nNouvelles propriétés récupérées avec succès.")
                time.sleep(5)
                continue
        elif user_choice == "2":
            overflow = is_airtable_overflow(get_airtable_data(LISTINGS_TABLE))
            if overflow is True:
                continue
            else:
                print("\nLancement du programme 2, veuillez patienter...")
                print("(Ctrl+C pour interrompre à tout moment)\n")
                time.sleep(1)
                scrape_custom_addresses()
                print("\nPropriétés spécifiques récupérées avec succès.")
                time.sleep(5)
                continue
        elif user_choice == "3":
            pages_str = input("Entrez le nombre total de pages DUPROPRIO à vérifier https://bit.ly/3YQ51jN : ")
            if pages_str.isdigit():
                pages_int = int(pages_str)
                print("\nLancement du programme 3, veuillez patienter...")
                print("(Ctrl+C pour interrompre à tout moment)\n")
                time.sleep(1)
                check_watchlist_in_update_properties(pages_int)
                time.sleep(5)
                continue
            else:
                print("\nOption invalide.")
                time.sleep(1)
                continue
        else:
            print("\nOption invalide.")
            time.sleep(1)
            continue


if __name__ == '__main__':
    main()
