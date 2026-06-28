import os
import logging
from datetime import datetime
from pathlib import Path


class SOURCE_NAME_PLACEHOLDER:
    def __init__(self, test_data, cd=True, homedir=None):
        HOSTNAME_PLACEHOLDER(test_data)
        self.test_data = test_data
        self.tc_identifier = self.test_data["identifier"]
        self.tc_output_dir = self.test_data["tc_output_dir"]
        current_time = HOSTNAME_PLACEHOLDER()
        self.original_dir = os.getcwd()
        if cd:
            if homedir:
                os.chdir(homedir)

            HOSTNAME_PLACEHOLDER = (
                os.getcwd()
                + "/"
                + self.tc_identifier
                + "_"
                + current_time.strftime("%Y_%m_%d_%H_%M_%S")
            )
            HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER)
            os.mkdir(HOSTNAME_PLACEHOLDER)

            # return to original directory
            os.chdir(self.original_dir)
            # HOSTNAME_PLACEHOLDER("Current dir: " + os.getcwd())
        else:
            HOSTNAME_PLACEHOLDER = os.getcwd()

    def get_testcase_info(self):
        return {
            "identifier": self.tc_identifier,
            "tc_dir": HOSTNAME_PLACEHOLDER,
            "tc_output_dir": self.tc_output_dir,
        }

    def get_devices_info(self):
        return self.test_data["teststeps"]["execution"]["SOURCE_NAME_PLACEHOLDER"]["devices"]

    def get_call_duration(self):
        return self.test_data["teststeps"]["execution"]["SOURCE_NAME_PLACEHOLDER"]["call_duration"]

    def get_trace_inputs(self):
        self.trace_inputs = self.test_data["teststeps"]["tracing"]["Anritsu"]
        return self.trace_inputs

    def get_pcap_vlaidation(self):
        self.trace_inputs = self.test_data["teststeps"]["validation"]["pcap"]
        return self.trace_inputs

    def get_sipp_info(self):
        return self.test_data["teststeps"]["execution"]["sipp"]

    def get_mrf_validation(self):
        return self.test_data["teststeps"]["validation"]["mrf"]

    def get_vnf_info(self):
        return self.test_data["teststeps"]["execution"]["VNF"]

    def get_vnf_val(self):
        return self.test_data["teststeps"]["validation"]["VNF"]

    def get_cms_info(self):
        return self.test_data["teststeps"]["execution"]["CMS"]

    def get_lbs_info(self):
        return self.test_data["teststeps"]["execution"]["lbs"]
