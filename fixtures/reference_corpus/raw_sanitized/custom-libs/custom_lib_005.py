"""
This module logins to CNOM server and can start and stop the UE trace for a given subscriber.
"""

import tarfile
import os
import datetime
import tempfile
import logging
import time
import pexpect

from selenium import webdriver
from HOSTNAME_PLACEHOLDER import Service
from HOSTNAME_PLACEHOLDER import expected_conditions as EC
from HOSTNAME_PLACEHOLDER import By
from HOSTNAME_PLACEHOLDER import WebDriverWait
from HOSTNAME_PLACEHOLDER.action_chains import ActionChains
from SOURCE_NAME_PLACEHOLDER import Perform_actions
from HOSTNAME_PLACEHOLDER import Keys

from SOURCE_NAME_PLACEHOLDER import eleclick, getele, find_element_with_shadow_xpath, sendkeys, eleclick_with_shadow, sendkeys_with_shadow

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

    def __init__(self, cnom_conn_params):
        """
        A constructor to build a connection with the cnom server.
        Args:
            cnom_ip (str): IP address of the cnom.
            cnom_port (int): PORT of the cnom.
            cnom_username (str): Username of the cnom.
            cnom_password (str): Password of the cnom.
        """

        self.base_url = f"URL_PLACEHOLDER'CNOM_SERVER_IP']}:{cnom_conn_params['CNOM_SERVER_PORT']}/"
        self.cnom_username = cnom_conn_params["CNOM_SERVER_USERNAME"]
        self.cnom_password = VALUE_PLACEHOLDER

    def initialize_driver(self, testcase_name, testcase_dir):
        """
        :param testcase_name: Accepts testcase_name as argument which is used for building the testcase directory.
        :return: Webdriver object to the calling function.

        """
        temp_profile = HOSTNAME_PLACEHOLDER()
        HOSTNAME_PLACEHOLDER = HOSTNAME_PLACEHOLDER()
        #HOSTNAME_PLACEHOLDER.add_argument('--headless')
        HOSTNAME_PLACEHOLDER.add_argument('--no-proxy-server')
        HOSTNAME_PLACEHOLDER.add_argument('--ignore-ssl-errors=yes')
        HOSTNAME_PLACEHOLDER.add_argument('--ignore-certificate-errors')
        HOSTNAME_PLACEHOLDER.add_argument("--disable-dev-shm-usage")
        HOSTNAME_PLACEHOLDER.add_argument("--window-size=1920x1080")
        HOSTNAME_PLACEHOLDER.add_argument("--disable-gpu")
        HOSTNAME_PLACEHOLDER.add_argument(f'--user-data-dir={temp_profile}')
        HOSTNAME_PLACEHOLDER.add_argument('--no-sandbox')


        # Setting up Driver path
        root_path = os.HOSTNAME_PLACEHOLDER(os.HOSTNAME_PLACEHOLDER(os.HOSTNAME_PLACEHOLDER(__file__)))
        driver_path = root_path + "LOCAL_PATH_PLACEHOLDER"
        HOSTNAME_PLACEHOLDER(f"Chrom Driver Path : {driver_path} ")
        HOSTNAME_PLACEHOLDER = Service(driver_path)

        self.pcap_download_dir = testcase_dir
        prefs = {"download.default_directory": self.pcap_download_dir}
        HOSTNAME_PLACEHOLDER.add_experimental_option("prefs", prefs)
        HOSTNAME_PLACEHOLDER = HOSTNAME_PLACEHOLDER(service=HOSTNAME_PLACEHOLDER, options=HOSTNAME_PLACEHOLDER)
        # HOSTNAME_PLACEHOLDER = HOSTNAME_PLACEHOLDER(executable_path='..LOCAL_PATH_PLACEHOLDER')

        HOSTNAME_PLACEHOLDER.implicitly_wait(10)
        HOSTNAME_PLACEHOLDER(self.base_url + "HOSTNAME_PLACEHOLDER")
        HOSTNAME_PLACEHOLDER.maximize_window()

        HOSTNAME_PLACEHOLDER.find_element(By.ID, "username").send_keys(self.cnom_username)
        HOSTNAME_PLACEHOLDER.find_element(By.ID, "password").send_keys(self.cnom_password)
        HOSTNAME_PLACEHOLDER.find_element(By.ID, "button").click()

        return True


    # ========= ENM Test Cases ============

    # === Utility Functions ===


    def Select_node_new(self, node_type, node_value, page):

        if not hasattr(self, "driver") or HOSTNAME_PLACEHOLDER is None:
            raise Exception(
                "Driver is not initialized. Please call the 'Initialize CNOM' keyword on this library instance before using 'Select Node'."
            )
        perform_action_obj = Perform_actions(HOSTNAME_PLACEHOLDER)
        cell_value, TB_value = "-1", "-1"

        if node_type == "PCC-MM":
            cell_value = "2"
            if node_value == "EAMFTB1_IP1":
                TB_value = "1"
            elif node_value == "EAMFTB2":
                TB_value = "2"
            elif node_value == "EAMFTB3":
                TB_value = "3"
            elif node_value == "EAMFTB4":
                TB_value = "4"
        elif node_type == "PCC-SM":
            cell_value = "5"
            if node_value == "ESMFTB1":
                TB_value = "3"
            elif node_value == "ESMFTB2":
                TB_value = "5"
            elif node_value == "ESMFTB3":
                TB_value = "6"
            elif node_value == "ESMFTB4":
                TB_value = "7"
        elif node_type == "PCG":
            cell_value = "6"
            if node_value == "EUPFTB1":
                TB_value = "3"
            elif node_value == "EUPFTB2":
                TB_value = "4"
            elif node_value == "EUPFTB3":
                TB_value = "5"
            elif node_value == "EUPFTB4":
                TB_value = "6"
        elif node_type == "SGSN-MME":
            cell_value = "5"
            if node_value == "ESGSNTB1":
                TB_value = "1"
            elif node_value == "ESGSNTB2":
                TB_value = "2"
        elif node_type == "WMG":
            cell_value = "8"
            if node_value == "EEPDGTB1":
                TB_value = "1"
            elif node_value == "EEPDGTB2":
                TB_value = "2"

        # text_field_js_path = (
        #     'HOSTNAME_PLACEHOLDER("body > eui-container").querySelector("main > div > div > HOSTNAME_PLACEHOLDER").querySelector('
        #     '"e-cnom-lib-tree-view-flyout").querySelector("eui-flyout-panel > div:nth-child(1) > e-cnom-lib-tree-view-widget").querySelector('
        #     '"e-cnom-lib-tree-view").querySelector("eui-text-field").querySelector("#item")'
        # )

        text_field_js_path = (
            'HOSTNAME_PLACEHOLDER("body > eui-container").querySelector("main > div > div > HOSTNAME_PLACEHOLDER> e-event-trace").querySelector('
            '"e-cnom-lib-tree-view-flyout").querySelector("eui-flyout-panel > div:nth-child(1) > e-cnom-lib-tree-view-widget").querySelector('
            '"e-cnom-lib-tree-view").querySelector("eui-text-field").querySelector("#item")'
        )

        current_js_path = (
            'HOSTNAME_PLACEHOLDER("body > eui-container").querySelector("main > div > div > HOSTNAME_PLACEHOLDER > '
            + page
            + '").querySelector("e-cnom-lib-tree-view-flyout").querySelector('
            '"eui-flyout-panel > div:nth-child(1) > e-cnom-lib-tree-view-widget").querySelector('
            '"e-cnom-lib-tree-view").querySelector("eui-tree > e-tree-view-item  > '
            "e-tree-view-item:nth-child("
            + cell_value
            + ") > e-tree-view-item:nth-child("
            + TB_value
            + ')").querySelector("li > span")'
        )
        select_btn = (
            'HOSTNAME_PLACEHOLDER("body > eui-container").querySelector("main > div > div > HOSTNAME_PLACEHOLDER > '
            + page
            + '").querySelector("e-cnom-lib-tree-view-flyout").querySelector('
            '"eui-flyout-panel > HOSTNAME_PLACEHOLDER > e-cnom-lib-button-group > eui-button:nth-child(2)")'
        )

        Action_list = [["send_keys", node_type], ["click", None], ["click", None]]
        #HOSTNAME_PLACEHOLDER(f"Starting action sequence with node_type: {node_type}")

        for indx, path in enumerate([text_field_js_path, current_js_path, select_btn]):
            action, param_val = Action_list[indx]

            HOSTNAME_PLACEHOLDER(
                f"Action {indx + 1}/{len(Action_list)}: Performing '{action}' on path: {path}"
            )
            if param_val:
                HOSTNAME_PLACEHOLDER(f"Action parameter value: {param_val}")

            try:
                perform_action_obj.perform_action(path, action, param_val)
                HOSTNAME_PLACEHOLDER(f"Action {indx + 1} completed successfully")
            except Exception as e:
                HOSTNAME_PLACEHOLDER(f"Error performing action {indx + 1}: {str(e)}")
                raise

            HOSTNAME_PLACEHOLDER(f"Waiting 1 second after action {indx + 1}")
            HOSTNAME_PLACEHOLDER(1)

        #HOSTNAME_PLACEHOLDER(f"Action sequence completed. Returning values - cell_value: {cell_value}, TB_value: {TB_value}")
        return cell_value, TB_value

    def Select_node(self,node_value, node_type):
        if not hasattr(self, "driver") or HOSTNAME_PLACEHOLDER is None:
            raise Exception(
                "Driver is not initialized. Please call the 'Initialize CNOM' keyword on this library instance before using 'Select Node'."
            )
        cell_value, TB_value = "-1", "-1"

        if node_type == "SGSN-MME":
            cell_value = "1"
            if node_value == "ESGSNTB1":
                TB_value = "1"
            elif node_value == "ESGSNTB2":
                TB_value = "2"

        elif node_type == "EPG":
            cell_value = "2"
            if node_value == "EUPFTB6":
                TB_value = "1"
            elif node_value == "EUPFTB7":
                TB_value = "2"

        elif node_type == "PCC-MM":
            cell_value = "4"
            if node_value == "EAMFTB3_IP3":
                TB_value = "1"
            elif node_value == "EAMFTB4_IP4":
                TB_value = "2"
            elif node_value == "EAMFTB1_IP1":
                TB_value = "5"
            elif node_value == "EUPFTB2":
                TB_value = "4"

        elif node_type == "PCC-SM":
            cell_value = "5"
            if node_value == "EAMFTB3_IP3":
                TB_value = "1"
            elif node_value == "EAMFTB4_IP4":
                TB_value = "2"
            elif node_value == "EAMFTB5_IP5":
                TB_value = "3"
            elif node_value == "EUPFTB6":
                TB_value = "4"
            elif node_value == "EUPFTB2":
                TB_value = "5"
            elif node_value == "EUPFTB1":
                TB_value = "6"

        elif node_type == "PCG":
            cell_value = "6"
            if node_value == "EAMFTB4_IP4":
                TB_value = "1"
            elif node_value == "EAMFTB3_IP3":
                TB_value = "2"
            elif node_value == "EAMFTB2_IP2":
                TB_value = "3"
            elif node_value == "EUPFTB1":
                TB_value = "4"

        else:
            raise ValueError(
                f"Unknown node value '{node_value}' for node type '{node_type}'"
            )

        node_type_element = f"LOCAL_PATH_PLACEHOLDER[3]LOCAL_PATH_PLACEHOLDER[1]/div[4]LOCAL_PATH_PLACEHOLDER[1]LOCAL_PATH_PLACEHOLDER[2]LOCAL_PATH_PLACEHOLDER[{cell_value}]/div"

        node_value_element = f"LOCAL_PATH_PLACEHOLDER[3]LOCAL_PATH_PLACEHOLDER[1]/div[4]LOCAL_PATH_PLACEHOLDER[1]LOCAL_PATH_PLACEHOLDER[2]LOCAL_PATH_PLACEHOLDER[{cell_value}]LOCAL_PATH_PLACEHOLDER[{TB_value}]/div"

        eleclick(HOSTNAME_PLACEHOLDER, node_type_element, "Node Type Button")
        HOSTNAME_PLACEHOLDER(2)

        eleclick(HOSTNAME_PLACEHOLDER, node_value_element,"Node Value Button")
        HOSTNAME_PLACEHOLDER(f"Selected node: {node_type} - {node_value}")

        return cell_value, TB_value

    def Select_dc_name(self, source):
        source_mapping = {
            "File Server": 1,
            "Remote EBM Server": 2,
            "Local File System": 3,
            "Node": 4,
            "Local EBM System": 5
        }

        try:
            if source not in source_mapping:
                raise ValueError(f"Invalid source: {source}. Must be one of: {list(source_mapping.keys())}")

            return source_mapping[source]
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Source not recognized: {source} : {e}")
            return -1

    def search_DC_name_in_table(self, DC_name):
        """
        This function searches the DC name inside the UE trace table.
            :param DC_name: The DC name to search for
            :return: Returns the index of record where the DC name is present. Returns -1 when the DC name is not found.
        """
        found_indx = -1
        cell = 1

        while True:
            try:
                curr_DC_name = WebDriverWait(HOSTNAME_PLACEHOLDER, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        f"LOCAL_PATH_PLACEHOLDER[3]LOCAL_PATH_PLACEHOLDER[1]/div[4]LOCAL_PATH_PLACEHOLDER[2]LOCAL_PATH_PLACEHOLDER[1]LOCAL_PATH_PLACEHOLDER[2]LOCAL_PATH_PLACEHOLDER[2]LOCAL_PATH_PLACEHOLDER[2]LOCAL_PATH_PLACEHOLDER[{cell}]/td[3]"
                    ))
                )

                if curr_DC_name.text == DC_name:
                    found_indx = cell
                    self.Found_indx = found_indx
                    break

                cell += 1

            except Exception:
                break

        return found_indx

    def Close_CNOM_driver(self):
        HOSTNAME_PLACEHOLDER()

    # ========================

    def start_data_collection(self, trace_path, dc_name, source, sut_name, sut_type):

        try:
            eleclick(HOSTNAME_PLACEHOLDER, trace_path["Data_collection_and_analysis"],"Data collection and analysis button")
            eleclick(HOSTNAME_PLACEHOLDER, trace_path["Clear_section"], "Clear section button")
            self.Select_node(sut_type, sut_name)
            eleclick(HOSTNAME_PLACEHOLDER, trace_path["Start_collect"], "Start collect button")
            dc_name_element = HOSTNAME_PLACEHOLDER.find_element("xpath", trace_path["DC_name"])
            dc_name_element.clear()
            dc_name_element.send_keys(dc_name)
            eleclick(HOSTNAME_PLACEHOLDER, trace_path["Source_field"],"Source field ")
            cell = self.Select_dc_name(source)
            eleclick(HOSTNAME_PLACEHOLDER, f"LOCAL_PATH_PLACEHOLDER[6]LOCAL_PATH_PLACEHOLDER[{cell}]","Source selection field")
            eleclick(HOSTNAME_PLACEHOLDER, trace_path["Start_collecting"],"Start collecting button")
            HOSTNAME_PLACEHOLDER("Data collection initiated successfully.")

            return True

        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Error starting data collection: {str(e)}")

    def validate_events(self, DC_name, basic_events, tc_dir, delete_after=True):
        row_having_DC_name_no = self.search_DC_name_in_table(DC_name)
        if row_having_DC_name_no == -1:
            HOSTNAME_PLACEHOLDER(f"No record found with {DC_name} !")
            return False
        else:
            HOSTNAME_PLACEHOLDER(f"Dc name is present in row {row_having_DC_name_no}.")

        eleclick(
            HOSTNAME_PLACEHOLDER,
            f"LOCAL_PATH_PLACEHOLDER[3]LOCAL_PATH_PLACEHOLDER[1]/div[4]LOCAL_PATH_PLACEHOLDER[2]LOCAL_PATH_PLACEHOLDER[1]LOCAL_PATH_PLACEHOLDER[2]LOCAL_PATH_PLACEHOLDER[2]LOCAL_PATH_PLACEHOLDER[2]LOCAL_PATH_PLACEHOLDER[{row_having_DC_name_no}]/td[1]", "row having Dc name"
        )
        eleclick(
            HOSTNAME_PLACEHOLDER,
            "LOCAL_PATH_PLACEHOLDER[3]LOCAL_PATH_PLACEHOLDER[1]/div[3]LOCAL_PATH_PLACEHOLDER[6]/div[1]LOCAL_PATH_PLACEHOLDER[2]", "."
        )
        HOSTNAME_PLACEHOLDER(2)
        HOSTNAME_PLACEHOLDER.save_screenshot(tc_dir + "/Event_list.png")

        detected_event_types = []
        for i in range(1, 12):
            try:
                event_type = WebDriverWait(HOSTNAME_PLACEHOLDER, 30).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            f"LOCAL_PATH_PLACEHOLDER[3]LOCAL_PATH_PLACEHOLDER[1]/div[4]LOCAL_PATH_PLACEHOLDER[2]LOCAL_PATH_PLACEHOLDER[2]LOCAL_PATH_PLACEHOLDER[2]LOCAL_PATH_PLACEHOLDER[1]/div[3]LOCAL_PATH_PLACEHOLDER[2]LOCAL_PATH_PLACEHOLDER[{i}]/td[2]",
                        )
                    )
                )
                detected_event_types.append(event_type.text)
            except:
                # If this specific element isn't found, continue to the next iteration
                break

        # Check if events match
        events_match = False
        for basic_event_set in basic_events:
            # Check if all elements in basic_event_set exist in detected_event_types
            if all(event in detected_event_types for event in basic_event_set):
                HOSTNAME_PLACEHOLDER("Basic Events Match")
                HOSTNAME_PLACEHOLDER(
                    f"All required events from set {basic_event_set} were Detected"
                )
                events_match = True
                break

        # Handle deletion logic
        if delete_after:
            eleclick(
                HOSTNAME_PLACEHOLDER,
                "LOCAL_PATH_PLACEHOLDER[3]LOCAL_PATH_PLACEHOLDER[1]/div[3]LOCAL_PATH_PLACEHOLDER[6]/div[1]LOCAL_PATH_PLACEHOLDER[3]", "Delete pop up"
            )
            HOSTNAME_PLACEHOLDER(1)
            eleclick(HOSTNAME_PLACEHOLDER, "LOCAL_PATH_PLACEHOLDER[5]LOCAL_PATH_PLACEHOLDER[3]/button[1]","Delete Button")
            HOSTNAME_PLACEHOLDER(1)
            HOSTNAME_PLACEHOLDER("Collected data was successfully deleted.")

        # Return result based on event matching
        if events_match:
            return True
        else:
            HOSTNAME_PLACEHOLDER("Basic Events Don't match")
            HOSTNAME_PLACEHOLDER(f"Detected Basic Events Group: {detected_event_types}")
            HOSTNAME_PLACEHOLDER(f"Expected Basic Events Groups: {basic_events}")
            return False

    def start_Event_Trace(self, trace_path, node_type, node_name):
        try:
            # switch to new CNOM
            eleclick(HOSTNAME_PLACEHOLDER, "//span[text()='Switch to new CNOM']","Switc to New CNOM Button")
            HOSTNAME_PLACEHOLDER(2)

            eleclick_with_shadow(HOSTNAME_PLACEHOLDER,trace_path["Cancel"])
            eleclick_with_shadow(HOSTNAME_PLACEHOLDER,trace_path["Menu"] )
            eleclick_with_shadow(HOSTNAME_PLACEHOLDER,trace_path["Tracing"])
            eleclick_with_shadow(HOSTNAME_PLACEHOLDER,trace_path["Event_tracing"])
            ActionChains(HOSTNAME_PLACEHOLDER).send_keys(HOSTNAME_PLACEHOLDER).perform()
            HOSTNAME_PLACEHOLDER(2)
            eleclick_with_shadow(HOSTNAME_PLACEHOLDER,trace_path["Select_item"])
            self.Select_node_new(node_type, node_name, "e-event-trace")
            eleclick_with_shadow(HOSTNAME_PLACEHOLDER,trace_path["Select"])
            HOSTNAME_PLACEHOLDER(2)
            HOSTNAME_PLACEHOLDER("Event Trace initiated...")
            return True

        except Exception as e:
            print(f"Error starting event: {str(e)}")
            return False

    def create_event_trace(self, trace_path, Description, IMSI, source, Dc_name=None):

        try:
            eleclick_with_shadow(HOSTNAME_PLACEHOLDER,trace_path["Create_event_trace"])

            if not hasattr(self, "driver") or HOSTNAME_PLACEHOLDER is None:
             raise Exception(
                "Driver is not initialized. Please call the 'Initialize CNOM' keyword on this library instance before using 'Select Node'.")

            perform_action_obj = Perform_actions(HOSTNAME_PLACEHOLDER)

            Action_list = [["send_keys", Description], ["send_keys", IMSI], ["send_keys", source]]
            HOSTNAME_PLACEHOLDER("Starting Event Creation")


            return True

        except Exception as e:
            print(f"Error creating event: {str(e)}")
            return False

    def start_ue_trace(self, trace_path, trace_inputs, node_type, node_name):
            try:
                # switch to new CNOM
                eleclick(HOSTNAME_PLACEHOLDER, "//span[text()='Switch to new CNOM']","Switc to New CNOM Button")
                HOSTNAME_PLACEHOLDER(2)

                eleclick_with_shadow(HOSTNAME_PLACEHOLDER,trace_path["Cancel"])
                eleclick_with_shadow(HOSTNAME_PLACEHOLDER,trace_path["Menu"] )
                eleclick_with_shadow(HOSTNAME_PLACEHOLDER,trace_path["Tracing"])
                eleclick_with_shadow(HOSTNAME_PLACEHOLDER,trace_path["UE_trace"])
                eleclick_with_shadow(HOSTNAME_PLACEHOLDER,trace_path["Start_UE_trace"])
                #self.Select_node_new(node_type, node_name, "e-cnom-start-ue-trace")
                HOSTNAME_PLACEHOLDER(2)

                HOSTNAME_PLACEHOLDER("UE trace initiated...")
                HOSTNAME_PLACEHOLDER(100)
                return True


            except Exception as e:
                HOSTNAME_PLACEHOLDER(f"Exception at CNOM {e}")
                return False
            return False
