from HOSTNAME_PLACEHOLDER import WebDriverWait
from HOSTNAME_PLACEHOLDER import expected_conditions as EC
import time
import logging
from HOSTNAME_PLACEHOLDER import By
from SOURCE_NAME_PLACEHOLDER import Perform_actions
from SOURCE_NAME_PLACEHOLDER import SOURCE_NAME_PLACEHOLDER
from HOSTNAME_PLACEHOLDER.action_chains import ActionChains
from HOSTNAME_PLACEHOLDER import keyword
from SOURCE_NAME_PLACEHOLDER import (
    eleclick,
    ele_presence,
)
from HOSTNAME_PLACEHOLDER import Keys


class SOURCE_NAME_PLACEHOLDER(SOURCE_NAME_PLACEHOLDER):
    def __init__(self, cnom_conn_params=None, node_type=None, node_value=None):
        super().__init__(cnom_conn_params)
        self.node_type = node_type
        self.node_value = node_value
        HOSTNAME_PLACEHOLDER("SOURCE_NAME_PLACEHOLDER loaded successfully.")


# === Utility Functions ===
    def Collect_data_SGSN_MME_node(self, output_dir):
        """Collect data from SGSN MME node including monitoring status, logs, traffic usage, comparisons and events"""
        HOSTNAME_PLACEHOLDER("Starting SGSN MME node data collection...")
        HOSTNAME_PLACEHOLDER(10)
        
        # Check Monitoring Status
        HOSTNAME_PLACEHOLDER("Checking monitoring status...")
        Status = 'HOSTNAME_PLACEHOLDER("body > eui-container").HOSTNAME_PLACEHOLDER("main > div > div > div:nth-child(2) > e-status-overview").HOSTNAME_PLACEHOLDER("div > e-cnom-lib-dashboard").HOSTNAME_PLACEHOLDER("div > e-cnom-lib-table-widget:nth-child(1) > div:nth-child(1) > e-cnom-lib-table").HOSTNAME_PLACEHOLDER("div:nth-child(2) > e-cnom-internal-extended-table").HOSTNAME_PLACEHOLDER("div > div > table > tbody > tr:nth-child(1) > td:nth-child(2) > div > span")'
        Monitoring_status = self.perform_action_obj.perform_action(Status, 'grab_text')
        HOSTNAME_PLACEHOLDER(f'Monitoring status: {Monitoring_status}')

        if "STARTED" in Monitoring_status:
            HOSTNAME_PLACEHOLDER("✓ Node is up and running")
            
            # Overview Screenshot
            HOSTNAME_PLACEHOLDER(1)
            HOSTNAME_PLACEHOLDER.save_screenshot(output_dir + '/Monitoring_status_overview.png')
            HOSTNAME_PLACEHOLDER(f"✓ Monitoring status overview screenshot saved to: {output_dir}/Monitoring_status_overview.png")

            # Logs Section
            HOSTNAME_PLACEHOLDER(1)
            HOSTNAME_PLACEHOLDER("Switching to Logs tab...")
            SGW_C_menu_tab_btn = 'HOSTNAME_PLACEHOLDER("body > eui-container").HOSTNAME_PLACEHOLDER("main > div > div > HOSTNAME_PLACEHOLDER > e-status-overview").HOSTNAME_PLACEHOLDER("div > div > span > eui-tabs > eui-tab:nth-child(2)")'
            self.perform_action_obj.perform_action(SGW_C_menu_tab_btn, 'click')
            
            HOSTNAME_PLACEHOLDER("Collecting log entries...")
            logs = []
            for cell in range(1, 11):
                try:
                    logs_xpath = f'HOSTNAME_PLACEHOLDER("html > body > eui-container").HOSTNAME_PLACEHOLDER("main > div > div > div:nth-child(2) > e-status-overview").HOSTNAME_PLACEHOLDER("div > e-cnom-lib-dashboard").HOSTNAME_PLACEHOLDER("div > e-cnom-lib-table-widget > div:nth-child(1) > e-cnom-lib-table").HOSTNAME_PLACEHOLDER("div:nth-child(2) > e-cnom-internal-extended-table").HOSTNAME_PLACEHOLDER("div > div > table > tbody > tr:nth-child({cell}) > td:nth-child(1) > div > span")'
                    log = self.perform_action_obj.perform_action(logs_xpath, 'grab_text')
                    if log and HOSTNAME_PLACEHOLDER():
                        HOSTNAME_PLACEHOLDER(log)
                except Exception as e:
                    HOSTNAME_PLACEHOLDER(f"Could not retrieve log entry {cell}: {e}")
                    break
                    
            HOSTNAME_PLACEHOLDER(f"✓ Found {len(logs)} log entries:")
            for i, log in enumerate(logs, 1):
                HOSTNAME_PLACEHOLDER(f"  {i}. {log}")
            
            HOSTNAME_PLACEHOLDER.save_screenshot(output_dir + '/HOSTNAME_PLACEHOLDER')
            HOSTNAME_PLACEHOLDER(f"✓ Logs screenshot saved to: {output_dir}/HOSTNAME_PLACEHOLDER")
            
            # SGSN-G Traffic Usage
            HOSTNAME_PLACEHOLDER(1)
            HOSTNAME_PLACEHOLDER("Switching to SGSN-G Traffic Usage tab...")
            PGW_C_menu_tab_btn = 'HOSTNAME_PLACEHOLDER("body > eui-container").HOSTNAME_PLACEHOLDER("main > div > div > HOSTNAME_PLACEHOLDER > e-status-overview").HOSTNAME_PLACEHOLDER("div > div > span > eui-tabs > eui-tab:nth-child(3)")'
            self.perform_action_obj.perform_action(PGW_C_menu_tab_btn, 'click')
            HOSTNAME_PLACEHOLDER.save_screenshot(output_dir + '/SGSN-G_Traffic_usage.png')
            HOSTNAME_PLACEHOLDER(f"✓ SGSN-G Traffic Usage screenshot saved to: {output_dir}/SGSN-G_Traffic_usage.png")

            # SGSN-W Traffic Usage
            HOSTNAME_PLACEHOLDER(1)
            HOSTNAME_PLACEHOLDER("Switching to SGSN-W Traffic Usage tab...")
            SMF_menu_tab_btn = 'HOSTNAME_PLACEHOLDER("body > eui-container").HOSTNAME_PLACEHOLDER("main > div > div > HOSTNAME_PLACEHOLDER > e-status-overview").HOSTNAME_PLACEHOLDER("div > div > span > eui-tabs > eui-tab:nth-child(4)")'
            self.perform_action_obj.perform_action(SMF_menu_tab_btn, 'click')
            HOSTNAME_PLACEHOLDER.save_screenshot(output_dir + '/SGSN-W_Traffic_usage.png')
            HOSTNAME_PLACEHOLDER(f"✓ SGSN-W Traffic Usage screenshot saved to: {output_dir}/SGSN-W_Traffic_usage.png")
            
            # Table Comparison
            HOSTNAME_PLACEHOLDER(1)
            HOSTNAME_PLACEHOLDER("Switching to Table Comparison tab...")
            Table_Comparision_menu_tab = 'HOSTNAME_PLACEHOLDER("body > eui-container").HOSTNAME_PLACEHOLDER("main > div > div > HOSTNAME_PLACEHOLDER > e-status-overview").HOSTNAME_PLACEHOLDER("div > div > span > eui-tabs > eui-tab:nth-child(5)")'
            self.perform_action_obj.perform_action(Table_Comparision_menu_tab, 'click')
            HOSTNAME_PLACEHOLDER.save_screenshot(output_dir + '/Table_Comparison.png')
            HOSTNAME_PLACEHOLDER(f"✓ Table Comparison screenshot saved to: {output_dir}/Table_Comparison.png")
            
            # Graph Comparison
            HOSTNAME_PLACEHOLDER(1)
            HOSTNAME_PLACEHOLDER("Switching to Graph Comparison tab...")
            graph_Comparision_menu_tab = 'HOSTNAME_PLACEHOLDER("body > eui-container").HOSTNAME_PLACEHOLDER("main > div > div > HOSTNAME_PLACEHOLDER > e-status-overview").HOSTNAME_PLACEHOLDER("div > div > span > eui-tabs > eui-tab:nth-child(6)")'
            self.perform_action_obj.perform_action(graph_Comparision_menu_tab, 'click')
            HOSTNAME_PLACEHOLDER(3)
            HOSTNAME_PLACEHOLDER.save_screenshot(output_dir + '/Graph_Comparison.png')
            HOSTNAME_PLACEHOLDER(f"✓ Graph Comparison screenshot saved to: {output_dir}/Graph_Comparison.png")

            # Events Section
            HOSTNAME_PLACEHOLDER("Switching to Events tab...")
            event_menu_tab = 'HOSTNAME_PLACEHOLDER("body > eui-container").HOSTNAME_PLACEHOLDER("main > div > div > HOSTNAME_PLACEHOLDER > e-status-overview").HOSTNAME_PLACEHOLDER("div > div > span > eui-tabs > eui-tab:nth-child(7)")'
            self.perform_action_obj.perform_action(event_menu_tab, 'click')
            HOSTNAME_PLACEHOLDER(2)  # Allow tab to load
            
            HOSTNAME_PLACEHOLDER("Collecting event data...")
            Events = []
            
            # Use a simpler approach - try to collect events until we can't find more
            for cell in range(1, 11):
                try:
                    events_xpath = f'HOSTNAME_PLACEHOLDER("html > body > eui-container").HOSTNAME_PLACEHOLDER("main > div > div > div:nth-child(2) > e-status-overview").HOSTNAME_PLACEHOLDER("div > e-cnom-lib-dashboard").HOSTNAME_PLACEHOLDER("div > e-cnom-lib-table-widget > div:nth-child(1) > e-cnom-lib-table").HOSTNAME_PLACEHOLDER("div:nth-child(2) > e-cnom-internal-extended-table").HOSTNAME_PLACEHOLDER("div > div > table > tbody > tr:nth-child({cell}) > td:nth-child(2) > div > span")'               
                    event = self.perform_action_obj.perform_action(events_xpath, 'grab_text')
                    if event and HOSTNAME_PLACEHOLDER():
                        HOSTNAME_PLACEHOLDER(event)
                    else:
                        HOSTNAME_PLACEHOLDER(f"Empty event at row {cell}, continuing...")
                except Exception as e:
                    HOSTNAME_PLACEHOLDER(f"No more events found after row {cell-1}")
                    break
            
            if Events:
                HOSTNAME_PLACEHOLDER(f"✓ Detected events are:")
                for i, event in enumerate(Events, 1):
                    HOSTNAME_PLACEHOLDER(f"  {i}. {event}")
            else:
                HOSTNAME_PLACEHOLDER("No events detected in the table")
                
            HOSTNAME_PLACEHOLDER.save_screenshot(output_dir + '/HOSTNAME_PLACEHOLDER')
            HOSTNAME_PLACEHOLDER(f"✓ Events screenshot saved to: {output_dir}/HOSTNAME_PLACEHOLDER")
            
            HOSTNAME_PLACEHOLDER("✓ SGSN MME node data collection completed successfully")
            return True

        elif "START ERROR" in Monitoring_status:
            HOSTNAME_PLACEHOLDER(f"✗ The monitoring status is '{Monitoring_status}'. Test case failed.")
            HOSTNAME_PLACEHOLDER.save_screenshot(output_dir + '/Monitoring_status_error.png')
            HOSTNAME_PLACEHOLDER(f"Error screenshot saved to: {output_dir}/Monitoring_status_error.png")
            return False
        
        else:
            HOSTNAME_PLACEHOLDER(f"⚠ Unexpected monitoring status: '{Monitoring_status}'")
            HOSTNAME_PLACEHOLDER.save_screenshot(output_dir + '/Monitoring_status_unexpected.png')
            HOSTNAME_PLACEHOLDER(f"Unexpected status screenshot saved to: {output_dir}/Monitoring_status_unexpected.png")
            return False
        
    
    def Collect_data_WMG_node(self, output_dir):
        """Collect data from WMG node including monitoring status, logs, traffic usage, comparisons and events"""
        HOSTNAME_PLACEHOLDER("Starting WMG node data collection...")
        HOSTNAME_PLACEHOLDER(10)
        
        # Check Monitoring Status
        HOSTNAME_PLACEHOLDER("Checking monitoring status...")
        Status = 'HOSTNAME_PLACEHOLDER("body > eui-container").HOSTNAME_PLACEHOLDER("main > div > div > div:nth-child(2) > e-status-overview").HOSTNAME_PLACEHOLDER("div > e-cnom-lib-dashboard").HOSTNAME_PLACEHOLDER("div > e-cnom-lib-table-widget:nth-child(1) > div:nth-child(1) > e-cnom-lib-table").HOSTNAME_PLACEHOLDER("div:nth-child(2) > e-cnom-internal-extended-table").HOSTNAME_PLACEHOLDER("div > div > table > tbody > tr:nth-child(1) > td:nth-child(2) > div > span")'
        Monitoring_status = self.perform_action_obj.perform_action(Status, 'grab_text')
        HOSTNAME_PLACEHOLDER(f'Monitoring status: {Monitoring_status}')

        if "STARTED" in Monitoring_status:
            HOSTNAME_PLACEHOLDER("✓ Node is up and running")
            HOSTNAME_PLACEHOLDER(500)
            
            # Overview Screenshot
            HOSTNAME_PLACEHOLDER(1)
            HOSTNAME_PLACEHOLDER.save_screenshot(output_dir + '/Monitoring_status_overview.png')
            HOSTNAME_PLACEHOLDER(f"✓ Monitoring status overview screenshot saved to: {output_dir}/Monitoring_status_overview.png")

            # WMG Traffic Usage
            HOSTNAME_PLACEHOLDER(1)
            HOSTNAME_PLACEHOLDER("Switching to WMG Traffic Usage tab...")
            PGW_C_menu_tab_btn = 'HOSTNAME_PLACEHOLDER("body > eui-container").HOSTNAME_PLACEHOLDER("main > div > div > HOSTNAME_PLACEHOLDER > e-status-overview").HOSTNAME_PLACEHOLDER("div > div > span > eui-tabs > eui-tab:nth-child(2)")'
            self.perform_action_obj.perform_action(PGW_C_menu_tab_btn, 'click')
            HOSTNAME_PLACEHOLDER.save_screenshot(output_dir + '/SGSN-G_Traffic_usage.png')
            HOSTNAME_PLACEHOLDER(f"✓ SGSN-G Traffic Usage screenshot saved to: {output_dir}/SGSN-G_Traffic_usage.png")

            # Table Comparison
            HOSTNAME_PLACEHOLDER(1)
            HOSTNAME_PLACEHOLDER("Switching to Table Comparison tab...")
            Table_Comparision_menu_tab = 'HOSTNAME_PLACEHOLDER("body > eui-container").HOSTNAME_PLACEHOLDER("main > div > div > HOSTNAME_PLACEHOLDER > e-status-overview").HOSTNAME_PLACEHOLDER("div > div > span > eui-tabs > eui-tab:nth-child(3)")'
            self.perform_action_obj.perform_action(Table_Comparision_menu_tab, 'click')
            HOSTNAME_PLACEHOLDER.save_screenshot(output_dir + '/Table_Comparison.png')
            HOSTNAME_PLACEHOLDER(f"✓ Table Comparison screenshot saved to: {output_dir}/Table_Comparison.png")
            
            # Graph Comparison
            HOSTNAME_PLACEHOLDER(1)
            HOSTNAME_PLACEHOLDER("Switching to Graph Comparison tab...")
            graph_Comparision_menu_tab = 'HOSTNAME_PLACEHOLDER("body > eui-container").HOSTNAME_PLACEHOLDER("main > div > div > HOSTNAME_PLACEHOLDER > e-status-overview").HOSTNAME_PLACEHOLDER("div > div > span > eui-tabs > eui-tab:nth-child(4)")'
            self.perform_action_obj.perform_action(graph_Comparision_menu_tab, 'click')
            HOSTNAME_PLACEHOLDER(3)
            HOSTNAME_PLACEHOLDER.save_screenshot(output_dir + '/Graph_Comparison.png')
            HOSTNAME_PLACEHOLDER(f"✓ Graph Comparison screenshot saved to: {output_dir}/Graph_Comparison.png")

            # Events Section
            HOSTNAME_PLACEHOLDER("Switching to Events tab...")
            event_menu_tab = 'HOSTNAME_PLACEHOLDER("body > eui-container").HOSTNAME_PLACEHOLDER("main > div > div > HOSTNAME_PLACEHOLDER > e-status-overview").HOSTNAME_PLACEHOLDER("div > div > span > eui-tabs > eui-tab:nth-child(5)")'
            self.perform_action_obj.perform_action(event_menu_tab, 'click')
            HOSTNAME_PLACEHOLDER(2) 
            HOSTNAME_PLACEHOLDER("Collecting event data...")
            Events = []
            
            # try to collect events until we can't find more
            for cell in range(1, 11):
                try:
                    events_xpath = f'HOSTNAME_PLACEHOLDER("html > body > eui-container").HOSTNAME_PLACEHOLDER("main > div > div > div:nth-child(2) > e-status-overview").HOSTNAME_PLACEHOLDER("div > e-cnom-lib-dashboard").HOSTNAME_PLACEHOLDER("div > e-cnom-lib-table-widget > div:nth-child(1) > e-cnom-lib-table").HOSTNAME_PLACEHOLDER("div:nth-child(2) > e-cnom-internal-extended-table").HOSTNAME_PLACEHOLDER("div > div > table > tbody > tr:nth-child({cell}) > td:nth-child(2) > div > span")'               
                    event = self.perform_action_obj.perform_action(events_xpath, 'grab_text')
                    if event and HOSTNAME_PLACEHOLDER():
                        HOSTNAME_PLACEHOLDER(event)
                    else:
                        HOSTNAME_PLACEHOLDER(f"Empty event at row {cell}, continuing...")
                except Exception as e:
                    HOSTNAME_PLACEHOLDER(f"No more events found after row {cell-1}")
                    break
            
            if Events:
                HOSTNAME_PLACEHOLDER(f"✓ Detected events are:")
                for i, event in enumerate(Events, 1):
                    HOSTNAME_PLACEHOLDER(f"  {i}. {event}")
            else:
                HOSTNAME_PLACEHOLDER("No events detected in the table")
                
            HOSTNAME_PLACEHOLDER.save_screenshot(output_dir + '/HOSTNAME_PLACEHOLDER')
            HOSTNAME_PLACEHOLDER(f"✓ Events screenshot saved to: {output_dir}/HOSTNAME_PLACEHOLDER")
            
            HOSTNAME_PLACEHOLDER("✓ SGSN MME node data collection completed successfully")
            return True

        elif "START ERROR" in Monitoring_status:
            HOSTNAME_PLACEHOLDER(f"✗ The monitoring status is '{Monitoring_status}'. Test case failed.")
            HOSTNAME_PLACEHOLDER.save_screenshot(output_dir + '/Monitoring_status_error.png')
            HOSTNAME_PLACEHOLDER(f"Error screenshot saved to: {output_dir}/Monitoring_status_error.png")
            return False
        
        else:
            HOSTNAME_PLACEHOLDER(f"⚠ Unexpected monitoring status: '{Monitoring_status}'")
            HOSTNAME_PLACEHOLDER.save_screenshot(output_dir + '/Monitoring_status_unexpected.png')
            HOSTNAME_PLACEHOLDER(f"Unexpected status screenshot saved to: {output_dir}/Monitoring_status_unexpected.png")
            return False
        # ==================
        
        
# Main Functions
    def initialize_cnom(self, cnom_obj: any, testcase_name: str, node_type: str, node_value: str, tc_dir):
        """
        This function is required to initialize driver to perform action on CNOM server.
            :param cnom_obj:    Object of class CNOM_server
            :param testcase_name:   Required to build the directory for storing the logs.
            :param node_type:   Required to select the server to perform the operations on.
            :param node_value:  Required to select the node to perform the opertions on.
            :return:    None.
        """
        self.login_cnom_obj = cnom_obj
        status = self.initialize_driver(testcase_name, tc_dir)
        self.testcase_dir = tc_dir
        self.node_type = node_type
        self.node_value = node_value
        self.perform_action_obj = Perform_actions(HOSTNAME_PLACEHOLDER)
        HOSTNAME_PLACEHOLDER(
            "CNOM initialized; driver set with testcase directory: %s",
            self.testcase_dir,
        )
        return status

    @keyword("Select Node Monitoring")
    def Select_Node_Monitoring(self, node_value, node_type):
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
            else:
                raise ValueError(
                    f"Unknown node value '{node_value}' for node type '{node_type}'"
                )
        elif node_type == "EPG":
            cell_value = "2"
            if node_value == "EUPFTB6":
                TB_value = "1"
            elif node_value == "EUPFTB7":
                TB_value = "2"
            else:
                raise ValueError(
                    f"Unknown node value '{node_value}' for node type '{node_type}'"
                )
        elif node_type == "WMG":
            cell_value = "4"
            if node_value == "EEPDGTB1":
                TB_value = "1"
            elif node_value == "EEPDGTB2":
                TB_value = "2"
            else:
                raise ValueError(
                    f"Unknown node value '{node_value}' for node type '{node_type}'"
                )
        else:
            raise ValueError(
                f"Unknown node type '{node_type}'"
            )

        node_type_element = f"LOCAL_PATH_PLACEHOLDER[3]LOCAL_PATH_PLACEHOLDER[1]/div[4]LOCAL_PATH_PLACEHOLDER[1]LOCAL_PATH_PLACEHOLDER[2]LOCAL_PATH_PLACEHOLDER[{cell_value}]/div"

        node_value_element = f"LOCAL_PATH_PLACEHOLDER[3]LOCAL_PATH_PLACEHOLDER[1]/div[4]LOCAL_PATH_PLACEHOLDER[1]LOCAL_PATH_PLACEHOLDER[2]LOCAL_PATH_PLACEHOLDER[{cell_value}]LOCAL_PATH_PLACEHOLDER[{TB_value}]/div"

        eleclick(HOSTNAME_PLACEHOLDER, node_type_element,"Node Type")
        HOSTNAME_PLACEHOLDER(2)

        eleclick(HOSTNAME_PLACEHOLDER, node_value_element,"Node Value")
        HOSTNAME_PLACEHOLDER(f" {node_type} : {node_value} Selected ")

        return cell_value, TB_value

    @keyword("Perform PM Monitoring")
    def Preform_PM_Monitoring(self):
        """
        Performs PM (Performance Monitoring) operations including navigation,
        element verification, and screenshot capture for monitoring dashboard.
        """
        HOSTNAME_PLACEHOLDER("Starting PM Monitoring process")
        
        try:
            # Initial delay for page stabilization
            HOSTNAME_PLACEHOLDER("Waiting for page stabilization (1 second)")
            HOSTNAME_PLACEHOLDER(1)
            
            # Navigate to PM Monitor section
            HOSTNAME_PLACEHOLDER("Navigating to PM Monitor section")
            pm_monitor_element = WebDriverWait(HOSTNAME_PLACEHOLDER, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[@test='PM Monitor']"))
            )
            HOSTNAME_PLACEHOLDER("PM Monitor element located successfully")
            pm_monitor_element.click()
            
            # Select node for monitoring
            HOSTNAME_PLACEHOLDER(f"Selecting node for monitoring - Node: {self.node_value}, Type: {self.node_type}")
            self.Select_Node_Monitoring(self.node_value, self.node_type)
            HOSTNAME_PLACEHOLDER("Node selection completed")
            
            # Wait for monitoring data to load
            HOSTNAME_PLACEHOLDER("Waiting for monitoring data to load (10 seconds)")
            HOSTNAME_PLACEHOLDER(10)
            
            # Verify presence of Timeline of SGSN Nodes section
            Timeline_Of_SGSN_Nodes = "//h4[@class='elTimeline-title' and @e-id='title']"
            HOSTNAME_PLACEHOLDER("Verifying Timeline of SGSN Nodes section")
            ele_presence(HOSTNAME_PLACEHOLDER, Timeline_Of_SGSN_Nodes, "Timeline Of SGSN Nodes")
            HOSTNAME_PLACEHOLDER("Timeline of SGSN Nodes section verified successfully")
            
            # Verify CPU Load (APs) section
            CPU_loads_aps = "//h4[@class='elTimeline-title' and text()='CPU Load (APs)']"
            HOSTNAME_PLACEHOLDER("Verifying CPU Load (APs) section")
            ele_presence(HOSTNAME_PLACEHOLDER, CPU_loads_aps, "CPU loads(APS)")
            HOSTNAME_PLACEHOLDER("CPU Load (APs) section verified successfully")
            
            # Verify CPU Load (SS7/SCTP DPs) section
            CPU_loads_SS7_SCTPDPs = (
                "//h4[@class='elTimeline-title' and text()='CPU Load (Payload DPs)']"
            )
            HOSTNAME_PLACEHOLDER("Verifying CPU Load (SS7/SCTP DPs) section")
            ele_presence(HOSTNAME_PLACEHOLDER, CPU_loads_SS7_SCTPDPs, "CPU Load (SS7/SCTP DPs)")
            HOSTNAME_PLACEHOLDER("CPU Load (SS7/SCTP DPs) section verified successfully")
            
            # Verify CPU Load (Payload DPs) section
            CPU_loads_Payload_Dps = (
                "//h4[@class='elTimeline-title' and text()='CPU Load (Payload DPs)']"
            )
            HOSTNAME_PLACEHOLDER("Verifying CPU Load (Payload DPs) section")
            ele_presence(HOSTNAME_PLACEHOLDER, CPU_loads_Payload_Dps, "CPU Load (Payload DPs)")
            HOSTNAME_PLACEHOLDER("CPU Load (Payload DPs) section verified successfully")
            
            # Verify main CPU Load section
            CPU_Load = "//h3[@class='elLayouts-Dashboard-item-header elLayouts-Dashboard-item-header_draggable']/span[text()='CPU Load']"
            HOSTNAME_PLACEHOLDER("Verifying main CPU Load section")
            ele_presence(HOSTNAME_PLACEHOLDER, CPU_Load, "CPU Load")
            HOSTNAME_PLACEHOLDER("Main CPU Load section verified successfully")
            
            # Capture first screenshot of monitoring summary
            screenshot_path1 = self.testcase_dir + "/PM Monitoring _summary.png"
            HOSTNAME_PLACEHOLDER.save_screenshot(screenshot_path1)
            HOSTNAME_PLACEHOLDER("First screenshot captured successfully")
            
            actions = ActionChains(HOSTNAME_PLACEHOLDER)
            actions.send_keys(Keys.PAGE_DOWN).perform()
            HOSTNAME_PLACEHOLDER("Page scroll down executed")
            
            # Brief pause for scroll completion
            HOSTNAME_PLACEHOLDER("Waiting for scroll completion (2 seconds)")
            HOSTNAME_PLACEHOLDER(2)
            
            # Capture second screenshot after scrolling
            screenshot_path2 = self.testcase_dir + "/PM Monitoring _summary2.png"
            HOSTNAME_PLACEHOLDER(f"Capturing second screenshot: {screenshot_path2}")
            HOSTNAME_PLACEHOLDER.save_screenshot(screenshot_path2)
            HOSTNAME_PLACEHOLDER("Second screenshot captured successfully")
            
            HOSTNAME_PLACEHOLDER("PM Monitoring process completed successfully")
            return True
            
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"PM Monitoring process failed with error: {str(e)}")
            HOSTNAME_PLACEHOLDER("Full exception details:")
            raise

    @keyword("Monitor Network")
    def Monitor_network(self,trace_path,output_dir):
            HOSTNAME_PLACEHOLDER(1)
            eleclick(HOSTNAME_PLACEHOLDER,trace_path['Network Monitor'], "Network Monitor_Button" )
            HOSTNAME_PLACEHOLDER(f"Selecting node - Type: '{self.node_type}', Value: '{self.node_value}'")
            self.Select_Node_Monitoring(self.node_value,self.node_type)
            eleclick(HOSTNAME_PLACEHOLDER,trace_path['Apply'],"Apply Button")
            
            
            return self.Collect_data_SGSN_MME_node(output_dir)

    # ==================