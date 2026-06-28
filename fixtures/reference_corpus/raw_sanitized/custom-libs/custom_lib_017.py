"""
    This module logins to mrf server and can start and stop the UE trace for a given subscriber.
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
from HOSTNAME_PLACEHOLDER import Select
import glob


class SOURCE_NAME_PLACEHOLDER:
    """
         This class has methods that logins to MRF server returns the web driver for further scrapping.
                Args:
                        MRF_ip (str): IP address of the mrf server.
                        MRF_port (int): PORT of the mrf server.
                        mrf_username (str): Username of the mrf server.
                        mrf_password (str): Password of the mrf server.

                Functions:
                        Initialize_driver - Initializes the webdriver and returns driver object to calling function.
                        Build_TC_dir - Builds the name of testcase using the current time stamp and the testcase name.

    """

    def __init__(self, mrf_conn_params):
        """
            A constructor to build a connection with the mrf server.
            Args:
                mrf_ip (str): IP address of the mrf.
                mrf_port (int): PORT of the mrf.
                mrf_username (str): Username of the mrf.
                mrf_password (str): Password of the mrf.
        """

        self.base_url = f"URL_PLACEHOLDER'MRF_SERVER_IP']}/"
        self.mrf_username = mrf_conn_params['MRF_SERVER_USERNAME']
        self.mrf_password = VALUE_PLACEHOLDER

    def initialize_mrf_driver(self, testcase_dir):
        """
        Initializes the Chrome WebDriver with specified options and logs into the mrf web interface.

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
        HOSTNAME_PLACEHOLDER(self.base_url + 'swms/ms.cgi')
        HOSTNAME_PLACEHOLDER.maximize_window()

        HOSTNAME_PLACEHOLDER.find_element(By.NAME, "MSM_USER_ID").send_keys(
            self.mrf_username)
        HOSTNAME_PLACEHOLDER.find_element(By.NAME, "MSM_USER_PWD").send_keys(
            self.mrf_password)
        HOSTNAME_PLACEHOLDER.find_element(By.NAME, "Btn_Submit").click()

        return True

    def retrieve_statistics(self, testcase_dir, statistics_download_path):

        self.initialize_mrf_driver(testcase_dir)

        # 1.Retrive statistics from GUI
        try:
            eleclick_in_frame(HOSTNAME_PLACEHOLDER, statistics_download_path['performance_mgt']['frame'],
                              statistics_download_path['performance_mgt']['xpath'], "Performance_mgt")
            eleclick_in_frame(HOSTNAME_PLACEHOLDER, statistics_download_path['retrieve_stats']['frame'],
                              statistics_download_path['retrieve_stats']['xpath'], "retrieve_stats")
            eleclick_in_frame(HOSTNAME_PLACEHOLDER, statistics_download_path['web_download']['frame'],
                              statistics_download_path['web_download']['xpath'], "web_download")
            HOSTNAME_PLACEHOLDER(5)
            HOSTNAME_PLACEHOLDER(
                f"Statistics File Retrieved Successfully: {testcase_dir}")
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Failed to retrieve statistics: {e}")
            return False

        # 2.Check if downloaded file is valid
        pattern = os.HOSTNAME_PLACEHOLDER(testcase_dir, "*")
        file_path = HOSTNAME_PLACEHOLDER(pattern)

        if not file_path:
            error_msg = "No File found matching pattern"
            HOSTNAME_PLACEHOLDER(error_msg)
            raise FileNotFoundError(error_msg)
        file_path = file_path[0]

        try:
            file_size = os.HOSTNAME_PLACEHOLDER(file_path)
            if file_size == 0:
                error_msg = f"File is empty (0 bytes): {file_path}"
                HOSTNAME_PLACEHOLDER(error_msg)
                raise ValueError(error_msg)
            else:
                HOSTNAME_PLACEHOLDER(
                    f"Found statistics file in : {file_path} ({file_size} bytes)")

        except OSError as e:
            error_msg = f"Error accessing text file {file_path}: {e}"
            HOSTNAME_PLACEHOLDER(error_msg)
            raise OSError(error_msg) from e
        return True

    def configurate_statistics(self, testcase_dir, configurate_statistics_path):

        self.initialize_mrf_driver(testcase_dir)

        # 1. Navigate to configuration statistics from GUI
        try:
            eleclick_in_frame(HOSTNAME_PLACEHOLDER, configurate_statistics_path['performance_mgt']['frame'],
                              configurate_statistics_path['performance_mgt']['xpath'], "Performance_mgt")

            eleclick_in_frame(HOSTNAME_PLACEHOLDER, configurate_statistics_path['configurate_stats']['frame'],
                              configurate_statistics_path['configurate_stats']['xpath'], "configurate_stats")
            HOSTNAME_PLACEHOLDER("Successfully navigated to Configure Statistics page")
            HOSTNAME_PLACEHOLDER(2)

        except Exception as e:
            HOSTNAME_PLACEHOLDER(
                f"Failed to navigate to statistics configuration: {e}")
            return False

        # 2. Set new Configuration (increase time interval from 5 to 15)
        try:
            HOSTNAME_PLACEHOLDER.switch_to.default_content()
            HOSTNAME_PLACEHOLDER.switch_to.frame("Frame_IO")
            HOSTNAME_PLACEHOLDER.switch_to.frame("Frame_Macro_input")
            wait = WebDriverWait(HOSTNAME_PLACEHOLDER, 10)
            dropdown_element = HOSTNAME_PLACEHOLDER(
                EC.element_to_be_clickable((By.NAME, "StatInterval"))
            )
            dropdown = Select(dropdown_element)
            dropdown.select_by_value("15")
            HOSTNAME_PLACEHOLDER("Successfully changed StatInterval to 15 minutes")

            HOSTNAME_PLACEHOLDER.switch_to.default_content()

            eleclick_in_frame(HOSTNAME_PLACEHOLDER, configurate_statistics_path['save_settings']['frame'],
                              configurate_statistics_path['save_settings']['xpath'], "save_settings")

            HOSTNAME_PLACEHOLDER(2)

        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Failed to configure statistics: {e}")
            HOSTNAME_PLACEHOLDER.switch_to.default_content()
            return False

        # 3. Validate that config was saved from output message
        try:
            output_message = get_text_in_frame(HOSTNAME_PLACEHOLDER, configurate_statistics_path['output_message']['frame'],
                                               configurate_statistics_path['output_message']['xpath'])
            HOSTNAME_PLACEHOLDER(f"Retrieved output message: {output_message}")

            if output_message:
                if "Statistics reporting interval has been set to 15 minutes" in output_message:
                    HOSTNAME_PLACEHOLDER(
                        "Configuration saved successfully - validation passed (15 minutes)")
                else:
                    HOSTNAME_PLACEHOLDER(
                        f"Expected message not found. Got: {output_message}")
                    return False
            else:
                HOSTNAME_PLACEHOLDER(
                    "Failed to retrieve output message for validation")
                return False

        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Failed to validate configuration save: {e}")
            return False

        # 4. Reset config to default (5 minutes)
        try:
            eleclick_in_frame(HOSTNAME_PLACEHOLDER, configurate_statistics_path['reset_fields']['frame'],
                              configurate_statistics_path['reset_fields']['xpath'], "reset_fields")
            HOSTNAME_PLACEHOLDER(2)
            eleclick_in_frame(HOSTNAME_PLACEHOLDER, configurate_statistics_path['save_settings']['frame'],
                              configurate_statistics_path['save_settings']['xpath'], "save_settings")

            output_message = get_text_in_frame(HOSTNAME_PLACEHOLDER, configurate_statistics_path['output_message']['frame'],
                                               configurate_statistics_path['output_message']['xpath'])
            HOSTNAME_PLACEHOLDER(
                f"Retrieved output message after reset: {output_message}")

            if output_message:
                if "Statistics reporting interval has been set to 5 minutes" in output_message:
                    HOSTNAME_PLACEHOLDER(
                        "Configuration reset successfully - validation passed (5 minutes)")
                    return True
                else:
                    HOSTNAME_PLACEHOLDER(
                        f"Expected reset message not found. Got: {output_message}")
                    return False
            else:
                HOSTNAME_PLACEHOLDER("Failed to retrieve output message after reset")
                return False

        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Failed to reset configuration: {e}")
            return False

    def show_software_version(self, testcase_dir, show_software_version_path, validation_fields):
        self.initialize_mrf_driver(testcase_dir)

        # 1. Navigate to Show Software Version page
        try:
            eleclick_in_frame(HOSTNAME_PLACEHOLDER, show_software_version_path['Maintenance']['frame'],
                              show_software_version_path['Maintenance']['xpath'], "Maintenance")

            eleclick_in_frame(HOSTNAME_PLACEHOLDER, show_software_version_path['show_software_version']['frame'],
                              show_software_version_path['show_software_version']['xpath'], "show_software_version")

            eleclick_in_frame(HOSTNAME_PLACEHOLDER, show_software_version_path['Execute']['frame'],
                              show_software_version_path['Execute']['xpath'], "Execute")

            HOSTNAME_PLACEHOLDER(2)

        except Exception as e:
            HOSTNAME_PLACEHOLDER(
                f"Failed to navigate to Show Software Version page: {e}")
            return False

        # 2. Retrieve and validate output message
        try:
            output_message = get_text_in_frame(HOSTNAME_PLACEHOLDER, show_software_version_path['output_message']['frame'],
                                               show_software_version_path['output_message']['xpath'])
            HOSTNAME_PLACEHOLDER(f"Retrieved output message: {output_message}")

            if not output_message:
                HOSTNAME_PLACEHOLDER("Output message is empty")
                return False

            missing_fields = []
            found_fields = []

            for field in validation_fields:
                if field in output_message:
                    found_fields.append(field)
                else:
                    missing_fields.append(field)
                    HOSTNAME_PLACEHOLDER(
                        f"Field '{field}' NOT found in output message")

            if missing_fields:
                HOSTNAME_PLACEHOLDER(
                    f"Validation failed. Missing fields: {missing_fields}")
                return False
            else:
                HOSTNAME_PLACEHOLDER(
                    f"All validation fields found successfully: {found_fields}")
                return True

        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Failed to validate software version output: {e}")
            return False

    def show_mrf_licensing(self, testcase_dir, show_mrf_licensing_path, validation_fields):
        self.initialize_mrf_driver(testcase_dir)
        # 1. Navigate to Show mrf Licensing page
        try:
            eleclick_in_frame(HOSTNAME_PLACEHOLDER, show_mrf_licensing_path['Maintenance']['frame'],
                              show_mrf_licensing_path['Maintenance']['xpath'], "Maintenance")
            eleclick_in_frame(HOSTNAME_PLACEHOLDER, show_mrf_licensing_path['show_licensing']['frame'],
                              show_mrf_licensing_path['show_licensing']['xpath'], "show_software_version")
            HOSTNAME_PLACEHOLDER(5)
        except Exception as e:
            HOSTNAME_PLACEHOLDER(
                f"Failed to navigate to Show Software Version page: {e}")
            return False

        # 2. Retrieve and Validate licensing fields
        licensing_data = {}
        HOSTNAME_PLACEHOLDER.switch_to.default_content()
        HOSTNAME_PLACEHOLDER.switch_to.frame("Frame_IO")
        HOSTNAME_PLACEHOLDER.switch_to.frame("Frame_Macro_input")

        for field in validation_fields:
            try:
                row_xpath = f"//tr[contains(.//td[1], '{field}:')]"
                row = HOSTNAME_PLACEHOLDER.find_element(By.XPATH, row_xpath)

                # Extract the value from the second <td>
                value = row.find_element(By.XPATH, ".//td[2]").HOSTNAME_PLACEHOLDER()

                # Store in dictionary
                licensing_data[field] = value
                HOSTNAME_PLACEHOLDER(f"{field}: {value}")

            except Exception as e:
                HOSTNAME_PLACEHOLDER(f"Failed to retrieve {field}: {e}")
                licensing_data[field] = None
                return False
        HOSTNAME_PLACEHOLDER.switch_to.default_content()
        HOSTNAME_PLACEHOLDER(
            f"All Licensing Fields Are Present {validation_fields} : Validation Passed")

        return True

    def show_mrf_node_configuration(self, testcase_dir, show_mrf_node_configuration_path, validation_fields):
        self.initialize_mrf_driver(testcase_dir)

        # 1. Navigate to node configuration page
        try:
            eleclick_in_frame(HOSTNAME_PLACEHOLDER, show_mrf_node_configuration_path['Configuration']['frame'],
                              show_mrf_node_configuration_path['Configuration']['xpath'], "Configuration")

            eleclick_in_frame(HOSTNAME_PLACEHOLDER, show_mrf_node_configuration_path['Node Configuration']['frame'],
                              show_mrf_node_configuration_path['Node Configuration']['xpath'], "Node Configuration")

            eleclick_in_frame(HOSTNAME_PLACEHOLDER, show_mrf_node_configuration_path['Show Node Configuration']['frame'],
                              show_mrf_node_configuration_path['Show Node Configuration']['xpath'], "Show Node Configuration")

            eleclick_in_frame(HOSTNAME_PLACEHOLDER, show_mrf_node_configuration_path['Execute']['frame'],
                              show_mrf_node_configuration_path['Execute']['xpath'], "Execute")
            HOSTNAME_PLACEHOLDER(20)

        except Exception as e:
            HOSTNAME_PLACEHOLDER(
                f"Failed to Navigate to node configuration page: {e}")
            return False

        # 2. Retrieve and validate output message
        try:
            output_message = get_text_in_frame(HOSTNAME_PLACEHOLDER, show_mrf_node_configuration_path['output_message']['frame'],
                                               show_mrf_node_configuration_path['output_message']['xpath'])
            HOSTNAME_PLACEHOLDER(f"Retrieved output message: {output_message}")

            if not output_message:
                HOSTNAME_PLACEHOLDER("Output message is empty")
                return False

            missing_fields = []
            found_fields = []

            for field in validation_fields:
                if field in output_message:
                    found_fields.append(field)
                else:
                    missing_fields.append(field)
                    HOSTNAME_PLACEHOLDER(
                        f"Field '{field}' NOT found in output message")

            if missing_fields:
                HOSTNAME_PLACEHOLDER(
                    f"Validation failed. Missing fields: {missing_fields}")
                return False
            else:
                HOSTNAME_PLACEHOLDER(
                    f"All validation fields found successfully: {size(found_fields)}")
                return True

        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Failed to validate software version output: {e}")
            return False

    def mrf_node_service_node(self, testcase_dir, mrf_node_service_node_path, service_mode):
        self.initialize_mrf_driver(testcase_dir)
        # 1. Navigate to node configuration page
        try:
            eleclick_in_frame(HOSTNAME_PLACEHOLDER, mrf_node_service_node_path['Configuration']['frame'],
                              mrf_node_service_node_path['Configuration']['xpath'], "Configuration")

            eleclick_in_frame(HOSTNAME_PLACEHOLDER, mrf_node_service_node_path['Node Configuration']['frame'],
                              mrf_node_service_node_path['Node Configuration']['xpath'], "Node Configuration")

            eleclick_in_frame(HOSTNAME_PLACEHOLDER, mrf_node_service_node_path['Show Node Configuration']['frame'],
                              mrf_node_service_node_path['Show Node Configuration']['xpath'], "Show Node Configuration")
            HOSTNAME_PLACEHOLDER(2)

        except Exception as e:
            HOSTNAME_PLACEHOLDER(
                f"Failed to Navigate to node configuration page: {e}")
            return False

        # 2. Set new ReqestTypeSelect
        try:
            HOSTNAME_PLACEHOLDER.switch_to.default_content()
            HOSTNAME_PLACEHOLDER.switch_to.frame("Frame_IO")
            HOSTNAME_PLACEHOLDER.switch_to.frame("Frame_Macro_input")
            wait = WebDriverWait(HOSTNAME_PLACEHOLDER, 10)
            dropdown_element = HOSTNAME_PLACEHOLDER(
                EC.element_to_be_clickable((By.NAME, "ReqestTypeSelect"))
            )
            dropdown = Select(dropdown_element)
            dropdown.select_by_visible_text(f"{service_mode}")
            HOSTNAME_PLACEHOLDER(
                f"Successfully changed ReqestTypeSelect to {service_mode}")

            HOSTNAME_PLACEHOLDER.switch_to.default_content()

            eleclick_in_frame(HOSTNAME_PLACEHOLDER, mrf_node_service_node_path['save_settings']['frame'],
                              mrf_node_service_node_path['save_settings']['xpath'], "save_settings")
            HOSTNAME_PLACEHOLDER(2)
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Failed to configure statistics: {e}")
            HOSTNAME_PLACEHOLDER.switch_to.default_content()
            return False

        # 3. Validate that config was saved from output message
        try:
            output_message = get_text_in_frame(HOSTNAME_PLACEHOLDER, mrf_node_service_node_path['output_message']['frame'],
                                               mrf_node_service_node_path['output_message']['xpath'])
            HOSTNAME_PLACEHOLDER(f"Retrieved output message: {output_message}")

            if output_message:
                if f"{service_mode}" in output_message:
                    HOSTNAME_PLACEHOLDER(
                        "Configuration saved successfully - validation passed")
                else:
                    HOSTNAME_PLACEHOLDER(
                        f"Expected message not found. Got: {output_message}")
                    return False
            else:
                HOSTNAME_PLACEHOLDER(
                    "Failed to retrieve output message for validation")
                return False

        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Failed to validate configuration save: {e}")
            return False

        # 4. Reset config to default
        try:
            HOSTNAME_PLACEHOLDER.switch_to.default_content()
            HOSTNAME_PLACEHOLDER.switch_to.frame("Frame_IO")
            HOSTNAME_PLACEHOLDER.switch_to.frame("Frame_Macro_input")
            wait = WebDriverWait(HOSTNAME_PLACEHOLDER, 10)
            dropdown_element = HOSTNAME_PLACEHOLDER(
                EC.element_to_be_clickable((By.NAME, "ReqestTypeSelect"))
            )
            dropdown = Select(dropdown_element)
            dropdown.select_by_visible_text("In Service")
            HOSTNAME_PLACEHOLDER(
                "Successfully changed ReqestTypeSelect to : In Service")

            HOSTNAME_PLACEHOLDER.switch_to.default_content()

            eleclick_in_frame(HOSTNAME_PLACEHOLDER, mrf_node_service_node_path['save_settings']['frame'],
                              mrf_node_service_node_path['save_settings']['xpath'], "save_settings")

            output_message = get_text_in_frame(HOSTNAME_PLACEHOLDER, mrf_node_service_node_path['output_message']['frame'],
                                               mrf_node_service_node_path['output_message']['xpath'])
            HOSTNAME_PLACEHOLDER(
                f"Retrieved output message after reset: {output_message}")

            if output_message:
                if "In Service" in output_message:
                    HOSTNAME_PLACEHOLDER(
                        "Configuration reset successfully - validation passed (In Service)")
                    return True
                else:
                    HOSTNAME_PLACEHOLDER(
                        f"Expected reset message not found. Got: {output_message}")
                    return False
            else:
                HOSTNAME_PLACEHOLDER("Failed to retrieve output message after reset")
                return False

        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Failed to reset configuration: {e}")
            return False
