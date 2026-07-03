import os
import logging
from datetime import datetime
from pathlib import Path


class SOURCE_NAME_PLACEHOLDER:
    def __init__(self, test_data, cd=True, homedir=None):
        self.test_data = test_data
        self.tc_tms_id = self.test_data["tmsid"]
        self.tc_output_dir = self.test_data["tc_output_dir"]
        current_time = HOSTNAME_PLACEHOLDER()
        self.original_dir = os.getcwd()
        if cd:
            if homedir:
                os.chdir(homedir)

            HOSTNAME_PLACEHOLDER = (
                os.getcwd()
                + "/"
                + self.tc_tms_id
                + "_"
                + current_time.strftime("%Y_%m_%d_%H_%M_%S")
            )
            HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER)
            os.mkdir(HOSTNAME_PLACEHOLDER)

            # return to original directory
            os.chdir(self.original_dir)
            HOSTNAME_PLACEHOLDER("Current dir: " + os.getcwd())
        else:
            HOSTNAME_PLACEHOLDER = os.getcwd()

    def get_testcase_info(self):
        return {
            "tmsid": self.tc_tms_id,
            "tc_dir": HOSTNAME_PLACEHOLDER,
            "tc_output_dir": self.tc_output_dir,
        }

    def get_trace_inputs(self):
        self.trace_inputs = self.test_data["teststeps"]["tracing"]["CNOM"]
        return self.trace_inputs

    def get_mc_inputs(self):
        self.mc_inputs = self.test_data["teststeps"]["execution"]["SOURCE_NAME_PLACEHOLDER"]
        return self.mc_inputs["DEVICE_ID"], self.mc_inputs["sleep_duration"]

    def get_SOURCE_NAME_PLACEHOLDER_inputs(self):
        self.SOURCE_NAME_PLACEHOLDER_inputs = self.test_data["teststeps"]["execution"]["SOURCE_NAME_PLACEHOLDER"]
        return self.SOURCE_NAME_PLACEHOLDER_inputs

    def get_pcap_validation_inputs(self):
        self.validation_inputs = self.test_data["teststeps"]["validation"]["pcap"][
            "messages"
        ]
        self.dynamic_test_data = self.test_data["teststeps"]["validation"]["pcap"][
            "dynamicfields"
        ]
        self.pcap_filter = self.test_data["teststeps"]["validation"]["pcap"]["filter"]
        return self.validation_inputs, self.dynamic_test_data, self.pcap_filter

    def get_cdr_validation_inputs(self):
        self.cdr_search_field = self.test_data["teststeps"]["validation"]["cdr"][
            "search_field"
        ]
        self.cdr_validation_inputs = self.test_data["teststeps"]["validation"]["cdr"][
            "fields"
        ]
        self.cdr_dynamicfields = self.test_data["teststeps"]["validation"]["cdr"][
            "dynamicfields"
        ]
        self.cdr_remote_folder = self.test_data["teststeps"]["validation"]["cdr"][
            "cdr_folder"
        ]
        return (
            self.cdr_validation_inputs,
            self.cdr_dynamicfields,
            self.cdr_remote_folder,
            self.cdr_search_field,
        )

    def get_enm_cli_inputs(self):
        self.cli_commands = self.test_data["teststeps"]["execution"]["commands"]
        return self.cli_commands

    def get_cdr_exp_val_inputs(self):
        self.number_of_days_cgs = self.test_data["teststeps"]["validation"][
            "number_of_days_cgs"
        ]
        self.backup_cdr_file_path = self.test_data["teststeps"]["execution"][
            "back_up_file_path"
        ]
        return self.backup_cdr_file_path, self.number_of_days_cgs

    def get_cnom_inputs(self):
        self.cnom_inputs = self.test_data["teststeps"]["tracing"]["CNOM"]
        return self.cnom_inputs["IMSI"], self.cnom_inputs["Description"]

    def get_basic_events(self):
        self.event_type = self.test_data["teststeps"]["validation"]["basic_events"]
        return self.event_type

    def get_event_type_validation_results(self):
        self.event_type = self.test_data["teststeps"]["validation"]["Event types"]
        return self.event_type

    def get_imsi_anritsu(self):
        self.mc_inputs = self.test_data["teststeps"]["tracing"]["ANRITSU"]
        return self.mc_inputs["IMSI"]

    def get_imsi_cnom(self):
        self.mc_inputs = self.test_data["teststeps"]["tracing"]["CNOM"]
        return self.mc_inputs["IMSI"]

    def get_anritsu_inputs(self):
        self.anritsu_inputs = self.test_data["teststeps"]["tracing"]["ANRITSU"]
        return self.anritsu_inputs

    def get_apn_names_list(self):
        apn_list = self.test_data["teststeps"]["validation"]["pcap"][
            "access point names"
        ]
        return apn_list

    def get_cdr_number(self):
        self.mc_inputs = self.test_data["teststeps"]["validation"]["cdr"]
        return self.mc_inputs["cdrnumber"]

    def get_cdr_folder(self):
        self.mc_inputs = self.test_data["teststeps"]["validation"]["cdr"]
        return self.mc_inputs["cdr_folder"]

    def get_SMFTB_inputs(self):
        self.SMFTB_inputs = self.test_data["teststeps"]["validation"]["SMFTB"]
        return self.SMFTB_inputs

    def get_pgw_validation_inputs(self):
        self.pgw_validation_inputs = self.test_data["teststeps"]["validation"][
            "PGW_fields"
        ]
        return self.pgw_validation_inputs

    def get_pcap_validation_messages(self, message_key):
        all_messages = self.test_data["teststeps"]["validation"]["pcap"]["messages"]
        for msg in all_messages:
            if msg["name"] == message_key:
                return msg

    def get_pcap_download(self):
        #self.SOURCE_NAME_PLACEHOLDER_inputs = self.test_data["teststeps"]["pcap_download"]["PATTERN"]
        return self.test_data["teststeps"]["pcap_download"]

    def get_cmg_commands(self):
        return self.test_data["teststeps"]["execution"]["cmg_commands"]

    def get_cmg_console_fields(self):
        return self.test_data ["teststeps"]["validation"]["console_output"]

    def get_cmg_ports(self):
        return self.test_data["teststeps"]["execution"]["Ports"]
