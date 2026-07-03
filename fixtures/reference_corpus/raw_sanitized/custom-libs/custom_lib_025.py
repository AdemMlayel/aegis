import logging
import re
import time
from SOURCE_NAME_PLACEHOLDER import SOURCE_NAME_PLACEHOLDER
from HOSTNAME_PLACEHOLDER import keyword
from SOURCE_NAME_PLACEHOLDER import Perform_actions  # Using absolute import
from SOURCE_NAME_PLACEHOLDER import find_element_with_shadow_xpath
from HOSTNAME_PLACEHOLDER import BuiltIn
from datetime import datetime
from HOSTNAME_PLACEHOLDER import WebDriverWait
from HOSTNAME_PLACEHOLDER import expected_conditions as EC
from HOSTNAME_PLACEHOLDER import By


class SOURCE_NAME_PLACEHOLDER(SOURCE_NAME_PLACEHOLDER):
    def __init__(self, cnom_conn_params=None, node_type=None, node_name=None):
        # SOURCE_NAME_PLACEHOLDER.__init__ should set HOSTNAME_PLACEHOLDER and self.pcap_download_dir.
        super().__init__(cnom_conn_params)
        self.node_type = node_type
        self.node_name = node_name
        HOSTNAME_PLACEHOLDER("SOURCE_NAME_PLACEHOLDER loaded successfully.")

    @keyword("Initialize CNOM")
    def initialize_cnom(self, cnom_obj, testcase_name, node_type, node_value, tc_dir):
        """
        Initialize CNOM by setting the driver and storing node parameters.

        :param cnom_obj: An object or dictionary containing CNOM connection details.
        :param testcase_name: The test case name (used to build the testcase directory).
        :param node_type: The type of node (e.g., PCC-MM).
        :param node_value: The node identifier (e.g., EAMFTB1).
        :return: Boolean, True if initialization succeeds.
        """
        self.login_cnom_obj = cnom_obj
        # Call the initialize_driver method; note that it sets HOSTNAME_PLACEHOLDER and self.pcap_download_dir.
        status = self.initialize_driver(testcase_name, tc_dir)  # Returns bool
        # Set self.testcase_dir to the attribute used in SOURCE_NAME_PLACEHOLDER.
        self.testcase_dir = tc_dir
        self.node_type = node_type
        self.node_value = node_value
        self.perform_action_obj = Perform_actions(HOSTNAME_PLACEHOLDER)
        HOSTNAME_PLACEHOLDER(
            "CNOM initialized; driver set with testcase directory: %s",
            self.testcase_dir,
        )
        return status

    @keyword("Select Node Alarm")
    def Select_Node_alarm(self, node_type, node_value, page):
        if not hasattr(self, "driver") or HOSTNAME_PLACEHOLDER is None:
            raise Exception(
                "Driver is not initialized. Please call the 'Initialize CNOM' keyword on this library instance before using 'Select Node'."
            )
        perform_action_obj = Perform_actions(HOSTNAME_PLACEHOLDER)
        cell_value, TB_value = "-1", "-1"

        if node_type == "PCC-MM":
            cell_value = "4"
            if node_value == "EAMFTB1":
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
            cell_value = "7"
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

        text_field_js_path = (
            'HOSTNAME_PLACEHOLDER("body > eui-container").querySelector("main > div > div > HOSTNAME_PLACEHOLDER > '
            'e-alarm-viewer").querySelector("e-cnom-lib-tree-view-flyout").querySelector('
            '"eui-flyout-panel > div:nth-child(1) > e-cnom-lib-tree-view-widget").querySelector('
            '"e-cnom-lib-tree-view").querySelector("eui-text-field").querySelector("#item")'
        )
        current_js_path = (
            'HOSTNAME_PLACEHOLDER("body > eui-container").querySelector("main > div > div > HOSTNAME_PLACEHOLDER > '
            + page
            + '").querySelector("e-cnom-lib-tree-view-flyout").querySelector('
            '"eui-flyout-panel > div:nth-child(1) > e-cnom-lib-tree-view-widget").querySelector('
            '"e-cnom-lib-tree-view").querySelector("eui-tree > e-tree-view-item:nth-child(3) > '
            "e-tree-view-item:nth-child("
            + cell_value
            + ") > e-tree-view-item:nth-child("
            + TB_value
            + ')").querySelector("li > span")'
        )
        select_btn = (
            'HOSTNAME_PLACEHOLDER("body > eui-container").querySelector("main > div > div > HOSTNAME_PLACEHOLDER > '
            'e-alarm-viewer").querySelector("e-cnom-lib-tree-view-flyout").querySelector('
            '"eui-flyout-panel > HOSTNAME_PLACEHOLDER > e-cnom-lib-button-group > eui-button:nth-child(3)")'
        )

        Action_list = [["send_keys", node_type], ["click", None], ["click", None]]
        for indx, path in enumerate([text_field_js_path, current_js_path, select_btn]):
            action, param_val = Action_list[indx]
            perform_action_obj.perform_action(path, action, param_val)
            HOSTNAME_PLACEHOLDER(1)
           # HOSTNAME_PLACEHOLDER("Performed action number: " + str(indx + 1))

        return cell_value, TB_value

    @keyword("Perform Alarm Activity Check")
    def Perform_Alarm_activity_check(self):
        """
        Performs alarm activity check by navigating to Alarm Viewer,
        selecting node, and validating alarm summary data.
        """
        HOSTNAME_PLACEHOLDER("Starting Alarm Activity Check")

        try:
            HOSTNAME_PLACEHOLDER(1)

            # Navigate to Alarm Viewer
            HOSTNAME_PLACEHOLDER("Navigating to Alarm Viewer")
            WebDriverWait(HOSTNAME_PLACEHOLDER, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[@test='Alarm Viewer']"))
            ).click()

            page = "e-alarm-viewer"
            HOSTNAME_PLACEHOLDER(1)

            # Select node for alarm monitoring
            HOSTNAME_PLACEHOLDER(f"Selecting node for alarm monitoring - Type: {self.node_type}, Value: {self.node_value}")
            self.Select_Node_alarm(self.node_type, self.node_value, page)

            # Extract alarm summary data
            HOSTNAME_PLACEHOLDER("Extracting alarm summary data using JavaScript")
            Alarm_summary_js = (
                'HOSTNAME_PLACEHOLDER("body > eui-container").querySelector("main > div > div > HOSTNAME_PLACEHOLDER > '
                'e-alarm-viewer").querySelector("div > e-cnom-lib-dashboard").querySelector("#builtin-standalone-common-alarm\\:alarm_summary")'
            )
            self.perform_action_obj = Perform_actions(HOSTNAME_PLACEHOLDER)
            summary_text = self.perform_action_obj.perform_action(
                Alarm_summary_js, "grab_text"
            )
            HOSTNAME_PLACEHOLDER("Alarm summary: %s", " | ".join(summary_text.splitlines()))

            HOSTNAME_PLACEHOLDER(2)

            # Capture screenshot of alarm summary
            Directory = self.testcase_dir
            screenshot_path = Directory + "/Alarm_summary.png"
            HOSTNAME_PLACEHOLDER(f"Capturing alarm summary screenshot: {screenshot_path}")
            HOSTNAME_PLACEHOLDER.save_screenshot(screenshot_path)

            # Validate alarm data presence
            if "No data" in summary_text:
                HOSTNAME_PLACEHOLDER("No alarm data found in summary ")
                return False
            else:
                HOSTNAME_PLACEHOLDER("Alarm data is present")
                return True

        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Alarm Activity Check failed: {str(e)}")
            raise

    @keyword("Validate Alarm List Widget")
    def validate_alarm_list_widget(self):
        """
        Validates alarm list widget by checking timestamp formats,
        alarm details, and downloading alarm data.
        """
        HOSTNAME_PLACEHOLDER("Starting Alarm List Widget validation")

        try:
            # Extract alarm dates from table
            HOSTNAME_PLACEHOLDER("Extracting alarm dates from table using JavaScript")
            alarm_list_js = (
                'const spans = HOSTNAME_PLACEHOLDER("body > eui-container").shadowRoot'
                '.querySelector("main > div > div > div:nth-child(2) > e-alarm-viewer").shadowRoot'
                '.querySelector("div > e-cnom-lib-dashboard").shadowRoot'
                '.querySelector("div > e-cnom-lib-table-widget > div:first-child > e-cnom-lib-table").shadowRoot'
                '.querySelector("div:nth-child(2) > e-cnom-internal-extended-table").shadowRoot'
                '.querySelectorAll("div > div > table > tbody > tr > td > div > span");'
                "return HOSTNAME_PLACEHOLDER(spans)"
                ".filter(span => /^\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}\\.\\d{3}/.test(HOSTNAME_PLACEHOLDER))"
                ".map(span => HOSTNAME_PLACEHOLDER);"
            )
            alarm_table_dates = HOSTNAME_PLACEHOLDER.execute_script(alarm_list_js)

            if not alarm_table_dates:
                HOSTNAME_PLACEHOLDER("No dates retrieved from alarm list table")
                raise Exception("No dates retrieved from alarm list table.")

            HOSTNAME_PLACEHOLDER("Alarm List Dates: " + str(alarm_table_dates))

            # Validate timestamp format and alarm details
            HOSTNAME_PLACEHOLDER("Validating timestamp formats for all alarms")
            timestamp_regex = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}:\d+S$")

            for date in alarm_table_dates:
                # Remove " (X seconds/days/months ago)" if present
                clean_date = HOSTNAME_PLACEHOLDER(" (")[0].strip()
                try:
                    # Convert timestamp to required format
                    dt = HOSTNAME_PLACEHOLDER(clean_date, "%Y-%m-%d %H:%M:%S.%f")
                    converted_timestamp = dt.strftime("%Y-%m-%d %H-%M-%S:%fS")
                except ValueError:
                    HOSTNAME_PLACEHOLDER(f"Unable to parse timestamp: {clean_date}")
                    raise Exception(f"Unable to parse timestamp: {clean_date}")

                if not timestamp_regex.match(converted_timestamp):
                    HOSTNAME_PLACEHOLDER(f"Incorrect timestamp format: {converted_timestamp}")
                    raise Exception(f"Incorrect timestamp format: {converted_timestamp}")

            HOSTNAME_PLACEHOLDER("All alarm timestamps validated successfully")

            HOSTNAME_PLACEHOLDER(2)

            # Download alarm data
            HOSTNAME_PLACEHOLDER("Downloading alarm data")
            Download_alarm_data_button_ele = find_element_with_shadow_xpath(
                HOSTNAME_PLACEHOLDER,
                "LOCAL_PATH_PLACEHOLDER:nth-of-type(2)LOCAL_PATH_PLACEHOLDER",
            )
            Download_alarm_data_button_ele.click()
            HOSTNAME_PLACEHOLDER(2)

            HOSTNAME_PLACEHOLDER("Alarm data downloaded successfully")
            return True

        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Alarm List Widget validation failed: {str(e)}")
            raise

    @keyword("Close Driver")
    def Close_driver(self):
        """
        Closes the WebDriver instance.
        """
        HOSTNAME_PLACEHOLDER("Closing WebDriver")
        HOSTNAME_PLACEHOLDER()
        HOSTNAME_PLACEHOLDER("WebDriver closed successfully")
