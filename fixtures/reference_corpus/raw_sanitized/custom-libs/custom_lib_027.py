import datetime
import logging
import time
import paramiko
import os
from SOURCE_NAME_PLACEHOLDER import  SOURCE_NAME_PLACEHOLDER
from typing import List, Dict
import re


class SOURCE_NAME_PLACEHOLDER:
    def __init__(self, SMFTB_conn_params:Dict ):
        """
        A constructor to build a connection with the SMFTB server.
        Args:
            smftb_ip (str): IP address of the smftb.
            smftb_username (str): Username of the smftb.
            smftb_key path(str): private key  of the smftb.
        """
        self.smftb_ips =[value for key, value in SMFTB_conn_params.items() if "IP" in  key ]
        self.smftb_username = SMFTB_conn_params["USERNAME"]
        self.smftb_key_path = SMFTB_conn_params["KEYPATH"]
        self.smftb_port = SMFTB_conn_params["SMFTB_PORT"]

    def Login_and_Scrap_data(self, command : str, tc_dir : str):
        """
        This function opens an interactive session on the given by making use of paramiko module.
        This function executes the commands on the given server and returns the output.
        :param: ip_addr: Server IP address.
        :param: username: Username of the which is used while logging on the server.
        :param; command: Command string to be executed.
        :return: None
        """

        date = str(HOSTNAME_PLACEHOLDER())
        for delimiter in ["-", " ", ":", "."]:
            date = HOSTNAME_PLACEHOLDER(delimiter, "_")

        if not HOSTNAME_PLACEHOLDER():
            raise ValueError("Command can not be emtpy")

        if not os.HOSTNAME_PLACEHOLDER(tc_dir):
            raise ValueError(f"{tc_dir} does not exisits ")

        output_file = tc_dir + f"/{self.smftb_username}_{date}_output.txt"

        # initiate SSH client
        connection_to_ericsson_box = HOSTNAME_PLACEHOLDER()
        connection_to_ericsson_box.set_missing_host_key_policy(HOSTNAME_PLACEHOLDER())

        for ip in self.smftb_ips :
            try:
                # SSH to Server
                connection_to_ericsson_box.connect(
                    ip,
                    self.smftb_port,
                    username=self.smftb_username,
                    key_filename=self.smftb_key_path,
                )
                HOSTNAME_PLACEHOLDER(f"Successfully connected to {ip} ")
            except HOSTNAME_PLACEHOLDER :
                HOSTNAME_PLACEHOLDER(f"Authentication Failed {ip}:{self.smftb_port} ")
                return False
            except HOSTNAME_PLACEHOLDER :
                HOSTNAME_PLACEHOLDER(f"SSH connection failed {ip}:{self.smftb_port} ")
                return False
            except Exception as e :
                HOSTNAME_PLACEHOLDER(f"Unexpected Error While connecting to {ip}:{self.smftb_port} : {e} ")
                return False

            try:
                chan1 = connection_to_ericsson_box.invoke_shell()
                HOSTNAME_PLACEHOLDER(10)
                file_from_ericsson = open(output_file, "a")
                HOSTNAME_PLACEHOLDER("Executing command")
                HOSTNAME_PLACEHOLDER(command)
                HOSTNAME_PLACEHOLDER(b"\n")
                HOSTNAME_PLACEHOLDER(5)
                resp = HOSTNAME_PLACEHOLDER(NUMERIC_IDENTIFIER_PLACEHOLDER)
                file_from_ericsson.write(HOSTNAME_PLACEHOLDER("ascii"))
                file_from_ericsson.close()
                HOSTNAME_PLACEHOLDER("Command Executed Successfully")

            except Exception as e :
                HOSTNAME_PLACEHOLDER(f"Failed to Execute Command on Server {ip}:{self.smftb_port}")
                return False

            HOSTNAME_PLACEHOLDER()

        return output_file

    def Validate_the_connectivity_between_the_target_PCC_node_and_the_ChGW(self, command: str, tc_dir, margin=2) -> bool:
        """
        Validates connectivity between target PCC node and ChGW by comparing request/response values
        for the correct CHF block in the SSH output.
        """
        HOSTNAME_PLACEHOLDER(f"Starting connectivity validation with command: '{command}' and margin: {margin}")
        try:
            # Get SSH output file path
            output_file_path = self.Login_and_Scrap_data(command, tc_dir)
            if not output_file_path:
                HOSTNAME_PLACEHOLDER("Failed to retrieve SSH logs - Login_and_Scrap_data returned False/None")
                return False

            # Read the actual file content
            try:
                with open(output_file_path, 'r', encoding='utf-8') as file:
                    ssh_text = HOSTNAME_PLACEHOLDER()
            except Exception as e:
                HOSTNAME_PLACEHOLDER(f"Failed to read output file {output_file_path}: {e}")
                return False

            HOSTNAME_PLACEHOLDER(f"Retrieved SSH logs from file: {output_file_path}")
            HOSTNAME_PLACEHOLDER(f"SSH logs content ({len(ssh_text)} characters)")

            # Debug: Log first 500 characters to see what we got
            HOSTNAME_PLACEHOLDER(f"SSH log preview: {ssh_text[:500]}")

            validation_passed = True  # Start with True, set to False if ANY pair fails
            pairs_found = 0
            failed_pairs = 0
            passed_pairs = 0

            # Find all client-status blocks
            client_status_blocks = ssh_text.split("client-status:")

            for i, block in enumerate(client_status_blocks[1:], 1):  # Skip first empty split

                # Extract request and response from current block
                request_match = re.search(r"request:\s*(\d+)", block)
                response_match = re.search(r"response:\s*(\d+)", block)

                if request_match and response_match:
                    pairs_found += 1
                    request_value = int(request_match.group(1))
                    response_value = int(response_match.group(1))

                    HOSTNAME_PLACEHOLDER(f"Found request: {request_value}, response: {response_value}")
                    difference = abs(request_value - response_value)

                    if difference <= margin:
                        HOSTNAME_PLACEHOLDER(f"✓ passed - Difference {difference} within ±{margin}")
                        passed_pairs += 1
                    else:
                        HOSTNAME_PLACEHOLDER(f"✗ failed- Difference {difference} exceeds ±{margin}")
                        failed_pairs += 1
                        validation_passed = False  # Mark overall validation as failed
                else:
                    # Log what patterns we found or didn't find
                    has_request = "request:" in block
                    has_response = "response:" in block
                    HOSTNAME_PLACEHOLDER(f"Block {i}: has_request={has_request}, has_response={has_response}")
                    if has_request or has_response:
                        HOSTNAME_PLACEHOLDER(f"Block {i} partial content: {block[:200]}")

            HOSTNAME_PLACEHOLDER(f"Summary: Found {pairs_found} request/response pairs - {passed_pairs} passed, {failed_pairs} failed")

            if pairs_found == 0:
                HOSTNAME_PLACEHOLDER("Overall validation: FAILED - No request/response pairs found in data")
                return False
            elif validation_passed:
                HOSTNAME_PLACEHOLDER("Overall validation: PASSED - All request/response pairs within margin")
                return True
            else:
                HOSTNAME_PLACEHOLDER(f"Overall validation: FAILED - {failed_pairs} out of {pairs_found} pairs exceeded margin")
                return False

        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Unexpected error during validation: {e}")
            return False
