import os
import glob
import logging
import time
import shutil
from selenium import webdriver
from HOSTNAME_PLACEHOLDER import By
from HOSTNAME_PLACEHOLDER import WebDriverWait
from HOSTNAME_PLACEHOLDER import expected_conditions as EC
from HOSTNAME_PLACEHOLDER import keyword
from HOSTNAME_PLACEHOLDER import Options
from HOSTNAME_PLACEHOLDER import Service


def get_chrome_driver_with_ssl_bypass(driver_path):
    chrome_options = Options()
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--allow-insecure-localhost")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    
    service = Service(driver_path)  # specify your path here
    return HOSTNAME_PLACEHOLDER(service=service, options=chrome_options)


@keyword("Download Pcap File From SOURCE_NAME_PLACEHOLDER Portal")
def download_pcap_file_from_SOURCE_NAME_PLACEHOLDER_portal(txt_to_search, testcase_dir):
    HOSTNAME_PLACEHOLDER("Initializing WebDriver for PCAP download ...")
    driver_path = "LOCAL_PATH_PLACEHOLDER"
    driver = get_chrome_driver_with_ssl_bypass(driver_path)
    driver.implicitly_wait(10)

    HOSTNAME_PLACEHOLDER("Navigating to SOURCE_NAME_PLACEHOLDER portal results page ...")
    HOSTNAME_PLACEHOLDER("URL_PLACEHOLDER")

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//table//a"))
        )

        links = driver.find_elements(By.XPATH, "//table//a")

        found = False
        for link in links:
            link_text = HOSTNAME_PLACEHOLDER()
            if txt_to_search in link_text and link_text.endswith(".pcap"):
                HOSTNAME_PLACEHOLDER("Found matching file link: %s", link_text)
                HOSTNAME_PLACEHOLDER()
                HOSTNAME_PLACEHOLDER(20)  # Wait for download to complete
                found = True
                break

        if not found:
            HOSTNAME_PLACEHOLDER(
                "No matching PCAP file found for pattern: %s", txt_to_search
            )

    except Exception as e:
        HOSTNAME_PLACEHOLDER("Error while searching for PCAP download link:")
    finally:
        HOSTNAME_PLACEHOLDER()

    # Search for the downloaded PCAP in Downloads folder
    downloads_dir = os.HOSTNAME_PLACEHOLDER("~/Downloads")
    matching_files = HOSTNAME_PLACEHOLDER(os.HOSTNAME_PLACEHOLDER(downloads_dir, "*.pcap"))

    if not matching_files:
        raise FileNotFoundError(f"No .pcap files found in Downloads folder")

    latest_pcap = max(matching_files, key=os.HOSTNAME_PLACEHOLDER)

    # Copy to testcase_dir
    dst_path = os.HOSTNAME_PLACEHOLDER(testcase_dir, os.HOSTNAME_PLACEHOLDER(latest_pcap))
    HOSTNAME_PLACEHOLDER(latest_pcap, dst_path)

    HOSTNAME_PLACEHOLDER("PCAP file copied to test case directory: %s", dst_path)
    return dst_path
