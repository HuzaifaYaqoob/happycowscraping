# Import statements
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import csv
import os
from datetime import datetime
import requests
import cv2
import numpy as np
from threading import Thread

# Directory for images
minutes = {}

BLOCKED = []
# page_count = 100
# total_listing = 3

import sys
sys.path.insert(0,'/usr/lib/chromium-browser/chromedriver')


def write_log(message, end='\n'):
    with open('/root/log.txt', 'a') as log_file:
        log_file.write(str(message) + end)

# Initialize Chrome in Google Colab
def initialize_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode in Colab
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f"--user-agent={UserAgent().random}")
    chrome_options.add_argument("--remote-debugging-port=9222")

    # Set path to Chrome binary in Google Colab
    chrome_options.binary_location = "/usr/bin/chromium-browser"

    # Disable images by setting Chrome preferences
    prefs = {
        "profile.managed_default_content_settings.images": 2  # 2 means images are disabled
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # Initialize ChromeDriver with options
    driver = webdriver.Chrome(options=chrome_options)

    write_log('Initialized driver...')
    return driver

def scrape_links(driver, page_url):
    driver.delete_all_cookies()
    write_log(page_url)
    driver.get(page_url)
    links = []
    page = 1
    find = True
    while find:
        # if page > page_count:
        #     find = False
        #     break
        try:
            WebDriverWait(driver, 40).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'thumbnail-link'))
            )
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            for l_i, link in enumerate(soup.find_all('a', class_='thumbnail-link')):
                if l_i > 20:
                    break
                relative_url = link.get('href')
                full_url = 'https://www.happycow.net' + relative_url
                links.append(full_url)

            write_log(f'Total : {len(links)}')
            write_log(f'Next page : {page + 1}')
            next_page = soup.select_one(f'a.pagination-link[data-page="{page + 1}"]')
            if not next_page:
                find = False
                continue
            next_element = driver.find_element(By.CSS_SELECTOR, f'a.pagination-link[data-page="{page + 1}"]')
            if next_element:
                next_element.click()
                driver.implicitly_wait(30)
                write_log('Clicked')
                page = page + 1
            else:
                find = False
        except Exception as e:
            write_log(f"Error navigating page {page}: {driver.title}")
            BLOCKED.append(page_url)
            find = False
            page += 1  # Continue to the next page if an error occurs

    return links

# Define get_data_from_link function as before
def get_data_from_link(driver, url):
    driver.get(url)
    # if 'Unusual Traffic' in driver.title:
    #   raise Exception('Sys : Unusual Traffic..........')
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'header-title'))
    )
    write_log(' : (Title) : ', end=' ')
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'hours-list'))
        )
    except:
        write_log('Could Not Fetched Hours', end=' ')
        pass

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    data = {
        "Accept Credit" : 'N/A',
        "Outdoor seating" : 'N/A',
        "Friend of HappyCow" : 'False',
        "Pricing" : 'N/A',
        "Top Rated" : 'N/A',
        "Open Hours" : 'N/A',
        "Facebook" : 'N/A',
        "Instagram" : 'N/A',
        "Last Updated" : 'N/A',
        "Nearby Listing" : 'N/A',
        "Added By" : 'N/A',
        "Tags" : 'N/A',
        "Categories" : 'N/A',
        "First Featured Review" : 'N/A',
    }

    # Name
    title = soup.find(class_='header-title')
    data['Name'] = title.get_text(strip=True) if title else 'N/A'

    # Tags
    tags_list = []
    tags = soup.select('div.venue-info div')
    if len(tags) > 0:
        tags_list.extend([tag.get_text(strip=True) for tag in tags[:-1] if tag])
    data['Tags'] = ','.join(tags_list)

    frnd_tag = soup.find(attrs={"title": "Friend of HappyCow"})
    if frnd_tag:
        data['Friend of HappyCow'] = 'True'


    # Top Rated
    element = soup.find(attrs={"data-observe-type" : "listing-top-rated"})
    if element:
        data['Top Rated'] = element.get_text(strip=True)

    # Favourite Count
    element = soup.find(class_='favorite-badge')
    data['Favourite Count'] = element.get_text(strip=True) if element else 'N/A'

    # Rating
    element = soup.find(attrs={"itemprop": "ratingValue"})
    data['Rating'] = element.get('content') if element else 'N/A'

    # Total Reviews
    element = soup.find(class_='rating-reviews')
    total_rating = element.get_text(strip=True) if element else 'N/A'
    data['Total Reviews'] = total_rating.replace('(', '').replace(')', '')

    # Outdoor seating
    element = soup.find(attrs={"title" : "Outdoor seating"})
    if element:
        data['Outdoor seating'] = element.get_text(strip=True)

     # Accept Credit
    element = soup.find(attrs={"title" : "Accepts credit cards"})
    if element:
        data['Accept Credit'] = element.get_text(strip=True)

     # Nearby Listing a tags
    elements = soup.find_all(attrs={"data-analytics" : "nearby-listings-venue"})
    if len(elements) > 0:
        hrefs = []
        for element in elements:
            hrf = f'https://www.happycow.net{element.get("href")}'
            if element.name == 'a' and hrf and hrf not in hrefs:
                hrefs.append(hrf)
        data['Nearby Listing'] = ", ".join(hrefs)


    # Listing Hours
    element = soup.find(class_='listing-hours')
    data['Listing Hours'] = " ".join(element.stripped_strings) if element else 'N/A'


    all_listing_hours = soup.select('.hours-list')
    if len(all_listing_hours) > 0:
        hours_list = all_listing_hours[0]
        hours_list_li = hours_list.select('li')
        hlist_strs = []
        for li in hours_list_li:
            hlist_strs.append(", ".join(li.stripped_strings))
        data['Open Hours'] = "\n".join(hlist_strs)



    # Pricing
    pricing = [soup.find(attrs={"title": "Inexpensive"}), soup.find(attrs={"title": "Moderate"}), soup.find(attrs={"title": "Expensive"})]
    pricing = ['$' for i in pricing if i and i.select_one('svg.text-yellow-500')]
    if len (pricing) > 0:
        data['Pricing'] = ' '.join(pricing)

    # Address
    element = soup.find(attrs={"itemprop": "address"})
    data['Address'] = element.get_text(strip=True) if element else 'N/A'

    # Phone Number
    element = soup.find(attrs={"itemprop": "telephone"})
    data['Phone Number'] = element.get_text(strip=True) if element else 'N/A'

    # Last Updated
    element = soup.find(class_='btn-update-info')
    if element:
        element_p = element.parent
        if element_p:
            element = element_p.find('span')
            data['Last Updated'] = element.get_text(strip=True) if element else 'N/A'

        element = element_p.parent
        if element.name == 'li':
            element = element.parent
            try:
                elements = element.select('li')[1]
            except:
                pass
            else:
                element = element.select_one('div')
                data['Added By'] = element.get_text(strip=True) if element else 'N/A'

    # Website
    element = soup.find('a', attrs={"data-analytics": "default-website"})
    data['Website'] = element.get('href') if element else 'N/A'

    # First Featured Review
    reviews = soup.select('div#reviews .user-review-text')
    if len(reviews) > 0:
        data['First Featured Review'] = reviews[0].get_text(strip=True)


    # Description
    element = soup.find('p', class_='venue-description')
    data['Description'] = element.get_text(strip=True) if element else 'N/A'

    element = soup.find_all('a', class_='venue-list-image-link')
    images = [img.get('href') for img in element]

    # Total Images
    data['Total Images'] = len(images) if images else 0

    # Images
    data['Images'] = ', '.join(images) if images else 'N/A'


    # Categories
    cat_list = []
    imgs_listing = soup.select_one('#listing-images')
    if imgs_listing:
        imgs_parent = imgs_listing.parent
        ul = imgs_parent.select_one('ul')
        if ul:
            category = ul.select('li')[-1]
            if category:
                cat_divs = category.select('div')
                cat_list.extend([i.select_one('span').get_text(strip=True) for i in cat_divs if i.select_one('span')])
                data['Categories'] = ', '.join(list(set(cat_list)))

    # URL
    data['URL'] = url
    data['ID'] = url.split("-")[-1]

    a_links = soup.select('div.map-info-desktop a')
    if a_links:
        for link_element in a_links:
            # href
            link_href = link_element.get('href')
            if not link_href:
                continue
            if 'facebook.com' in link_href:
                # Facebook
                data['Facebook'] = link_href
            elif 'instagram.com' in link_href:
                # Instagram
                data['Instagram'] = link_href
    return data


print_length = 85
DONE_CITIES = []
# Main function
def main():

    # Read encoded city URLs from a CSV file
    new_map_cities_links = []
    already_scraped_cities = []
    already_scraped_rest = []
    with open('/root/scraped_data.csv', 'r') as already_scraped_file:
        reader = list(csv.DictReader(already_scraped_file))
        write_log(f'Total Fetched till Yet : {len(reader)}')
        for row in reader:
            already_scraped_rest.append(row['URL'])
            if row.get('City Map Url', None) and (row.get('City Map Url',) not in already_scraped_cities ):
                # or reader[-1]['City Map Url'] == row.get('City Map Url',)
                already_scraped_cities.append(row['City Map Url'])

    write_log('Unique')
    write_log(len(list(set(already_scraped_rest))))
    write_log('=' * 50)
    write_log("already Scrapped Cities")
    write_log('=' * 50)

    CITY_DICT = {}
    with open('/root/encoded_cities_8.csv', 'r') as cities_file:
        reader = csv.DictReader(cities_file)
        for row in reader:
            if row['EncodedURL'] not in already_scraped_cities:
                CityName = row['Name']
                city_name, links_count = CityName.split(', ')
                links_count = links_count.replace('(', '').replace(')', '')
                CITY_DICT[row['EncodedURL']] = {
                    **row,
                    'Count' : links_count
                }
                new_map_cities_links.append(row['EncodedURL'])


    write_log(len(new_map_cities_links))
    driver = initialize_driver()
    for map_url in new_map_cities_links:
        all_links = []
        if map_url in BLOCKED:
            continue
        BLOCKED.append(map_url)
        try:
            links = scrape_links(driver, map_url)
            city_obj = CITY_DICT.get(map_url, {}) or {}
            links = [{**city_obj, 'URL' : l, 'City Map Url' : map_url} for l in links]
            all_links.extend(links)
        except Exception as e:
            write_log(f"======================================== : Error scraping page: {e}")
        else:

            write_log(f'Total found Links {len(all_links)}')
            unique_links = []
            unique_links_urls = []
            if len(all_links) == 0:
                BLOCKED.append(map_url)
                continue
            for p_l in all_links:
                if p_l['URL'] not in unique_links_urls:
                    unique_links.append(p_l)
                    unique_links_urls.append(p_l['URL'])

            write_log(f'Unique Links {len(unique_links)}')

            with open('/root/scraped_data.csv', 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    "ID", "Name", "Tags", "Categories", "Friend of HappyCow", "Pricing", "Top Rated", "Rating",
                    "Total Reviews", "Favourite Count", "Accept Credit", "Outdoor seating", "Listing Hours",
                    "Open Hours", "Total Images", "Phone Number", "Last Updated", "Added By", "Address",
                    "First Featured Review", "Website", "Description", "Images", "URL", "Facebook",
                    "Instagram", "Nearby Listing", "City Map Url","CityUrl","Expected Count"
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                for index, link in enumerate(unique_links):
                    # if index > total_listing:
                    #     break
                    if link['URL'] in already_scraped_rest:
                        write_log(f'Continue..... {link["URL"]}')
                        continue
                    cm = datetime.now().strftime('%M')
                    minutes[cm] = minutes.get(cm, 0) + 1
                    # if index > 0 and index % 10 == 0:
                    #     driver.quit()
                    #     write_log("Sleeping for 10 seconds... Count 10")
                    #     time.sleep(10)
                    #     driver = initialize_driver()

                    try:
                        rm = print_length - len(link["URL"])
                        write_log(f'Fetching ::: {link["URL"]}', end=f'{" " * rm}{index}/{len(unique_links)} ====>>>> ')

                        data = get_data_from_link(driver, link['URL'])
                        data['City Map Url'] = link['City Map Url']
                        data['CityUrl'] = link['URL']
                        data['Expected Count'] = link['Count']
                        writer.writerow(data)
                        write_log(f"\tData Saved")
                    except Exception as e:
                        # write_log(f"Error fetching data for {link['City Map Url']}: {e}")
                        unique_links.append(link)
                        write_log(f"\t{driver.title}")
                        # write_log(driver.page_source)
                        # driver.quit()
                        # write_log("Sleeping for 1 minutes due to error")
                        # time.sleep(60 * 1)
                        # driver = initialize_driver()
                driver.quit()


            break
    write_log("Done.......... Finished")