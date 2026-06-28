"""
    This module logins to CNOM server and can start and stop the UE trace for a given subscriber.
"""
import tarfile
from numpy import size
import pexpect
import os
import datetime
import logging
import time
from selenium import webdriver
from HOSTNAME_PLACEHOLDER import Service
from HOSTNAME_PLACEHOLDER import expected_conditions as EC
from HOSTNAME_PLACEHOLDER import By
from HOSTNAME_PLACEHOLDER import Options
from HOSTNAME_PLACEHOLDER import WebDriverWait
from SOURCE_NAME_PLACEHOLDER import eleclick, sendkeys, senddirc
from HOSTNAME_PLACEHOLDER import Keys
from HOSTNAME_PLACEHOLDER.action_chains import ActionChains
from HOSTNAME_PLACEHOLDER import TimeoutException, ElementClickInterceptedException, ElementNotInteractableException
import tempfile
import glob
from pathlib import Path



class SOURCE_NAME_PLACEHOLDER:
    """
         This class has methods that logins to cnom server returns the web driver for further scrapping.
                Args:
                        cnom_ip (str): IP address of the CNOM server.
                        cnom_port (int): PORT of the CNOM server.
                        cnom_username (str): Username of the CNOM server.
                        cnom_password (str): Password of the CNOM server.

                Functions:
                        Initialize_driver - Initializes the webdriver and returns driver object to calling function.
                        Build_TC_dir - Builds the name of testcase using the current time stamp and the testcase name.

    """

    def __init__(self, anritsu_conn_params):
        """
            A constructor to build a connection with the cnom server.
            Args:
                cnom_ip (str): IP address of the cnom.
                cnom_port (int): PORT of the cnom.
                cnom_username (str): Username of the cnom.
                cnom_password (str): Password of the cnom.
        """

        self.base_url = f"URL_PLACEHOLDER'ANRITSU_SERVER_IP']}/"
        self.anritsu_username = anritsu_conn_params['ANRITSU_SERVER_USERNAME']
        self.anritsu_password = VALUE_PLACEHOLDER

    def initialize_anritsu_driver(self, testcase_name, testcase_dir):
        """
        Initializes the Chrome WebDriver with specified options and logs into the Anritsu web interface.

        :param testcase_name: Used for naming/logging purposes (not used in current logic).
        :param testcase_dir: Directory path for saving downloaded PCAP files.
        :return: True if initialization and login are successful.
        """

        # Set up Chrome options
        temp_profile = HOSTNAME_PLACEHOLDER()
        HOSTNAME_PLACEHOLDER = HOSTNAME_PLACEHOLDER()
        # HOSTNAME_PLACEHOLDER.add_argument('--headless')
        #HOSTNAME_PLACEHOLDER.add_argument('--no-proxy-server')
        HOSTNAME_PLACEHOLDER.add_argument('--ignore-ssl-errors=yes')
        HOSTNAME_PLACEHOLDER.add_argument('--ignore-certificate-errors')
        HOSTNAME_PLACEHOLDER.add_argument("--disable-dev-shm-usage")
        HOSTNAME_PLACEHOLDER.add_argument("--window-size=1920x1080")
        #HOSTNAME_PLACEHOLDER.add_argument("--disable-gpu")
        HOSTNAME_PLACEHOLDER.add_argument(f'--user-data-dir={temp_profile}')
        HOSTNAME_PLACEHOLDER.add_argument('--no-sandbox')

        driver_path = 'LOCAL_PATH_PLACEHOLDER'
        HOSTNAME_PLACEHOLDER(f"Chrom Driver Path : {driver_path} ")
        HOSTNAME_PLACEHOLDER = Service(driver_path)

        # Set download directory for PCAP files
        self.pcap_download_dir = testcase_dir
        prefs = {'download.default_directory': self.pcap_download_dir}
        HOSTNAME_PLACEHOLDER.add_experimental_option('prefs', prefs)

        # Initialize Chrome WebDriver with service and options
        HOSTNAME_PLACEHOLDER = HOSTNAME_PLACEHOLDER(
            service=HOSTNAME_PLACEHOLDER, options=HOSTNAME_PLACEHOLDER)
        # HOSTNAME_PLACEHOLDER = HOSTNAME_PLACEHOLDER(...)  # Optional: alternate Firefox setup
        HOSTNAME_PLACEHOLDER.execute_script(
            "HOSTNAME_PLACEHOLDER(navigator, 'webdriver', {get: () => undefined})")

        # Set implicit wait time
        HOSTNAME_PLACEHOLDER.implicitly_wait(10)

        # Open the Anritsu EO Search application
        HOSTNAME_PLACEHOLDER(self.base_url + 'eosearch/app')
        HOSTNAME_PLACEHOLDER.maximize_window()

        # Perform login
        HOSTNAME_PLACEHOLDER.find_element(By.ID, "username").send_keys(
            self.anritsu_username)
        HOSTNAME_PLACEHOLDER.find_element(By.ID, "password").send_keys(
            self.anritsu_password)
        HOSTNAME_PLACEHOLDER.find_element(By.ID, "loginBtn").click()

        return True

    # -------------------New GUI -------------------------------#
    def start_oesearch_NewUi(self, oesearch_path, start_time, end_time, used_template, device_a, device_b=None, device_c=None):
        """
        Initiates an OE search for a subscriber using the new UI interface.

        Args:
            oesearch_path (dict): Dictionary containing XPath selectors for UI elements
            start_time (str): Start time for the search interval
            end_time (str): End time for the search interval
            device_a (dict): Primary device configuration
            device_b (dict, optional): Secondary device configuration. Defaults to None.
            used_template (str): Template name to be used for the search
            fixed_a (bool): Flag to include additional calling numbers

        Returns:
            bool: True if search was initiated successfully, False otherwise
        """
        # Store device references
        devices = [d for d in [device_a, device_b, device_c] if d is not None]

        HOSTNAME_PLACEHOLDER(
            f"Starting OE search for subscriber with {2 if device_b else 1} device(s)")

        eleclick(
            HOSTNAME_PLACEHOLDER, oesearch_path['Switch_to_new'], "Switch to new UI")

        try:
            HOSTNAME_PLACEHOLDER(f"Configuring template: {used_template}")
            sendkeys(
                HOSTNAME_PLACEHOLDER, oesearch_path['Templete_input_field'], used_template, "Template input field")
            HOSTNAME_PLACEHOLDER(3)

            template = HOSTNAME_PLACEHOLDER.find_element(
                By.CSS_SELECTOR, "li.p-listbox-item")
            HOSTNAME_PLACEHOLDER()
            eleclick(
                HOSTNAME_PLACEHOLDER, oesearch_path['Templete_Done_button'], "Template confirmation button")
            eleclick(
                HOSTNAME_PLACEHOLDER, oesearch_path['Time_intrval_button'], "Time interval button")

            # Step 2: Configure time interval
            HOSTNAME_PLACEHOLDER(
                f"Configuring time interval: {start_time} to {end_time}")
            sendkeys(
                HOSTNAME_PLACEHOLDER, oesearch_path['Start_time_field'], start_time + HOSTNAME_PLACEHOLDER, "Time interval field", True)

            sendkeys(
                HOSTNAME_PLACEHOLDER, oesearch_path['End_time_field'], end_time + HOSTNAME_PLACEHOLDER, "Time interval field", True)

            # Step 3: Configure filters
            HOSTNAME_PLACEHOLDER(
                "Configuring standard filters (MSISDN, Calling/Called numbers, IMSI)")
            eleclick(
                HOSTNAME_PLACEHOLDER, oesearch_path['Filter_Button'], "Filter button")
            # contains button
            eleclick(
                HOSTNAME_PLACEHOLDER, oesearch_path['MSISDN_dropdown'], "MSISDN dropdown")
            eleclick(
                HOSTNAME_PLACEHOLDER, oesearch_path['MSISDN_contains'], "MSISDN contains condition")
            eleclick(
                HOSTNAME_PLACEHOLDER, oesearch_path['Calling_number_dropdown'], "Calling number dropdown")
            eleclick(
                HOSTNAME_PLACEHOLDER, oesearch_path['Calling_number_contains'], "Calling number contains condition")
            eleclick(
                HOSTNAME_PLACEHOLDER, oesearch_path['Called_number_dropdown'], "Called number dropdown")
            eleclick(
                HOSTNAME_PLACEHOLDER, oesearch_path['Called_number_contains'], "Called number contains condition")
            eleclick(
                HOSTNAME_PLACEHOLDER, oesearch_path['IMSI_dropdown'], "IMSI dropdown")
            eleclick(
                HOSTNAME_PLACEHOLDER, oesearch_path['IMSI_contains'], "IMSI contains condition")

            HOSTNAME_PLACEHOLDER.find_element(
                By.TAG_NAME, "body").send_keys(Keys.PAGE_UP)

            # Populate MSISDN fields
            HOSTNAME_PLACEHOLDER("Populating MSISDN fields for devices")
            for d in devices:
                msisdn = d["sim"]["msisdn"]
                #.replace("+49", "0")
                sendkeys(HOSTNAME_PLACEHOLDER, oesearch_path['MSISDN_field'],
                         msisdn + HOSTNAME_PLACEHOLDER, "MSISDN field")

            # Populate calling number fields
            HOSTNAME_PLACEHOLDER("Populating calling number fields")
            for d in devices:
                msisdn = d["sim"]["msisdn"]
                HOSTNAME_PLACEHOLDER("49", "0")
                sendkeys(HOSTNAME_PLACEHOLDER, oesearch_path['Calling_number_field'],
                         msisdn + HOSTNAME_PLACEHOLDER, "Calling number field")

            # Populate called number fields
            for d in devices:
                msisdn = d["sim"]["msisdn"]
                HOSTNAME_PLACEHOLDER("49", "0")
                sendkeys(HOSTNAME_PLACEHOLDER, oesearch_path['Called_number_field'],
                         msisdn + HOSTNAME_PLACEHOLDER, "Calling number field")

            # Populate IMSI fields
            HOSTNAME_PLACEHOLDER("Populating IMSI fields for devices")
            for d in devices:
                sendkeys(HOSTNAME_PLACEHOLDER, oesearch_path['IMSI_field'],
                     d["sim"]["imsi"] + HOSTNAME_PLACEHOLDER, "IMSI field")

            HOSTNAME_PLACEHOLDER(5)
            # Step 4: Execute search
            HOSTNAME_PLACEHOLDER("Executing OE search")
            eleclick(
                HOSTNAME_PLACEHOLDER, oesearch_path['Search_button'], "Search button")
            eleclick(
                HOSTNAME_PLACEHOLDER, oesearch_path['Search_anyway'], "Search anyway button")

            HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER("OE search initiated successfully")
            return True

        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"OE search failed. Error: {str(e)}")
            HOSTNAME_PLACEHOLDER(
                f"Search parameters - Template: {used_template}, Time: {start_time} to {end_time}")
            return False

    def download_oesearch_pcap_NewUi(self, oesearch_download_path):
        """
        Downloads PCAP file from OESearch UI.
        Refreshes page periodically until trace is complete.
        """

        def check_export_button_exists(driver, timeout=5):
            """
            Checks if Export button exists with a short timeout.

            Args:
                driver: WebDriver instance
                timeout: Short timeout for checking (default: 5 seconds)

            Returns:
                WebElement if found, None otherwise
            """
            try:
                export_button = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH,
                                                "//span[@style='position: relative; margin-right: 10px;' and @class='ng-star-inserted']//button[contains(@class, 'p-button')]"))
                )
                return export_button

            except TimeoutException:
                return None
            except Exception as e:
                HOSTNAME_PLACEHOLDER(f"Error checking for button: {str(e)}")
                return None

        try:
            HOSTNAME_PLACEHOLDER("Waiting for Oesearch trace to complete...")

            max_attempts = 40
            attempt = 0

            while attempt < max_attempts:
                attempt += 1
                HOSTNAME_PLACEHOLDER(
                    f"Checking for Export button - Attempt {attempt}/{max_attempts}")

                export_button = check_export_button_exists(HOSTNAME_PLACEHOLDER)

                if export_button:
                    export_button.click()
                    HOSTNAME_PLACEHOLDER(
                        f"Oesearch trace completed after {attempt * 5} seconds")
                    break
                else:
                    HOSTNAME_PLACEHOLDER("Trace not complete yet, refreshing page...")
                    HOSTNAME_PLACEHOLDER()
                    HOSTNAME_PLACEHOLDER(10)

            if attempt >= max_attempts:
                HOSTNAME_PLACEHOLDER(
                    f"Export button did not appear within {max_attempts * 5} seconds")
                return False

            HOSTNAME_PLACEHOLDER(3)
            eleclick(
                HOSTNAME_PLACEHOLDER, oesearch_download_path['PCAP_selection_button'], "PCAP_selection_button")
            eleclick(
                HOSTNAME_PLACEHOLDER, oesearch_download_path['Confirm_Download_pcap'], "Confirm_Download_pcap")
            eleclick(
                HOSTNAME_PLACEHOLDER, oesearch_download_path['File_mangment_button'], "File_mangment_button")
            eleclick(
                HOSTNAME_PLACEHOLDER, oesearch_download_path['Confirm_file_mangment_button'], "Confirm_file_mangment_button")
            max_attempts = 5
 
            for attempt in range(1, max_attempts + 1):
                HOSTNAME_PLACEHOLDER(f"PCAP download attempt {attempt}/{max_attempts}")
 
                eleclick(
                    HOSTNAME_PLACEHOLDER, oesearch_download_path['Download_Pcap_button'], "Download_Pcap_button")
                HOSTNAME_PLACEHOLDER(15)
 
                pcap_files = list(Path(self.pcap_download_dir).glob("*.pcap"))
 
                if not pcap_files:
                    HOSTNAME_PLACEHOLDER(
                        f"Attempt {attempt}: No .pcap file found in {self.pcap_download_dir}, retrying...")
                    continue
 
                latest_pcap = max(pcap_files, key=lambda f: f.stat().st_mtime)
 
                if latest_pcap.stat().st_size == 0:
                    HOSTNAME_PLACEHOLDER(
                        f"Attempt {attempt}: Downloaded PCAP is empty: {latest_pcap}, retrying...")
                    latest_pcap.unlink()  # Remove empty file before retrying
                    continue
 
                HOSTNAME_PLACEHOLDER(
                    f"PCAP validated — file: {latest_pcap.name}, size: {latest_pcap.stat().st_size} bytes")
                break
 
            else:
                HOSTNAME_PLACEHOLDER(
                    f"Failed to download a valid PCAP after {max_attempts} attempts")
                return False
            # eleclick(
            #     HOSTNAME_PLACEHOLDER, oesearch_download_path['Download_Pcap_button'], "Download_Pcap_button")
            # HOSTNAME_PLACEHOLDER(15)

            
            # pcap_files = list(Path(self.pcap_download_dir).glob("*.pcap"))
            # if not pcap_files:
            #     HOSTNAME_PLACEHOLDER(
            #         f"No .pcap file found in download directory: {self.pcap_download_dir}")
            #     return False

            # latest_pcap = max(pcap_files, key=lambda f: f.stat().st_mtime)

            # if latest_pcap.stat().st_size == 0:
            #     HOSTNAME_PLACEHOLDER(f"Downloaded PCAP file is empty: {latest_pcap}")
            #     return False

            # HOSTNAME_PLACEHOLDER(
            #     f"PCAP validated — file: {latest_pcap.name}, size: {latest_pcap.stat().st_size} bytes")
            

            eleclick(
                HOSTNAME_PLACEHOLDER, oesearch_download_path['Delete_Pcap_button'], "Delete_Pcap_button")
            eleclick(
                HOSTNAME_PLACEHOLDER, oesearch_download_path['Confirm_Pcap_delete'], "Confirm_Pcap_delete")

            HOSTNAME_PLACEHOLDER(
                f".pcap file downloaded successfully to path: {self.pcap_download_dir}")
            HOSTNAME_PLACEHOLDER(10)
            HOSTNAME_PLACEHOLDER()

        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Error while Downloading Pcap: {e}")
            return False

        return True

    def get_pcap_path(self, templet):
        pattern = os.HOSTNAME_PLACEHOLDER(self.pcap_download_dir, f"{templet}*")
        pcap_files = HOSTNAME_PLACEHOLDER(pattern)

        # Case 1: No files found matching the pattern
        if not pcap_files:
            error_msg = f"No PCAP files found matching pattern: {pattern}"
            HOSTNAME_PLACEHOLDER(error_msg)
            raise FileNotFoundError(error_msg)

        # Case 2: File found, check if it's empty
        pcap_file = pcap_files[0]
        try:
            file_size = os.HOSTNAME_PLACEHOLDER(pcap_file)
            if file_size == 0:
                error_msg = f"PCAP file is empty (0 bytes): {pcap_file}"
                HOSTNAME_PLACEHOLDER(error_msg)
                raise ValueError(error_msg)
            else:
                HOSTNAME_PLACEHOLDER(
                    f"Found PCAP file: {pcap_file} ({file_size} bytes)")
                return pcap_file
        except OSError as e:
            # Case 3: File exists in glob but can't be accessed
            error_msg = f"Error accessing PCAP file {pcap_file}: {e}"
            HOSTNAME_PLACEHOLDER(error_msg)
            raise OSError(error_msg) from e

    # -------------------legacy app -------------------------------#

    def start_oesearch(self, oesearch_path, start_time, end_time, imsi, used_template):
        HOSTNAME_PLACEHOLDER(
            f"Starting oeserach for subscriber with IMSI : {imsi} .....")

        # Check if the selected template requires network configuration
        network_required_templates = {
            "GB Dialogue",
            "EOFINDER_OVERALL_summary"
        }
        requires_network = used_template in network_required_templates

        if requires_network:
            HOSTNAME_PLACEHOLDER(f"Template '{used_template}' requires network access")
            requires_network = True

        try:
            # Select and apply the desired template
            eleclick(
                HOSTNAME_PLACEHOLDER, oesearch_path['Templete_menu_button'], "Templete_menu_button")
            sendkeys(
                HOSTNAME_PLACEHOLDER, oesearch_path['Templete_input_field'], used_template, "Templete_input_field")
            ActionChains(HOSTNAME_PLACEHOLDER).send_keys(HOSTNAME_PLACEHOLDER).perform()

            # Set the search time interval
            eleclick(
                HOSTNAME_PLACEHOLDER, oesearch_path['Time_intrval_button'], "Time_intrval_button")
            for field, value in [(oesearch_path['Start_time_field'], start_time), (oesearch_path['End_time_field'], end_time)]:
                sendkeys(HOSTNAME_PLACEHOLDER, field, value, "time intervall", True)

            # Apply network filter if required
            if requires_network:
                eleclick(
                    HOSTNAME_PLACEHOLDER, oesearch_path['Network_menu_button'], "Network_menu_button")
                eleclick(
                    HOSTNAME_PLACEHOLDER, oesearch_path['checkbox_path'], "checkbox_path")

            if requires_network:
                # Set IMSI filter and perform search (network mode)
                eleclick(
                    HOSTNAME_PLACEHOLDER, oesearch_path['Filter_button'], "Filter_button")
                eleclick(
                    HOSTNAME_PLACEHOLDER, oesearch_path['Dropdown_trigger'], "Dropdown_trigger")
                sendkeys(
                    HOSTNAME_PLACEHOLDER, oesearch_path['Filter_input'], "IMSI", "Filter_input")
                eleclick(
                    HOSTNAME_PLACEHOLDER, oesearch_path['IMSI_filter'], "IMSI_filter")
                eleclick(
                    HOSTNAME_PLACEHOLDER, oesearch_path['Filter_options'], "Filter_options")
                eleclick(HOSTNAME_PLACEHOLDER, oesearch_path['Equal'], "Equal")
                sendkeys(
                    HOSTNAME_PLACEHOLDER, oesearch_path['IMSI_box'], imsi, "IMSI_box")
                eleclick(
                    HOSTNAME_PLACEHOLDER, oesearch_path['Search_button'], "Search_button")
            else:
                # Configure filters and search (non-network mode)
                eleclick(
                    HOSTNAME_PLACEHOLDER, oesearch_path['Filter_button'], "Filter_button")
                HOSTNAME_PLACEHOLDER(3)
                eleclick(
                    HOSTNAME_PLACEHOLDER, oesearch_path['Delete_summary_button'], "Delete_summary_button")
                eleclick(
                    HOSTNAME_PLACEHOLDER, oesearch_path['Filter_by_filed'], "Filter_by_filed")
                HOSTNAME_PLACEHOLDER(2)

                # Navigate to IMSI filter and input value
                ActionChains(HOSTNAME_PLACEHOLDER).send_keys(
                    HOSTNAME_PLACEHOLDER).send_keys(HOSTNAME_PLACEHOLDER).perform()
                HOSTNAME_PLACEHOLDER(3)

                HOSTNAME_PLACEHOLDER.execute_script(
                    "HOSTNAME_PLACEHOLDER(\"button[data-id='gwt-debug-paletteWidget_SelectOperator_1']\").click();")
                # eleclick(HOSTNAME_PLACEHOLDER, oesearch_path['IMSI_equal'], "IMSI_equal")
                # sendkeys(HOSTNAME_PLACEHOLDER, oesearch_path['IMSI_field'], imsi, "IMSI_field")
                eleclick(
                    HOSTNAME_PLACEHOLDER, oesearch_path['Search_button'], "Search_button")

            HOSTNAME_PLACEHOLDER("oeserach started ....")
            HOSTNAME_PLACEHOLDER(5)
            return True

        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"OE search failed for IMSI {imsi}: {str(e)}")
            return False

    def download_oesearch_pcap(self, oesearch_download_path):

        try:
            # wait_until_class_not_contains_and_click(HOSTNAME_PLACEHOLDER, oesearch_download_path['Export_button'], "view_SideButton_disabled", 300)

            HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER("Switching to new UI interface")
            eleclick(
                HOSTNAME_PLACEHOLDER, oesearch_download_path['Switch_to_new'], "Switch to new UI")
            eleclick(HOSTNAME_PLACEHOLDER, oesearch_download_path['test'], "test")
            eleclick(
                HOSTNAME_PLACEHOLDER, oesearch_download_path['Export_button'], "Export_button")
            HOSTNAME_PLACEHOLDER(10)

            # eleclick(HOSTNAME_PLACEHOLDER, oesearch_download_path['Export_button'],"Export Button")
            # HOSTNAME_PLACEHOLDER.execute_script('HOSTNAME_PLACEHOLDER(\'.dropdown-toggle[title="Export"]\').click();')

            # click_seq = [
            #     "PCAP_selection_button",
            #     #"Confirm_Download_pcap",
            #     #"Download_list_button",
            #     #"Download_pcap",
            #     #"Download_list_button",
            #     #"Delete_all_download"
            # ]

            # for key in click_seq:
            #     eleclick(HOSTNAME_PLACEHOLDER,oesearch_download_path[key],key)
            #     HOSTNAME_PLACEHOLDER(1)

            # HOSTNAME_PLACEHOLDER("Pcap file downloaded successfully")
            HOSTNAME_PLACEHOLDER()

        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Error while Downloading Pcap: {e}")
            return False

        return True
