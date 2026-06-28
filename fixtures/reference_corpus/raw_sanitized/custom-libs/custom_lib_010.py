import datetime
import logging
import time
import paramiko
import os
from SOURCE_NAME_PLACEHOLDER import  SOURCE_NAME_PLACEHOLDER
from typing import List, Dict
import re


class SOURCE_NAME_PLACEHOLDER:
    def __init__(self, EMFTB_conn_params:Dict):
        """
        A constructor to build a connection with the EMFTB server.
        Args:
            emftb_ip (str): IP address of the EMFTB.
            emftb_username (str): Username of the EMFTB.
            emftb_key path(str): private key  of the EMFTB.
        """
        self.emftb_ips =[value for key, value in EMFTB_conn_params.items() if "IP" in  key ]   
        self.emftb_username = EMFTB_conn_params["USERNAME"]
        self.emftb_key_path = EMFTB_conn_params["KEYPATH"]
        self.emftb_port = EMFTB_conn_params["EMFTB_PORT"]

    def Login_and_Scrap_data(self, command : str, tc_dir : str):
        """
        This function opens an interactive session on the given by making use of paramiko module.
        This function executes the commands on the given server and returns the output path.
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
        
        output_file = tc_dir + f"/{self.emftb_username}_{date}_output.txt"

        # initiate SSH client
        connection_to_ericsson_box = HOSTNAME_PLACEHOLDER()
        connection_to_ericsson_box.set_missing_host_key_policy(HOSTNAME_PLACEHOLDER())

        for ip in self.emftb_ips :
            try:
                # SSH to Server
                connection_to_ericsson_box.connect(
                    ip,
                    self.emftb_port,
                    username=self.emftb_username,
                    key_filename=self.emftb_key_path,
                )
                HOSTNAME_PLACEHOLDER(f"Successfully connected to {ip} ")
            except HOSTNAME_PLACEHOLDER :
                HOSTNAME_PLACEHOLDER(f"Authentication Failed {ip}:{self.emftb_port} ")
                return False
            except HOSTNAME_PLACEHOLDER :
                HOSTNAME_PLACEHOLDER(f"SSH connection failed {ip}:{self.emftb_port} ")
                return False
            except Exception as e :
                HOSTNAME_PLACEHOLDER(f"Unexpected Error While connecting to {ip}:{self.emftb_port} : {e} ")
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
                HOSTNAME_PLACEHOLDER(f"Failed to Execute Command on Server {ip}:{self.emftb_port}")
                return False
                
            HOSTNAME_PLACEHOLDER()

        return output_file

    