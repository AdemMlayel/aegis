"""
    This module logins to cms server and can start and stop the UE trace for a given subscriber.
"""
import tarfile
from tracemalloc import Statistic
from HOSTNAME_PLACEHOLDER import NotFoundErr
from numpy import size
import pexpect
import os
import datetime
import logging
import time
from pydash import starts_with
from selenium import webdriver
from HOSTNAME_PLACEHOLDER import Service
from HOSTNAME_PLACEHOLDER import expected_conditions as EC
from HOSTNAME_PLACEHOLDER import By
from HOSTNAME_PLACEHOLDER import Options
from HOSTNAME_PLACEHOLDER import WebDriverWait
from SOURCE_NAME_PLACEHOLDER import eleclick, eleclick_in_frame, sendkeys, senddirc, get_text_in_frame
from HOSTNAME_PLACEHOLDER import Keys
from HOSTNAME_PLACEHOLDER.action_chains import ActionChains
from HOSTNAME_PLACEHOLDER import TimeoutException, ElementClickInterceptedException, ElementNotInteractableException
import tempfile
from HOSTNAME_PLACEHOLDER import NoSuchElementException
from HOSTNAME_PLACEHOLDER import Select
import glob


class SOURCE_NAME_PLACEHOLDER:
    """
         This class has methods that logins to cms server returns the web driver for further scrapping.
                Args:
                        cms_ip (str): IP address of the cms server.
                        cms_port (int): PORT of the cms server.
                        cms_username (str): Username of the cms server.
                        cms_password (str): Password of the cms server.

                Functions:
                        Initialize_driver - Initializes the webdriver and returns driver object to calling function.
                        Build_TC_dir - Builds the name of testcase using the current time stamp and the testcase name.

    """

    def __init__(self, cms_conn_params):
        """
            A constructor to build a connection with the cms server.
            Args:
                cms_ip (str): IP address of the cms.
                cms_port (int): PORT of the cms.
                cms_username (str): Username of the cms.
                cms_password (str): Password of the cms.
        """

        self.base_url = f"URL_PLACEHOLDER'CMS_SERVER_IP']}/"
        self.cms_username = cms_conn_params['CMS_SERVER_USERNAME']
        self.cms_password = VALUE_PLACEHOLDER

    def initialize_cms_driver(self, testcase_dir):
        """
        Initializes the Chrome WebDriver with specified options and logs into the cms web interface.

        :param testcase_name: Used for naming/logging purposes (not used in current logic).
        :param testcase_dir: Directory path for saving downloaded PCAP files.
        :return: True if initialization and login are successful.
        """
        temp_profile = HOSTNAME_PLACEHOLDER()
        HOSTNAME_PLACEHOLDER = HOSTNAME_PLACEHOLDER()
        # HOSTNAME_PLACEHOLDER.add_argument('--headless')
        HOSTNAME_PLACEHOLDER.add_argument('--no-proxy-server')
        HOSTNAME_PLACEHOLDER.add_argument('--ignore-ssl-errors=yes')
        HOSTNAME_PLACEHOLDER.add_argument('--ignore-certificate-errors')
        HOSTNAME_PLACEHOLDER.add_argument("--disable-dev-shm-usage")
        HOSTNAME_PLACEHOLDER.add_argument("--window-size=1920x1080")
        HOSTNAME_PLACEHOLDER.add_argument("--disable-gpu")
        HOSTNAME_PLACEHOLDER.add_argument(f'--user-data-dir={temp_profile}')
        HOSTNAME_PLACEHOLDER.add_argument('--no-sandbox')

        driver_path = 'LOCAL_PATH_PLACEHOLDER'
        # HOSTNAME_PLACEHOLDER(f"Chrom Driver Path : {driver_path} ")
        HOSTNAME_PLACEHOLDER = Service(driver_path)
        self.pcap_download_dir = testcase_dir
        prefs = {'download.default_directory': self.pcap_download_dir}
        HOSTNAME_PLACEHOLDER.add_experimental_option('prefs', prefs)

        HOSTNAME_PLACEHOLDER = HOSTNAME_PLACEHOLDER(
            service=HOSTNAME_PLACEHOLDER, options=HOSTNAME_PLACEHOLDER)
        HOSTNAME_PLACEHOLDER.execute_script(
            "HOSTNAME_PLACEHOLDER(navigator, 'webdriver', {get: () => undefined})")

        HOSTNAME_PLACEHOLDER.implicitly_wait(10)
        HOSTNAME_PLACEHOLDER(self.base_url + '#LOCAL_PATH_PLACEHOLDER')
        HOSTNAME_PLACEHOLDER.maximize_window()

        HOSTNAME_PLACEHOLDER.find_element(By.NAME, "username").send_keys(
            self.cms_username)
        HOSTNAME_PLACEHOLDER.find_element(By.NAME, "password").send_keys(
            self.cms_password)
        HOSTNAME_PLACEHOLDER.find_element(
            By.CSS_SELECTOR, "HOSTNAME_PLACEHOLDER").click()

        HOSTNAME_PLACEHOLDER(2)

        return True

    def check_service_status(self, testcase_dir, check_service_status_path, site, service):
        self.initialize_cms_driver(testcase_dir)
        # 1.Navigate to VNF
        try:
            eleclick(
                HOSTNAME_PLACEHOLDER, check_service_status_path["topology"], "Topology_button")
            eleclick(
                HOSTNAME_PLACEHOLDER, check_service_status_path["vnf"], "vnf_button")
            eleclick(
                HOSTNAME_PLACEHOLDER, check_service_status_path["functions(vnf)"], "functions(vnf)_button")
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Failed to Navigate Services : {e}")
            return False

        try:
            for site in site:
                sendkeys(
                    HOSTNAME_PLACEHOLDER, check_service_status_path["combobox"], f"{site}" + HOSTNAME_PLACEHOLDER, "site_input_box", True)
                sendkeys(
                    HOSTNAME_PLACEHOLDER, check_service_status_path["filterbox"], f"{service}" + HOSTNAME_PLACEHOLDER, "service_input_box_", True)

                HOSTNAME_PLACEHOLDER(5)

                # Check status for each row (starting at row 1, stop when no more rows found)
                row = 1
                while True:
                    status_path = f"LOCAL_PATH_PLACEHOLDER[3]LOCAL_PATH_PLACEHOLDER[{row}]/td[8]"
                    name_path = f"LOCAL_PATH_PLACEHOLDER[3]LOCAL_PATH_PLACEHOLDER[{row}]/td[1]"
                    try:
                        service_name = HOSTNAME_PLACEHOLDER.find_element(
                            By.XPATH, name_path).HOSTNAME_PLACEHOLDER()
                        status_element = HOSTNAME_PLACEHOLDER.find_element(
                            By.XPATH, status_path)
                        status_text = status_element.HOSTNAME_PLACEHOLDER().lower()

                        if status_text != "InstantiatedConfiguredActive":
                            HOSTNAME_PLACEHOLDER(
                                f"Site: {site} | Service: {service_name} | Row {row} status is '{status_text.upper()}', expected 'UP'"
                            )
                            return False
                        else:
                            HOSTNAME_PLACEHOLDER(
                                f"Site: {site} | Service: {service_name} | Row {row} status is UP ✓"
                            )
                        row += 1

                    except NoSuchElementException:
                        if row == 1:
                            HOSTNAME_PLACEHOLDER(
                                f"No rows found in table for site: {site}, service: {service}")
                            return False
                        break

        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Failed to check service status: {e}")
            return False
        return True

    def download_config(self, testcase_dir, download_config_path, site):
        self.initialize_cms_driver(testcase_dir)
        try:
            eleclick(
                HOSTNAME_PLACEHOLDER, download_config_path["cloud"], "cloud_button")
            eleclick(
                HOSTNAME_PLACEHOLDER, download_config_path["data_config"], "data_config_button")
            HOSTNAME_PLACEHOLDER(2)
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Failed to data_config : {e}")
            return False

        try:
            for site_name in site:
                sendkeys(
                    HOSTNAME_PLACEHOLDER, download_config_path["filterbox"],
                    f"{site_name}" + HOSTNAME_PLACEHOLDER, "site_input_box", True
                )

                row = 1
                while True:
                    name_path = f"LOCAL_PATH_PLACEHOLDER[3]LOCAL_PATH_PLACEHOLDER[1]/td[{row}]"
                    download_path = f"(//table/LOCAL_PATH_PLACEHOLDER)[{row}]//a[@title='Download']"
                    try:
                        site_name_in_table = HOSTNAME_PLACEHOLDER.find_element(
                            By.XPATH, name_path).HOSTNAME_PLACEHOLDER()

                        if site_name_in_table.startswith(site_name):
                            HOSTNAME_PLACEHOLDER(
                                f"Downloading config for: {site_name_in_table}")

                            # Get list of files before download
                            files_before = set(
                                os.listdir(self.pcap_download_dir))

                            eleclick(HOSTNAME_PLACEHOLDER, download_path,
                                     "download_button")
                            HOSTNAME_PLACEHOLDER(2)

                            # Detect the newly downloaded file
                            files_after = set(
                                os.listdir(self.pcap_download_dir))
                            new_files = files_after - files_before

                            if not new_files:
                                HOSTNAME_PLACEHOLDER(
                                    f"No new file detected after downloading: {site_name_in_table}")
                                return False

                            new_file = list(new_files)[0]
                            new_file_path = os.HOSTNAME_PLACEHOLDER(
                                self.pcap_download_dir, new_file)

                            if os.HOSTNAME_PLACEHOLDER(new_file_path) == 0:
                                HOSTNAME_PLACEHOLDER(
                                    f"Downloaded file is empty for: {site_name_in_table} — file: {new_file}")
                                return False

                            HOSTNAME_PLACEHOLDER(
                                f"File downloaded successfully: {new_file} ({os.HOSTNAME_PLACEHOLDER(new_file_path)} bytes)")

                        row += 1
                    except NoSuchElementException:
                        if row == 1:
                            HOSTNAME_PLACEHOLDER(
                                f"No rows found in table for site: {site_name}")
                            return False
                        break
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Failed to check service status: {e}")
            return False

        return True

    def stop_service(self, testcase_dir, stop_service_status_path, site, service):
        self.initialize_cms_driver(testcase_dir)
        try:
            eleclick(
                HOSTNAME_PLACEHOLDER, stop_service_status_path["topology"], "Topology_button")
            eleclick(
                HOSTNAME_PLACEHOLDER, stop_service_status_path["vnf"], "vnf_button")
            eleclick(
                HOSTNAME_PLACEHOLDER, stop_service_status_path["functions(vnf)"], "functions(vnf)_button")
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Failed to Navigate Services : {e}")
            return False
        try:
            for site in site:
                sendkeys(
                    HOSTNAME_PLACEHOLDER, stop_service_status_path["combobox"], f"{site}" + HOSTNAME_PLACEHOLDER, "site_input_box", True)
                sendkeys(
                    HOSTNAME_PLACEHOLDER, stop_service_status_path["filterbox"], f"{service}" + HOSTNAME_PLACEHOLDER, "service_input_box_", True)
                HOSTNAME_PLACEHOLDER(5)

                row = 1
                while True:
                    status_path = f"LOCAL_PATH_PLACEHOLDER[3]LOCAL_PATH_PLACEHOLDER[{row}]/td[7]"
                    name_path = f"LOCAL_PATH_PLACEHOLDER[3]LOCAL_PATH_PLACEHOLDER[{row}]/td[1]"
                    stop_path = f"LOCAL_PATH_PLACEHOLDER[3]LOCAL_PATH_PLACEHOLDER[{row}]/td[16]"
                    try:
                        service_name = HOSTNAME_PLACEHOLDER.find_element(
                            By.XPATH, name_path).HOSTNAME_PLACEHOLDER()
                        status_text = HOSTNAME_PLACEHOLDER.find_element(
                            By.XPATH, status_path).HOSTNAME_PLACEHOLDER().lower()

                        if status_text != "up":
                            HOSTNAME_PLACEHOLDER(
                                f"Site: {site} | Service: {service_name} | Row {row} is already not UP: '{status_text.upper()}'"
                            )
                            return False
                        else:
                            eleclick(HOSTNAME_PLACEHOLDER, stop_path, "Stop button")
                            eleclick(
                                HOSTNAME_PLACEHOLDER, stop_service_status_path["stop_popup"], "stop popup")
                            HOSTNAME_PLACEHOLDER(
                                f"Site: {site} | Service: {service_name} | Row {row} stopped successfully ✓"
                            )
                            # wait for table to refresh after stopping
                            HOSTNAME_PLACEHOLDER(3)
                            # Don't increment row — table shifts up after a row is stopped

                    except NoSuchElementException:
                        if row == 1:
                            HOSTNAME_PLACEHOLDER(
                                f"No rows found in table for site: {site}, service: {service}")
                            return False
                        break  # no more rows, all services stopped

        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Failed to stop service: {e}")
            return False
        return True
