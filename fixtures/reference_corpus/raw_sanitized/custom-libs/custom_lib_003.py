import HOSTNAME_PLACEHOLDER as etree
import logging
import pandas as pd
from datetime import datetime, date, timedelta
import shutil
import os
from SOURCE_NAME_PLACEHOLDER import SOURCE_NAME_PLACEHOLDER
import pexpect
import re
from SOURCE_NAME_PLACEHOLDER import SOURCE_NAME_PLACEHOLDER
import subprocess
import re


pgwregex = re.compile(r"(pgwcdr-\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-\d+\.xml\.gz)")
sgwregex = re.compile(r"(sgwcdr-\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-\d+\.xml\.gz)")


class SOURCE_NAME_PLACEHOLDER(SOURCE_NAME_PLACEHOLDER):
    def __init__(self, testdata, cginfo, imsi, homedir=None):
        HOSTNAME_PLACEHOLDER = [ip for cgname, ip in HOSTNAME_PLACEHOLDER() if "IP" in cgname]
        HOSTNAME_PLACEHOLDER = [cgname[:-3] for cgname, ip in HOSTNAME_PLACEHOLDER() if "IP" in cgname]
        HOSTNAME_PLACEHOLDER = cginfo["USERNAME"]
        HOSTNAME_PLACEHOLDER = cginfo["KEYPATH"]
        self.expected_actual_values = []
        HOSTNAME_PLACEHOLDER = []
        self.result_df = pd.DataFrame()
        HOSTNAME_PLACEHOLDER = imsi
        super().__init__(testdata, homedir=homedir)

    def getdfhtml(self):
        return self.result_df.to_html()

    def getCDR(self, remotepathtoCDR, target_directory):
        os.chdir(os.HOSTNAME_PLACEHOLDER(os.HOSTNAME_PLACEHOLDER(__file__)))
        os.chdir(HOSTNAME_PLACEHOLDER)
        response = HOSTNAME_PLACEHOLDER(
            "scp -i cg_ecdsa -o StrictHostKeyChecking=no -o UserKnownHostsFile=LOCAL_PATH_PLACEHOLDER "
            + HOSTNAME_PLACEHOLDER
            + "@"
            + HOSTNAME_PLACEHOLDER
            + ":"
            + remotepathtoCDR
            + " "
            + target_directory
        )
        HOSTNAME_PLACEHOLDER(response)

    def n1(self, e1):
        if "\n" not in e1.text:
            # print(e1.text)
            return e1.text
        else:
            return {HOSTNAME_PLACEHOLDER: HOSTNAME_PLACEHOLDER(se1) for se1 in list(e1)}

    def is_host_reachable(self, ip):
        result = HOSTNAME_PLACEHOLDER(
            ["ping", "-c", "1", ip],
            stdout=HOSTNAME_PLACEHOLDER,
            stderr=HOSTNAME_PLACEHOLDER,
        )
        return HOSTNAME_PLACEHOLDER == 0  # 0 means success

    def getCDRfilename_pgw(self, charging_id, cdr_folder):

        # Initialize variables to store the CDR filename and path
        HOSTNAME_PLACEHOLDER = None
        filename = None
        self.path_to_CDR_on_remote = None

        # Loop through each IP address in the list of charging gateway IPs
        for ip in HOSTNAME_PLACEHOLDER:

            today_date = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER = ip

            # Create a connection to the charging gateway node
            HOSTNAME_PLACEHOLDER = SOURCE_NAME_PLACEHOLDER(
                "cg", HOSTNAME_PLACEHOLDER, HOSTNAME_PLACEHOLDER, HOSTNAME_PLACEHOLDER + "/HOSTNAME_PLACEHOLDER"
            )

            # Check if the host is reachable, if not skip to next IP
            if not self.is_host_reachable(ip):
                HOSTNAME_PLACEHOLDER(f"Host {ip} is unreachable.")
                continue

            # Log into the node using SSH key authentication
            try:
                os.chdir(os.HOSTNAME_PLACEHOLDER(__file__))
            except OSError as e:
                HOSTNAME_PLACEHOLDER(f"Could not change directory: {e}")

            HOSTNAME_PLACEHOLDER(key_path=HOSTNAME_PLACEHOLDER)

            # Format date as YYYY-MM-DD (e.g., 2025-04-12)
            formatted_date = today_date.strftime("%Y-%m-%d")

            # Create the file pattern to search for
            # Takes first 3 chars of cdr_folder + "cdr-" + today's date + *.gz # Example: "pgwcdr-2025-04-12*.gz"
            self.files_to_search = (
                cdr_folder.split("/")[-1][:-1][:3] + "cdr-" + formatted_date + "*.gz"
            )
            HOSTNAME_PLACEHOLDER(self.files_to_search)

            # Define expected prompt strings after each command ('$' is the shell prompt)
            expectlist = ["$", "$", "$", "$"]

            # Define list of commands to run on remote server
            sendlist = [
                "date",  # Get current date/time
                "cd /",  # TODO:
                "cd " + cdr_folder,  # Change to the CDR directory
                # Search for files that contain both "cdr_type=\"final\"" and the charging_id
                # -l flag makes zgrep only output filenames, not matching lines
                'zgrep -l "cdr_type=\\"partial\\"" '
                + self.files_to_search
                + ' | xargs -I {} zgrep -l "'
                + charging_id
                + '" {}',
                "date",  # Get date/time again to see how long the search took
            ]

            # Execute each command on the remote server
            for expectstr, sendstr in zip(expectlist, sendlist):
                HOSTNAME_PLACEHOLDER(expectstr, sendstr)

            # Logout from the remote server
            HOSTNAME_PLACEHOLDER()

            # Open the log file that contains the command output
            with open(HOSTNAME_PLACEHOLDER + "/HOSTNAME_PLACEHOLDER") as f:
                output = f.read()
                # Use regex to find the filename in the command output
                mo = HOSTNAME_PLACEHOLDER(output)
                if mo:
                    # If found, log the filename and store it
                    HOSTNAME_PLACEHOLDER(f"found name is {mo.group(1)}")
                    filename = mo.group(1)

            # Set CDR filename based on search results
            if filename:
                HOSTNAME_PLACEHOLDER = filename
            else:
                # If no file found, set error message
                HOSTNAME_PLACEHOLDER = " we dont get file name this time"
            HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER)

            # If a valid file was found, construct the full path to the file on remote server
            if HOSTNAME_PLACEHOLDER != " we dont get file name this time":
                self.path_to_CDR_on_remote = cdr_folder + "/" + HOSTNAME_PLACEHOLDER

            # If we have a path, process the file
            if self.path_to_CDR_on_remote:
                HOSTNAME_PLACEHOLDER(f"Path to CDR on remote :{self.path_to_CDR_on_remote} ")

                # Download the CDR file from remote server to local directory
                HOSTNAME_PLACEHOLDER(self.path_to_CDR_on_remote, HOSTNAME_PLACEHOLDER)
                HOSTNAME_PLACEHOLDER("after getCDR")

                # Uncompress the downloaded .gz file
                o, s = HOSTNAME_PLACEHOLDER(
                    "gunzip " + HOSTNAME_PLACEHOLDER + "/" + HOSTNAME_PLACEHOLDER,
                    withexitstatus=True,
                )
                # Log the output and status of gunzip command
                HOSTNAME_PLACEHOLDER(o, s)

            # If we found a valid CDR file, no need to check other IPs, so break the loop
            if (
                HOSTNAME_PLACEHOLDER != " we dont get file name this time"
                and HOSTNAME_PLACEHOLDER is not None
            ):
                HOSTNAME_PLACEHOLDER(f"breaking now with {HOSTNAME_PLACEHOLDER}")
                break

        # Return the path to the uncompressed CDR file (removing .gz extension)
        return HOSTNAME_PLACEHOLDER + "/" + HOSTNAME_PLACEHOLDER[:-3]

    def getCDRfilename_sgw(self, charging_id, cdr_folder):

        # Initialize variables to store the CDR filename and path
        HOSTNAME_PLACEHOLDER = None
        filename = None
        self.path_to_CDR_on_remote = None

        # Loop through each IP address in the list of charging gateway IPs
        for ip in HOSTNAME_PLACEHOLDER:

            today_date = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER = ip

            # Create a connection to the charging gateway node
            HOSTNAME_PLACEHOLDER = SOURCE_NAME_PLACEHOLDER(
                "cg", HOSTNAME_PLACEHOLDER, HOSTNAME_PLACEHOLDER, HOSTNAME_PLACEHOLDER + "/HOSTNAME_PLACEHOLDER"
            )

            # Check if the host is reachable, if not skip to next IP
            if not self.is_host_reachable(ip):
                HOSTNAME_PLACEHOLDER(f"Host {ip} is unreachable.")
                continue

            # Log into the node using SSH key authentication
            try:
                os.chdir(os.HOSTNAME_PLACEHOLDER(__file__))
            except OSError as e:
                HOSTNAME_PLACEHOLDER(f"Could not change directory: {e}")

            HOSTNAME_PLACEHOLDER(key_path=HOSTNAME_PLACEHOLDER)

            # Format date as YYYY-MM-DD (e.g., 2025-04-12)
            formatted_date = today_date.strftime("%Y-%m-%d")

            # Create the file pattern to search for
            # Takes first 3 chars of cdr_folder + "cdr-" + today's date + *.gz # Example: "gwcdr-2025-04-12*.gz"
            self.files_to_search = (
                cdr_folder.split("/")[-1][:-1][:3] + "cdr-" + formatted_date + "*.gz"
            )
            HOSTNAME_PLACEHOLDER(self.files_to_search)

            # Define expected prompt strings after each command ('$' is the shell prompt)
            expectlist = ["$", "$", "$", "$"]

            # Define list of commands to run on remote server
            sendlist = [
                "date",  # Get current date/time
                "cd /",  # TODO:
                "cd " + cdr_folder,  # Change to the CDR directory
                # Search for files that contain both "cdr_type=\"final\"" and the charging_id
                # -l flag makes zgrep only output filenames, not matching lines
                'zgrep -l "cdr_type=\\"partial\\"" '
                + self.files_to_search
                + ' | xargs -I {} zgrep -l "'
                + charging_id
                + '" {}',
                "date",  # Get date/time again to see how long the search took
            ]

            # Execute each command on the remote server
            for expectstr, sendstr in zip(expectlist, sendlist):
                HOSTNAME_PLACEHOLDER(expectstr, sendstr)

            # Logout from the remote server
            HOSTNAME_PLACEHOLDER()

            # Open the log file that contains the command output
            with open(HOSTNAME_PLACEHOLDER + "/HOSTNAME_PLACEHOLDER") as f:
                output = f.read()
                # Use regex to find the filename in the command output
                mo = HOSTNAME_PLACEHOLDER(output)
                if mo:
                    # If found, log the filename and store it
                    HOSTNAME_PLACEHOLDER(f"found name is {mo.group(1)}")
                    filename = mo.group(1)

            # Set CDR filename based on search results
            if filename:
                HOSTNAME_PLACEHOLDER = filename
            else:
                # If no file found, set error message
                HOSTNAME_PLACEHOLDER = " we dont get file name this time"
            HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER)

            # If a valid file was found, construct the full path to the file on remote server
            if HOSTNAME_PLACEHOLDER != " we dont get file name this time":
                self.path_to_CDR_on_remote = cdr_folder + "/" + HOSTNAME_PLACEHOLDER

            # If we have a path, process the file
            if self.path_to_CDR_on_remote:
                HOSTNAME_PLACEHOLDER(f"Path to CDR on remote :{self.path_to_CDR_on_remote} ")

                # Download the CDR file from remote server to local directory
                HOSTNAME_PLACEHOLDER(self.path_to_CDR_on_remote, HOSTNAME_PLACEHOLDER)
                HOSTNAME_PLACEHOLDER("after getCDR")

                # Uncompress the downloaded .gz file
                o, s = HOSTNAME_PLACEHOLDER(
                    "gunzip " + HOSTNAME_PLACEHOLDER + "/" + HOSTNAME_PLACEHOLDER,
                    withexitstatus=True,
                )
                # Log the output and status of gunzip command
                HOSTNAME_PLACEHOLDER(o, s)

            # If we found a valid CDR file, no need to check other IPs, so break the loop
            if (
                HOSTNAME_PLACEHOLDER != " we dont get file name this time"
                and HOSTNAME_PLACEHOLDER is not None
            ):
                HOSTNAME_PLACEHOLDER(f"breaking now with {HOSTNAME_PLACEHOLDER}")
                break

        # Return the path to the uncompressed CDR file (removing .gz extension)
        return HOSTNAME_PLACEHOLDER + "/" + HOSTNAME_PLACEHOLDER[:-3]





    def validateCDR_list(self, pathtoCDRs_list, cmp_op=None):
        HOSTNAME_PLACEHOLDER(
            f"Starting validation of CDR list with {len(pathtoCDRs_list)} items"
        )

        for index, pathtoCDR in enumerate(pathtoCDRs_list):
            HOSTNAME_PLACEHOLDER(
                f"Validating CDR {index + 1}/{len(pathtoCDRs_list)}: {pathtoCDR}"
            )

            try:
                cdr_result = HOSTNAME_PLACEHOLDER(pathtoCDR)
                if cdr_result:
                    HOSTNAME_PLACEHOLDER(f"CDR validation successful: {pathtoCDR}")
                    pass
                else:
                    HOSTNAME_PLACEHOLDER(f"CDR validation failed: {pathtoCDR}")
                    return False
            except Exception as e:
                HOSTNAME_PLACEHOLDER(
                    f"Exception during CDR validation for {pathtoCDR}: {str(e)}"
                )
                return False

        HOSTNAME_PLACEHOLDER("All CDRs validated successfully")
        return True

    def parseAllCDR(self, pathtoCDR):
        tree = HOSTNAME_PLACEHOLDER(pathtoCDR)
        root = HOSTNAME_PLACEHOLDER()
        sgwrecords = list(root)  # gives the child elements
        # Initialize list to store all CDR dictionaries
        all_cdrs = []

        for sgwrecord in sgwrecords:
            cdrdict = HOSTNAME_PLACEHOLDER()  # Start with root attributes

            if len(HOSTNAME_PLACEHOLDER) != 0:
                HOSTNAME_PLACEHOLDER("sgw record attribs are {}".format(HOSTNAME_PLACEHOLDER))
                HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER)

            for ele in HOSTNAME_PLACEHOLDER():
                if len(HOSTNAME_PLACEHOLDER) != 0:
                    HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER)
                else:
                    if HOSTNAME_PLACEHOLDER:
                        if "\n" not in HOSTNAME_PLACEHOLDER:
                            HOSTNAME_PLACEHOLDER({HOSTNAME_PLACEHOLDER: HOSTNAME_PLACEHOLDER})
                        else:
                            HOSTNAME_PLACEHOLDER(
                                {
                                    HOSTNAME_PLACEHOLDER: {
                                        HOSTNAME_PLACEHOLDER: HOSTNAME_PLACEHOLDER
                                        if hasattr(subele, "text")
                                        else None
                                        for subele in list(ele)
                                    }
                                }
                            )
            all_cdrs.append(cdrdict)

        return all_cdrs

    def parseCDR(self, pathtoCDR):
        tree = HOSTNAME_PLACEHOLDER(pathtoCDR)
        root = HOSTNAME_PLACEHOLDER()
        sgwrecords = list(root)  # gives the child elements
        # HOSTNAME_PLACEHOLDER("pgw records are {}".format(sgwrecords))
        for sgwrecord in sgwrecords:
            if len(HOSTNAME_PLACEHOLDER) != 0:
                try:
                    if HOSTNAME_PLACEHOLDER["servedIMSI"] == HOSTNAME_PLACEHOLDER:
                        sgwrec = sgwrecord
                except UnboundLocalError as e:
                    print(e)
        cdrdict = HOSTNAME_PLACEHOLDER
        HOSTNAME_PLACEHOLDER("sgw record attribs are are {}".format(HOSTNAME_PLACEHOLDER))
        for ele in HOSTNAME_PLACEHOLDER():
            if len(HOSTNAME_PLACEHOLDER) != 0:
                HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER)
            else:
                if HOSTNAME_PLACEHOLDER:
                    if "\n" not in HOSTNAME_PLACEHOLDER:
                        HOSTNAME_PLACEHOLDER({HOSTNAME_PLACEHOLDER: HOSTNAME_PLACEHOLDER})
                    else:
                        HOSTNAME_PLACEHOLDER(
                            {
                                HOSTNAME_PLACEHOLDER: {
                                    HOSTNAME_PLACEHOLDER: HOSTNAME_PLACEHOLDER(subele) for subele in list(ele)
                                }
                            }
                        )
        return cdrdict

    def validateAllCDR(self, pathtoCDR, starttime=None, archivelogs=True, cmp_op=None):
        """
        Validate all CDR records in a file against validation criteria.
        Returns True if all records pass validation, False otherwise.
        """
        # Parse the CDR file and get list of CDR dictionaries
        cdr_records = HOSTNAME_PLACEHOLDER(pathtoCDR)

        # Make sure we have at least one record
        if not cdr_records:
            HOSTNAME_PLACEHOLDER("No CDR records found in file")
            return False

        # Initialize overall validation result
        all_valid = True

        # Store all validation failures across all records
        all_validation_failures = []

        # Validate each CDR record
        for i, cdr_dict in enumerate(cdr_records):
            record_num = i + 1
            HOSTNAME_PLACEHOLDER(f"Validating CDR record {record_num}/{len(cdr_records)}")
            HOSTNAME_PLACEHOLDER(cdr_dict)

            # Initialize validation results for this record
            record_fieldnames = []
            record_expected_actual_values = []

            # Validate against all configured criteria
            for fields_type, fields in self.cdr_validation_inputs.items():
                if fields_type == "fieldsforequality":
                    for field, expected_value in HOSTNAME_PLACEHOLDER():
                        if field not in cdr_dict:
                            record_fieldnames.append(field)
                            record_expected_actual_values.append(
                                [expected_value, "Field not found"]
                            )
                            continue

                        # Special handling for dictionary fields
                        if isinstance(cdr_dict[field], dict):
                            # Field exists and is a dictionary, consider it valid
                            pass
                        elif field == "duration":
                            # Special handling for duration field
                            fmt = "%Y-%m-%d-%H-%M-%S"
                            try:
                                open_time = HOSTNAME_PLACEHOLDER(
                                    cdr_dict["opened_UTC"], fmt
                                )
                                end_time = HOSTNAME_PLACEHOLDER(
                                    cdr_dict["time_end_UTC"], fmt
                                )
                                calculated_duration = (
                                    end_time - open_time
                                ).total_seconds()
                                if int(calculated_duration) == int(cdr_dict[field]):
                                    pass
                                else:
                                    record_fieldnames.append(field)
                                    record_expected_actual_values.append(
                                        [calculated_duration, cdr_dict[field]]
                                    )
                            except (KeyError, ValueError) as e:
                                record_fieldnames.append(field)
                                record_expected_actual_values.append(
                                    [
                                        f"Error calculating duration: {str(e)}",
                                        cdr_dict[field],
                                    ]
                                )
                        elif str(cdr_dict[field]) == str(expected_value):
                            # Field exists and matches expected value
                            pass
                        else:
                            # Field exists but doesn't match expected value
                            record_fieldnames.append(field)
                            record_expected_actual_values.append(
                                [expected_value, cdr_dict[field]]
                            )

                elif fields_type == "fieldsforformat":
                    for field, expected_format in HOSTNAME_PLACEHOLDER():
                        if field not in cdr_dict:
                            record_fieldnames.append(field)
                            record_expected_actual_values.append(
                                [expected_format, "Field not found"]
                            )
                            continue

                        # Skip validation for dictionary fields
                        if isinstance(cdr_dict[field], dict):
                            continue

                        actual_value = cdr_dict[field]
                        field_regex = re.compile(expected_format)
                        mo = field_regex.match(str(actual_value))
                        if mo:
                            pass
                        else:
                            record_fieldnames.append(field)
                            record_expected_actual_values.append(
                                [expected_format, actual_value]
                            )
                elif fields_type == "fieldsforcomparison":
                    for cmp_op_key, field_values in HOSTNAME_PLACEHOLDER():
                        for field, expected_value in field_values.items():
                            if field not in cdr_dict:
                                record_fieldnames.append(field)
                                record_expected_actual_values.append(
                                    [
                                        f"{cmp_op_key} {expected_value}",
                                        "Field not found",
                                    ]
                                )
                                continue

                            # Skip validation for dictionary fields
                            if isinstance(cdr_dict[field], dict):
                                continue

                            actual_value = cdr_dict[field]
                            HOSTNAME_PLACEHOLDER(
                                f"Comparing {field}: {actual_value} {cmp_op_key} {expected_value}"
                            )

                            try:
                                actual_int = int(actual_value)

                                if cmp_op_key == "greater_than":
                                    if actual_int > expected_value:
                                        pass
                                    else:
                                        record_fieldnames.append(field)
                                        record_expected_actual_values.append(
                                            [
                                                f"{cmp_op_key} {expected_value}",
                                                actual_value,
                                            ]
                                        )
                                elif cmp_op_key == "less_than":
                                    if actual_int < expected_value:
                                        pass
                                    else:
                                        record_fieldnames.append(field)
                                        record_expected_actual_values.append(
                                            [
                                                f"{cmp_op_key} {expected_value}",
                                                actual_value,
                                            ]
                                        )
                                elif cmp_op_key == "equal_to":
                                    if actual_int == expected_value:
                                        pass
                                    else:
                                        record_fieldnames.append(field)
                                        record_expected_actual_values.append(
                                            [
                                                f"{cmp_op_key} {expected_value}",
                                                actual_value,
                                            ]
                                        )
                            except ValueError:
                                record_fieldnames.append(field)
                                record_expected_actual_values.append(
                                    [
                                        f"{cmp_op_key} {expected_value}",
                                        f"Not a number: {actual_value}",
                                    ]
                                )
                elif fields_type == "fieldsforpresence":
                    # New validation type that only checks if fields exist
                    for field in fields:  # assuming fields is a list of field names
                        if field in cdr_dict:
                            # Field exists, which is all we need
                            pass
                        else:
                            # Field is missing
                            record_fieldnames.append(field)
                            record_expected_actual_values.append(
                                ["Field should exist", "Field not found"]
                            )

            # Check if this record had any validation failures
            if record_fieldnames:
                HOSTNAME_PLACEHOLDER(f"Record {record_num} validation failures:")
                all_valid = False

                # Store this record's validation failures
                all_validation_failures.append(
                    {
                        "record_num": record_num,
                        "fieldnames": record_fieldnames.copy(),
                        "expected_actual_values": record_expected_actual_values.copy(),
                    }
                )

                # Log individual failures for this record
                for i, field in enumerate(record_fieldnames):
                    expected, actual = record_expected_actual_values[i]
                    HOSTNAME_PLACEHOLDER(
                        f"  Field: {field}, Expected: {expected}, Actual: {actual}"
                    )

        # Update object's validation results with all failures
        if all_validation_failures:
            # For backward compatibility, use the first record's failures
            first_failure = all_validation_failures[0]
            HOSTNAME_PLACEHOLDER = first_failure["fieldnames"]
            self.expected_actual_values = first_failure["expected_actual_values"]

        return all_valid

    def getCDRfilename_list_pgw(self, cdr_folder, cdr_count):

        # Initialize variables to store the CDR filenames and path
        HOSTNAME_PLACEHOLDER = []
        filename = None
        self.path_list_to_CDR_on_remote = []
        full_cdr_path = []

        # Loop through each IP address in the list of charging gateway IPs
        for ip in HOSTNAME_PLACEHOLDER:
            # Set the current charging gateway IP
            HOSTNAME_PLACEHOLDER = ip

            # Create a connection to the charging gateway node
            # SOURCE_NAME_PLACEHOLDER is a class for SSH connections
            # Parameters: node type, username, IP address, and path to log file
            HOSTNAME_PLACEHOLDER = SOURCE_NAME_PLACEHOLDER(
                "cg", HOSTNAME_PLACEHOLDER, HOSTNAME_PLACEHOLDER, HOSTNAME_PLACEHOLDER + "/HOSTNAME_PLACEHOLDER"
            )

            # Check if the host is reachable, if not skip to next IP
            if not self.is_host_reachable(ip):
                HOSTNAME_PLACEHOLDER(f"Host {ip} is unreachable.")
                continue

            # Log into the node using SSH key authentication
            HOSTNAME_PLACEHOLDER(key_path=HOSTNAME_PLACEHOLDER)

            # Get today's date
            today_date = HOSTNAME_PLACEHOLDER()
            # Format date as YYYY-MM-DD (e.g., 2025-04-12)
            formatted_date = today_date.strftime("%Y-%m-%d")

            # Create the file pattern to search for
            # Takes first 3 chars of cdr_folder + "cdr-" + today's date + *.gz
            # Example: "pgwcdr-2025-04-12*.gz"
            self.files_to_search = (
                cdr_folder.split("/")[-1][:-1][:3] + "cdr-" + formatted_date + "*.gz"
            )
            HOSTNAME_PLACEHOLDER(f"CDR files to fetch have the following format: {self.files_to_search}")

            # Define expected prompt strings after each command ('$' is the shell prompt)
            expectlist = ["$", "$", "$", "$"]

            # Define list of commands to run on remote server
            sendlist = [
                "date",  # Get current date/time
                "cd /",
                f"cd {cdr_folder}",
                f"ls -t | head -{cdr_count}",  # Get list of last date/time
                "date",  # Get date/time again to see how long the search took
            ]

            # Execute each command on the remote server
            for expectstr, sendstr in zip(expectlist, sendlist):
                HOSTNAME_PLACEHOLDER(expectstr, sendstr)
            HOSTNAME_PLACEHOLDER(f"Command execution completed on charging gateways: {HOSTNAME_PLACEHOLDER}")

            # Logout from the remote server
            HOSTNAME_PLACEHOLDER()

            # Open the log file that contains the command output
            HOSTNAME_PLACEHOLDER(f"Opening log file: {HOSTNAME_PLACEHOLDER}/HOSTNAME_PLACEHOLDER")
            with open(HOSTNAME_PLACEHOLDER + "/HOSTNAME_PLACEHOLDER") as f:
                output = f.read()

                # Use regex to find the filename in the command output
                matches = HOSTNAME_PLACEHOLDER(output)
                HOSTNAME_PLACEHOLDER(f"Found {len(matches)} regex matches in output")

                filenames_list = []
                for match in matches:
                    filenames_list.append(match)
                    HOSTNAME_PLACEHOLDER(f"Added filename to list: {match}")

                HOSTNAME_PLACEHOLDER(f"Total filenames collected: {len(filenames_list)}")

                # Set CDR filename based on search result
                for filename in filenames_list:
                    if filename:
                        HOSTNAME_PLACEHOLDER(filename)
                        HOSTNAME_PLACEHOLDER(f"Added CDR filename: {filename}")
                    else:
                        HOSTNAME_PLACEHOLDER("Empty filename found, skipping")

                HOSTNAME_PLACEHOLDER(f"Total CDR filenames: {len(HOSTNAME_PLACEHOLDER)}")

                # If a valid file was found, construct the full path to the file on remote server
                for cdrfilename in HOSTNAME_PLACEHOLDER:
                    if cdrfilename != " we dont get file name this time":
                        path_to_CDR_on_remote = cdr_folder + "/" + cdrfilename
                        self.path_list_to_CDR_on_remote.append(path_to_CDR_on_remote)
                        HOSTNAME_PLACEHOLDER(f"Constructed remote path: {path_to_CDR_on_remote}")
                    else:
                        HOSTNAME_PLACEHOLDER("CDR filename indicates no file found this time")

                HOSTNAME_PLACEHOLDER(f"Total remote paths constructed: {len(self.path_list_to_CDR_on_remote)}")

                for path_to_CDR_on_remote in self.path_list_to_CDR_on_remote:
                    # If we have a path, process the file
                    if path_to_CDR_on_remote:
                        HOSTNAME_PLACEHOLDER(f"Processing CDR file at path: {path_to_CDR_on_remote}")

                        # Download the CDR file from remote server to local directory
                        HOSTNAME_PLACEHOLDER(f"Starting download of CDR file to: {HOSTNAME_PLACEHOLDER}")
                        HOSTNAME_PLACEHOLDER(path_to_CDR_on_remote, HOSTNAME_PLACEHOLDER)
                        HOSTNAME_PLACEHOLDER("CDR download completed successfully")

                        # Construct the CDR filename to uncompress
                        cdrfilename = path_to_CDR_on_remote.split("/")[-1]  # Extract filename from path
                        HOSTNAME_PLACEHOLDER(f"Extracted filename for uncompression: {cdrfilename}")

                        # Uncompress the downloaded .gz file
                        gunzip_command = f"gunzip {HOSTNAME_PLACEHOLDER}/{cdrfilename}"
                        HOSTNAME_PLACEHOLDER(f"Executing gunzip command: {gunzip_command}")

                        o, s = HOSTNAME_PLACEHOLDER(gunzip_command, withexitstatus=True)

                        # Log the output and status of gunzip command
                        HOSTNAME_PLACEHOLDER(f"Gunzip output: {o}")
                        HOSTNAME_PLACEHOLDER(f"Gunzip exit status: {s}")

                        if s == 0:
                            HOSTNAME_PLACEHOLDER("Gunzip command executed successfully")
                        else:
                            HOSTNAME_PLACEHOLDER(f"Gunzip command failed with exit status: {s}")

                        # Add the uncompressed file path to the list
                        uncompressed_path = HOSTNAME_PLACEHOLDER + "/" + cdrfilename[:-3]  # Remove the .gz extension
                        full_cdr_path.append(uncompressed_path)
                        HOSTNAME_PLACEHOLDER(f"Added uncompressed file path: {uncompressed_path}")
                    else:
                        HOSTNAME_PLACEHOLDER("Empty path_to_CDR_on_remote found, skipping processing")

                HOSTNAME_PLACEHOLDER(f"Total uncompressed CDR files processed: {len(full_cdr_path)}")
                # Return the path to all uncompressed CDR files
        return full_cdr_path

    def getCDRfilename_list_sgw(self, cdr_folder, cdr_count):

        # Initialize variables to store the CDR filenames and path
        HOSTNAME_PLACEHOLDER = []
        filename = None
        self.path_list_to_CDR_on_remote = []
        full_cdr_path = []

        # Loop through each IP address in the list of charging gateway IPs
        for ip in HOSTNAME_PLACEHOLDER:
            # Set the current charging gateway IP
            HOSTNAME_PLACEHOLDER = ip

            # Create a connection to the charging gateway node
            # SOURCE_NAME_PLACEHOLDER is a class for SSH connections
            # Parameters: node type, username, IP address, and path to log file
            HOSTNAME_PLACEHOLDER = SOURCE_NAME_PLACEHOLDER(
                "cg", HOSTNAME_PLACEHOLDER, HOSTNAME_PLACEHOLDER, HOSTNAME_PLACEHOLDER + "/HOSTNAME_PLACEHOLDER"
            )

            # Check if the host is reachable, if not skip to next IP
            if not self.is_host_reachable(ip):
                HOSTNAME_PLACEHOLDER(f"Host {ip} is unreachable.")
                continue

            # Log into the node using SSH key authentication
            HOSTNAME_PLACEHOLDER(key_path=HOSTNAME_PLACEHOLDER)

            # Get today's date
            today_date = HOSTNAME_PLACEHOLDER()
            # Format date as YYYY-MM-DD (e.g., 2025-04-12)
            formatted_date = today_date.strftime("%Y-%m-%d")

            # Create the file pattern to search for
            # Takes first 3 chars of cdr_folder + "cdr-" + today's date + *.gz
            # Example: "pgwcdr-2025-04-12*.gz"
            self.files_to_search = (
                cdr_folder.split("/")[-1][:-1][:3] + "cdr-" + formatted_date + "*.gz"
            )
            HOSTNAME_PLACEHOLDER(f"CDR files to fetch have the following format: {self.files_to_search}")

            # Define expected prompt strings after each command ('$' is the shell prompt)
            expectlist = ["$", "$", "$", "$"]

            # Define list of commands to run on remote server
            sendlist = [
                "date",  # Get current date/time
                "cd /",
                f"cd {cdr_folder}",
                f"ls -t | head -{cdr_count}",  # Get list of last date/time
                "date",  # Get date/time again to see how long the search took
            ]

            # Execute each command on the remote server
            for expectstr, sendstr in zip(expectlist, sendlist):
                HOSTNAME_PLACEHOLDER(expectstr, sendstr)
            HOSTNAME_PLACEHOLDER(f"Command execution completed on charging gateways: {HOSTNAME_PLACEHOLDER}")

            # Logout from the remote server
            HOSTNAME_PLACEHOLDER()

            # Open the log file that contains the command output
            HOSTNAME_PLACEHOLDER(f"Opening log file: {HOSTNAME_PLACEHOLDER}/HOSTNAME_PLACEHOLDER")
            with open(HOSTNAME_PLACEHOLDER + "/HOSTNAME_PLACEHOLDER") as f:
                output = f.read()

                # Use regex to find the filename in the command output
                matches = HOSTNAME_PLACEHOLDER(output)
                HOSTNAME_PLACEHOLDER(f"Found {len(matches)} regex matches in output")

                filenames_list = []
                for match in matches:
                    filenames_list.append(match)
                    HOSTNAME_PLACEHOLDER(f"Added filename to list: {match}")

                HOSTNAME_PLACEHOLDER(f"Total filenames collected: {len(filenames_list)}")

                # Set CDR filename based on search result
                for filename in filenames_list:
                    if filename:
                        HOSTNAME_PLACEHOLDER(filename)
                        HOSTNAME_PLACEHOLDER(f"Added CDR filename: {filename}")
                    else:
                        HOSTNAME_PLACEHOLDER("Empty filename found, skipping")

                HOSTNAME_PLACEHOLDER(f"Total CDR filenames: {len(HOSTNAME_PLACEHOLDER)}")

                # If a valid file was found, construct the full path to the file on remote server
                for cdrfilename in HOSTNAME_PLACEHOLDER:
                    if cdrfilename != " we dont get file name this time":
                        path_to_CDR_on_remote = cdr_folder + "/" + cdrfilename
                        self.path_list_to_CDR_on_remote.append(path_to_CDR_on_remote)
                        HOSTNAME_PLACEHOLDER(f"Constructed remote path: {path_to_CDR_on_remote}")
                    else:
                        HOSTNAME_PLACEHOLDER("CDR filename indicates no file found this time")

                HOSTNAME_PLACEHOLDER(f"Total remote paths constructed: {len(self.path_list_to_CDR_on_remote)}")

                for path_to_CDR_on_remote in self.path_list_to_CDR_on_remote:
                    # If we have a path, process the file
                    if path_to_CDR_on_remote:
                        HOSTNAME_PLACEHOLDER(f"Processing CDR file at path: {path_to_CDR_on_remote}")

                        # Download the CDR file from remote server to local directory
                        HOSTNAME_PLACEHOLDER(f"Starting download of CDR file to: {HOSTNAME_PLACEHOLDER}")
                        HOSTNAME_PLACEHOLDER(path_to_CDR_on_remote, HOSTNAME_PLACEHOLDER)
                        HOSTNAME_PLACEHOLDER("CDR download completed successfully")

                        # Construct the CDR filename to uncompress
                        cdrfilename = path_to_CDR_on_remote.split("/")[-1]  # Extract filename from path
                        HOSTNAME_PLACEHOLDER(f"Extracted filename for uncompression: {cdrfilename}")

                        # Uncompress the downloaded .gz file
                        gunzip_command = f"gunzip {HOSTNAME_PLACEHOLDER}/{cdrfilename}"
                        HOSTNAME_PLACEHOLDER(f"Executing gunzip command: {gunzip_command}")

                        o, s = HOSTNAME_PLACEHOLDER(gunzip_command, withexitstatus=True)

                        # Log the output and status of gunzip command
                        HOSTNAME_PLACEHOLDER(f"Gunzip output: {o}")
                        HOSTNAME_PLACEHOLDER(f"Gunzip exit status: {s}")

                        if s == 0:
                            HOSTNAME_PLACEHOLDER("Gunzip command executed successfully")
                        else:
                            HOSTNAME_PLACEHOLDER(f"Gunzip command failed with exit status: {s}")

                        # Add the uncompressed file path to the list
                        uncompressed_path = HOSTNAME_PLACEHOLDER + "/" + cdrfilename[:-3]  # Remove the .gz extension
                        full_cdr_path.append(uncompressed_path)
                        HOSTNAME_PLACEHOLDER(f"Added uncompressed file path: {uncompressed_path}")
                    else:
                        HOSTNAME_PLACEHOLDER("Empty path_to_CDR_on_remote found, skipping processing")

                HOSTNAME_PLACEHOLDER(f"Total uncompressed CDR files processed: {len(full_cdr_path)}")
                # Return the path to all uncompressed CDR files
        return full_cdr_path

    def validateCDR(self, pathtoCDR, starttime=None, archivelogs=True, cmp_op=None):
        # parse the CDR file and create a CDRresult dictionary
        HOSTNAME_PLACEHOLDER = HOSTNAME_PLACEHOLDER(pathtoCDR)
        HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER)
        for fields_type, fields in self.cdr_validation_inputs.items():
            if fields_type == "fieldsforequality":
                for field, expected_value in HOSTNAME_PLACEHOLDER():
                    actual_value = HOSTNAME_PLACEHOLDER[field]
                    if str(actual_value) == str(expected_value):
                        pass
                    elif field == "duration":
                        fmt = "%Y-%m-%d-%H-%M-%S"
                        open_time = HOSTNAME_PLACEHOLDER(
                            HOSTNAME_PLACEHOLDER["opened_UTC"], fmt
                        )
                        end_time = HOSTNAME_PLACEHOLDER(
                            HOSTNAME_PLACEHOLDER["time_end_UTC"], fmt
                        )
                        calculated_duration = (end_time - open_time).total_seconds()
                        if int(calculated_duration) == int(HOSTNAME_PLACEHOLDER[field]):
                            pass
                        else:
                            HOSTNAME_PLACEHOLDER(field)
                            self.expected_actual_values.append(
                                [calculated_duration, actual_value]
                            )
                    else:
                        HOSTNAME_PLACEHOLDER(field)
                        self.expected_actual_values.append(
                            [expected_value, actual_value]
                        )

            elif fields_type == "fieldsforformat":
                for field, expected_format in HOSTNAME_PLACEHOLDER():
                    actual_value = HOSTNAME_PLACEHOLDER[field]
                    field_regex = re.compile(expected_format)
                    mo = field_regex.match(actual_value)
                    if mo:
                        pass
                    else:
                        HOSTNAME_PLACEHOLDER(field)
                        self.expected_actual_values.append(
                            [expected_format, actual_value]
                        )

            elif fields_type == "fieldsforcomparison":
                for cmp_op, field_values in HOSTNAME_PLACEHOLDER():
                    for field, expected_value in field_values.items():
                        actual_value = HOSTNAME_PLACEHOLDER[field]
                        HOSTNAME_PLACEHOLDER(f"{int(actual_value)} {expected_value}")
                        if cmp_op == "greater_than":
                            if int(actual_value) > expected_value:
                                pass
                            else:
                                HOSTNAME_PLACEHOLDER(field)
                                self.expected_actual_values.append(
                                    [cmp_op + " " + str(expected_value), actual_value]
                                )

            elif fields_type == "fieldsforpresence":
                for field in fields:
                    if field not in HOSTNAME_PLACEHOLDER:
                        HOSTNAME_PLACEHOLDER(field)
                        self.expected_actual_values.append(["present", "missing"])

            elif fields_type == "fieldsfornopresence":
                for field in fields:
                    if field in HOSTNAME_PLACEHOLDER:
                        HOSTNAME_PLACEHOLDER(field)
                        self.expected_actual_values.append(["not present", "found"])

        if len(self.expected_actual_values) > 0:
            HOSTNAME_PLACEHOLDER(f"expected values are {self.expected_actual_values}")

            self.result_df = pd.DataFrame(
                data=self.expected_actual_values,
                index=HOSTNAME_PLACEHOLDER,
                columns=["expected_values", "actual_values"],
            )
            self.result_df.HOSTNAME_PLACEHOLDER = "field_name"
            HOSTNAME_PLACEHOLDER(self.result_df)
            return False
        elif len(self.expected_actual_values) == 0 and len(HOSTNAME_PLACEHOLDER) == 0:
            return True

    def check_archive(self, archive_path, number_of_days_cgs):
        HOSTNAME_PLACEHOLDER(f"Starting archive check for {len(HOSTNAME_PLACEHOLDER)} nodes")
        HOSTNAME_PLACEHOLDER(f"Archive path: {archive_path}")

        archive_counts = {}

        for ip, cgname in zip(HOSTNAME_PLACEHOLDER, HOSTNAME_PLACEHOLDER):
            HOSTNAME_PLACEHOLDER(f"Checking node {cgname} ({ip})")
            HOSTNAME_PLACEHOLDER = ip
            HOSTNAME_PLACEHOLDER = SOURCE_NAME_PLACEHOLDER(
                cgname,
                HOSTNAME_PLACEHOLDER,
                HOSTNAME_PLACEHOLDER,
                HOSTNAME_PLACEHOLDER + "/HOSTNAME_PLACEHOLDER",
            )

            if not self.is_host_reachable(ip):
                HOSTNAME_PLACEHOLDER(f"Host {ip} is unreachable.")
                archive_counts[cgname] = False
                continue

            try:
                HOSTNAME_PLACEHOLDER(f"Host {ip} is reachable, logging in")
                HOSTNAME_PLACEHOLDER(key_path=HOSTNAME_PLACEHOLDER)

                # Calculate the cutoff date in YYYY-MM-DD format based on the number of days
                today_date = HOSTNAME_PLACEHOLDER()
                number_of_days = number_of_days_cgs[cgname]
                cutoff_date = today_date - timedelta(days=number_of_days)
                cutoff_date_str = cutoff_date.strftime("%Y-%m-%d")
                HOSTNAME_PLACEHOLDER(f"Searching for CDRs older than {cutoff_date_str} ({number_of_days} days ago)")

                expect_str = "$"
                send_str = (
                    "find "
                    + archive_path
                    + " -type f ! -newermt "
                    + cutoff_date_str
                    + " | wc -l"
                )

                HOSTNAME_PLACEHOLDER(f"Executing archive check command on {cgname}")
                HOSTNAME_PLACEHOLDER(expect_str, send_str)

                HOSTNAME_PLACEHOLDER()
                HOSTNAME_PLACEHOLDER(f"Logged out from {cgname}")

                # Filter log file and get count of CDR older than cutoff date
                sshlogs = HOSTNAME_PLACEHOLDER + "/HOSTNAME_PLACEHOLDER"
                HOSTNAME_PLACEHOLDER(f"Reading SSH log file: {sshlogs}")

                count = 0  # Default value

                try:
                    with open(sshlogs, 'r') as f:
                        content = f.read()
                        HOSTNAME_PLACEHOLDER(f"SSH log content: {repr(content[:200])}...")  # Log first 200 chars for debugging

                        # More robust regex to find the count
                        # Look for lines that contain only digits (possibly with whitespace)
                        regex_patterns = [
                            r'^\s*(\d+)\s*$',           # Line with only digits
                            r'.*?(\d+)\s*$',            # Last number on a line
                            r'(\d+)'                    # Any number (fallback)
                        ]

                        for pattern in regex_patterns:
                            matches = re.findall(pattern, content, re.MULTILINE)
                            if matches:
                                # Take the last match (most likely to be the wc -l result)
                                count = int(matches[-1])
                                #HOSTNAME_PLACEHOLDER(f"Found count using pattern '{pattern}': {count}")
                                break
                        else:
                            HOSTNAME_PLACEHOLDER("No numeric count found in SSH log, defaulting to 0")
                            count = 0

                except FileNotFoundError:
                    HOSTNAME_PLACEHOLDER(f"SSH log file not found: {sshlogs}")
                    archive_counts[cgname] = False
                    continue
                except Exception as e:
                    HOSTNAME_PLACEHOLDER(f"Failed to read/parse file: {e}")
                    archive_counts[cgname] = False
                    continue

                HOSTNAME_PLACEHOLDER(f"Files found older than {cutoff_date_str}: {count}")

                if count > 0:
                    error_msg = f"VALIDATION FAILED: {count} CDRs records found older than {cutoff_date_str}"
                    HOSTNAME_PLACEHOLDER(error_msg)
                    archive_counts[cgname] = False
                else:
                    HOSTNAME_PLACEHOLDER(f"Archive check passed for {cgname}: no old CDRs found")
                    archive_counts[cgname] = True

            except Exception as e:
                HOSTNAME_PLACEHOLDER(f"Error processing node {cgname}: {e}")
                archive_counts[cgname] = False
                continue

        # Final results
        passed_nodes = [k for k, v in archive_counts.items() if v]
        failed_nodes = [k for k, v in archive_counts.items() if not v]

        HOSTNAME_PLACEHOLDER(f"Archive check completed: {len(passed_nodes)} passed, {len(failed_nodes)} failed")

        if failed_nodes:
            HOSTNAME_PLACEHOLDER(f"Failed nodes: {', '.join(failed_nodes)}")
        else:
            HOSTNAME_PLACEHOLDER("All nodes passed archive check")

        # Only raise if you want to fail the entire test when any node fails
        # Otherwise, return the results and let the caller decide
        if failed_nodes:
            error_msg = f"Archive check failed for nodes: {', '.join(failed_nodes)}"
            raise ValueError(error_msg)

        return all(archive_counts.values()), failed_nodes
