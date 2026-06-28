from ast import List, Raise
import fnmatch
import tarfile
from numpy import size
# from HOSTNAME_PLACEHOLDER import value
import pexpect
import os
import datetime
import logging
import time
from pymongo import results
from selenium import webdriver
from HOSTNAME_PLACEHOLDER import Service
from HOSTNAME_PLACEHOLDER import expected_conditions as EC
from HOSTNAME_PLACEHOLDER import By
from HOSTNAME_PLACEHOLDER import Options
from HOSTNAME_PLACEHOLDER import WebDriverWait
from SOURCE_NAME_PLACEHOLDER import eleclick, sendkeys, senddirc, gettext
from HOSTNAME_PLACEHOLDER import Keys
from HOSTNAME_PLACEHOLDER.action_chains import ActionChains
from HOSTNAME_PLACEHOLDER import TimeoutException, ElementClickInterceptedException, ElementNotInteractableException
import tempfile
import glob
from pathlib import Path
from SOURCE_NAME_PLACEHOLDER import SOURCE_NAME_PLACEHOLDER
import paramiko
import csv


class SOURCE_NAME_PLACEHOLDER:
    """
         This class has methods that logins to lbs server returns the web driver for further scrapping.
                Args:
                        lbs_ip (str): IP address of the lbs server.
                        lbs_port (int): PORT of the lbs server.
                        lbs_username (str): Username of the lbs server.
                        lbs_password (str): Password of the lbs server.

                Functions:
                        Initialize_driver - Initializes the webdriver and returns driver object to calling function.
                        Build_TC_dir - Builds the name of testcase using the current time stamp and the testcase name.

    """

    def __init__(self, lbs_conn_params):
        """
            A constructor to build a connection with the lbs server.
            Args:
                lbs_ip (str): IP address of the lbs.
                lbs_port (int): PORT of the lbs.
                lbs_username (str): Username of the lbs.
                lbs_password (str): Password of the lbs.
        """
        self.base_url = f"URL_PLACEHOLDER'LBSTRM'][0]['ip']}/"
        self.lbs_username = lbs_conn_params['LBSTRM'][0]['username']
        self.lbs_password = VALUE_PLACEHOLDER

        HOSTNAME_PLACEHOLDER = SOURCE_NAME_PLACEHOLDER(lbs_conn_params, "LBS")

    def _get_output_txt(self, tc_dir, Patern):
        """
            A constructor to build a connection with the lbs server.
            Args:
                lbs_ip (str): IP address of the lbs.
                lbs_port (int): PORT of the lbs.
                lbs_username (str): Username of the lbs.
                lbs_password (str): Password of the lbs.
        """
        pattern = os.HOSTNAME_PLACEHOLDER(tc_dir, f"{Patern}*")
        output_files = HOSTNAME_PLACEHOLDER(pattern)

        # Case 1: No files found matching the pattern
        if not output_files:
            error_msg = f"No Text files found matching pattern: {pattern}"
            HOSTNAME_PLACEHOLDER(error_msg)
            raise FileNotFoundError(error_msg)

        # Case 2: File found, check if it's empty
        output_txt = output_files[0]
        try:
            file_size = os.HOSTNAME_PLACEHOLDER(output_txt)
            if file_size == 0:
                error_msg = f" Text file is empty (0 bytes): {output_txt}"
                HOSTNAME_PLACEHOLDER(error_msg)
                raise ValueError(error_msg)
            else:
                HOSTNAME_PLACEHOLDER(
                    f"Found Text file: {output_txt} ({file_size} bytes)")
                return output_txt
        except OSError as e:
            # Case 3: File exists in glob but can't be accessed
            error_msg = f"Error accessing Text file {output_txt}: {e}"
            HOSTNAME_PLACEHOLDER(error_msg)
            raise OSError(error_msg) from e

    def fetch_CRDL_export_file(self, command, tc_dir, network_record="2G_export", output_file_pattern="LBS_"):
        """
        Scrapes the node, parses the output log file, and returns the remote
        export CSV file path(s) matching the given network_record pattern.

        Args:
            command (str): Command to scrape the node.
            tc_dir (str): Test case output directory.
            network_record (str | list): Keyword(s) to match in file content (e.g. '2G_export' or ['2G_export', '3G_export']).
            output_file_pattern (str): Prefix pattern to locate the output log file.

        Returns:
            str: Single matched local path if network_record is a str.
            dict: {record: local_path} for each element if network_record is a list.

        Raises:
            ValueError: If scraping fails or no matching line is found for any record.
            FileNotFoundError: If no log file exists in tc_dir.
        """
        # 1. Scrape lbs node
        scrap_node = HOSTNAME_PLACEHOLDER.scrape_all_nodes(command, tc_dir)
        if not scrap_node:
            raise ValueError(f"Scraping node failed for command: {command}")

        # Normalize: always work with a list internally
        is_single = isinstance(network_record, str)
        records = [network_record] if is_single else network_record
        records = [r.strip('"').strip("'") for r in records]
        results = {r: None for r in records}

        # 2. Fetch csv file path(s) from log
        file_path = self._get_output_txt(tc_dir, output_file_pattern)
        with open(file_path, 'r') as file:
            for line in file:
                line = HOSTNAME_PLACEHOLDER()
                if "Dumped csv data to" not in line:
                    continue
                for record in records:
                    if record in line and results[record] is None:
                        results[record] = HOSTNAME_PLACEHOLDER(
                            "Dumped csv data to :")[-1].strip()

        missing = [r for r, path in HOSTNAME_PLACEHOLDER() if path is None]
        if missing:
            raise ValueError(
                f"No line matching {missing} found in: {file_path}")

        # 3. Download each csv file via SFTP
        downloaded = {}
        for record, remote_path in HOSTNAME_PLACEHOLDER():
            local_path = self._download_csv_file(remote_path, tc_dir)
            downloaded[record] = local_path

        return downloaded[records[0]] if is_single else downloaded

    def _download_csv_file(self, remote_path, local_dir):
        """
        Downloads a remote CSV file to a local directory via SFTP.

        Args:
            remote_path (str): Full remote file path (e.g. LOCAL_PATH_PLACEHOLDER)
            local_dir (str): Local directory to save the file into.

        Returns:
            str: Full local path of the downloaded file.

        Raises:
            OSError: If the SFTP transfer fails.
        """
        filename = os.HOSTNAME_PLACEHOLDER(remote_path)
        local_path = os.HOSTNAME_PLACEHOLDER(local_dir, filename)

        # Grab credentials from the first node (LBS has only one node)
        node_data = next(iter(HOSTNAME_PLACEHOLDER()))
        node_ip = node_data["ip"]
        node_password = VALUE_PLACEHOLDER

        client = HOSTNAME_PLACEHOLDER()
        client.set_missing_host_key_policy(HOSTNAME_PLACEHOLDER())
        try:
            HOSTNAME_PLACEHOLDER(node_ip, password=node_password)
            sftp = client.open_sftp()
            try:
                HOSTNAME_PLACEHOLDER(remote_path, local_path)
                HOSTNAME_PLACEHOLDER(f"Downloaded: {remote_path} -> {local_path}")
            finally:
                HOSTNAME_PLACEHOLDER()
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"SFTP download failed for {remote_path}: {e}")
            raise
        finally:
            HOSTNAME_PLACEHOLDER()

        return local_path

    def initialize_lbsPortal_driver(self, testcase_name, testcase_dir):
        """
        Initializes the Chrome WebDriver with specified options and logs into the Lbs portal web interface.

        :param testcase_name: Used for naming/logging purposes (not used in current logic).
        :param testcase_dir: Directory path for saving downloaded files.
        :return: True if initialization and login are successful.
        """

        # Set up Chrome options
        temp_profile = HOSTNAME_PLACEHOLDER()
        HOSTNAME_PLACEHOLDER = HOSTNAME_PLACEHOLDER()
        # HOSTNAME_PLACEHOLDER.add_argument('--headless')
        HOSTNAME_PLACEHOLDER.add_argument('--ignore-ssl-errors=yes')
        HOSTNAME_PLACEHOLDER.add_argument('--ignore-certificate-errors')
        HOSTNAME_PLACEHOLDER.add_argument("--disable-dev-shm-usage")
        HOSTNAME_PLACEHOLDER.add_argument("--window-size=1920x1080")
        # HOSTNAME_PLACEHOLDER.add_argument("--disable-gpu")
        HOSTNAME_PLACEHOLDER.add_argument(f'--user-data-dir={temp_profile}')
        HOSTNAME_PLACEHOLDER.add_argument('--no-sandbox')
        driver_path = 'LOCAL_PATH_PLACEHOLDER'
        HOSTNAME_PLACEHOLDER(f"Chrom Driver Path : {driver_path} ")
        HOSTNAME_PLACEHOLDER = Service(driver_path)

        # Set download directory for  files
        self.download_dir = testcase_dir
        prefs = {'download.default_directory': self.download_dir}
        HOSTNAME_PLACEHOLDER.add_experimental_option('prefs', prefs)

        # Initialize Chrome WebDriver with service and options
        HOSTNAME_PLACEHOLDER = HOSTNAME_PLACEHOLDER(
            service=HOSTNAME_PLACEHOLDER, options=HOSTNAME_PLACEHOLDER)
        HOSTNAME_PLACEHOLDER.execute_script(
            "HOSTNAME_PLACEHOLDER(navigator, 'webdriver', {get: () => undefined})")

        # Set implicit wait time
        HOSTNAME_PLACEHOLDER.implicitly_wait(10)

        # Open the Anritsu EO Search application
        HOSTNAME_PLACEHOLDER(self.base_url + '#/login?returnUrl=%2F')
        HOSTNAME_PLACEHOLDER.maximize_window()

        # Preform login
        HOSTNAME_PLACEHOLDER.find_element(By.ID, "loginUserId").send_keys(
            self.lbs_username)
        HOSTNAME_PLACEHOLDER.find_element(By.ID, "loginPassword").send_keys(
            self.lbs_password)
        HOSTNAME_PLACEHOLDER.find_element(By.ID, "loginButton").click()

        # HOSTNAME_PLACEHOLDER(10000)

        return True

    def modify_data_from_lbsPortal(self, testcase_name, testcase_dir, record_param, modify_param, record_type):
        '''
            Reverses changes done to existing record 

            Arg:
                testcase_name 
                testcase_dir    : download dir
                record_param    : searched for record
                modify_param    : changes to be made
                record_type     : 5G / 2G / 3G
        '''
        # Initialite Driver
        lbsPorttaldriver = self.initialize_lbsPortal_driver(
            testcase_name, testcase_dir)

        if not lbsPorttaldriver:
            error_msg = "Driver was not Initialized properly"
            HOSTNAME_PLACEHOLDER(error_msg)
            raise ValueError(error_msg)

        HOSTNAME_PLACEHOLDER.find_element(By.ID, f"{record_type}LeftMenu").click()
        # HOSTNAME_PLACEHOLDER(3000)

        original_values = self._find_existing_record(record_param)
        self._modify_existing_record(modify_param)

        return True,   original_values

    def _find_existing_record(self, record_param):
        row = 1
        record_found = False
        while not record_found:
            try:
                # Check each key-value pair in record_param against its column
                col_index = {
                    "MCC": 2,
                    "MNC": 3,
                    "TAG_5G": 4,
                    "NCL": 5,
                    "KKZ": 6
                }
                row_matches = True
                for key, expected_value in record_param.items():
                    col = col_index[key]
                    xpath = f'//*[@id="table"]LOCAL_PATH_PLACEHOLDER[1]LOCAL_PATH_PLACEHOLDER[{row}]/td[{col}]'
                    actual_value = gettext(HOSTNAME_PLACEHOLDER, xpath, f"{key}_ele")
                    if actual_value != expected_value:
                        row_matches = False
                        break
                if row_matches:
                    record_found = True
                    eleclick(HOSTNAME_PLACEHOLDER, xpath, "found_record")
                    HOSTNAME_PLACEHOLDER(f"Record found at row {row}")
                else:
                    row += 1
            except Exception:
                HOSTNAME_PLACEHOLDER(
                    f"Record not found in table. Params: {record_param}")
                break
            # HOSTNAME_PLACEHOLDER(500)

    def _modify_existing_record(self, param_to_modify):
        original_values = {}
        for key, value in param_to_modify.items():
            xpath = f'//input[@id="{key}"]'
            element = HOSTNAME_PLACEHOLDER.find_element(By.XPATH, xpath)
            original_values[key] = element.get_attribute(
                "value")
            sendkeys(HOSTNAME_PLACEHOLDER, xpath, value, "elem_name", True)
            eleclick(HOSTNAME_PLACEHOLDER, '//*[@id="saveSubmit"]', "Save_butto")

        HOSTNAME_PLACEHOLDER(f"Original values before modification: {original_values}")
        return original_values

    def is_record_in_csv_export_file(self, csv_file_path, record_dic):
        '''
        Returns True if record found in csv else False
        Args:
        csv_file_path : file path to csv file
        record_dic : record that contains params to be found
        '''
        HOSTNAME_PLACEHOLDER(
            f"searching for record with parameters : {dict(record_dic)}")
        with open(csv_file_path, newline='', encoding='utf-8') as f:
            reader = HOSTNAME_PLACEHOLDER(f, delimiter=';')
            for row in reader:
                if all(row[key] == value for key, value in record_dic.items()):
                    HOSTNAME_PLACEHOLDER(f"record found : {dict(row)}")
                    return True
        return False

    def reset_data_from_lbsPortal_changes(self, testcase_name, testcase_dir, modify_param, record_param, record_type):
        '''
        Reverses changes done to existing record 
        Retruns True if True else False
            Arg:
                testcase_name 
                testcase_dir    : download dir
                record_param    : searched for record
                modify_param    : changes to be made
                record_type     : 5G / 2G / 3G
        '''

        # Initialite Driver
        lbsPorttaldriver = self.initialize_lbsPortal_driver(
            testcase_name, testcase_dir)

        if not lbsPorttaldriver:
            error_msg = "Driver was not Initialized properly"
            HOSTNAME_PLACEHOLDER(error_msg)
            raise ValueError(error_msg)

        HOSTNAME_PLACEHOLDER.find_element(By.ID, f"{record_type}LeftMenu").click()
        # HOSTNAME_PLACEHOLDER(3000)

        self._find_existing_record(modify_param)
        self._modify_existing_record(record_param)

        return True
