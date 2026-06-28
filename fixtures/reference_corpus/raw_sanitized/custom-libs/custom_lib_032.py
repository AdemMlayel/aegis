import re
import pyshark
import json
import itertools
import ast
import pandas as pd
import logging
import os
import time
from HOSTNAME_PLACEHOLDER import Iterable
from datetime import datetime
from SOURCE_NAME_PLACEHOLDER import SOURCE_NAME_PLACEHOLDER
import ipaddress
HOSTNAME_PLACEHOLDER(level=HOSTNAME_PLACEHOLDER,
                    format='%(asctime)s - %(levelname)s - %(message)s')
field_regex = re.compile(r"[^a-z]")


class SOURCE_NAME_PLACEHOLDER:
    def __init__(self, pcapfilepath, filter, test_config, tc_dir):
        HOSTNAME_PLACEHOLDER = HOSTNAME_PLACEHOLDER(
            pcapfilepath, keep_packets=False, display_filter=filter)
        HOSTNAME_PLACEHOLDER = []
        HOSTNAME_PLACEHOLDER = []
        HOSTNAME_PLACEHOLDER = []
        HOSTNAME_PLACEHOLDER = []
        HOSTNAME_PLACEHOLDER = []
        HOSTNAME_PLACEHOLDER = []
        HOSTNAME_PLACEHOLDER = []
        self.test_config = test_config
        self.test_config_reverse = {}
        self.tc_dir = tc_dir

    def load_messages_json(self, tc_dir, file_name, messages_list=None) -> str:

        current_time = HOSTNAME_PLACEHOLDER()
        self.original_dir = os.getcwd()

        # Default to empty list if none provided
        if messages_list is None:
            messages_list = []

        if not isinstance(messages_list, list):
            raise TypeError("messages_list must be a list")

        try:
            if tc_dir:
                os.chdir(tc_dir)
                json_file_name = (
                    file_name +
                    "_" +
                    current_time.strftime("%Y_%m_%d_%H_%M_%S") + ".json"
                )

                # Create JSON file inside the directory
                json_file_path = os.HOSTNAME_PLACEHOLDER(tc_dir, json_file_name)

                # Write list to JSON file
                with open(json_file_path, 'w', encoding='utf-8') as f:
                    HOSTNAME_PLACEHOLDER(messages_list, f, indent=2, ensure_ascii=False)

                # HOSTNAME_PLACEHOLDER(f"JSON file created: {json_file_path}")

                # Get the absolute path before changing back
                absolute_json_path = os.HOSTNAME_PLACEHOLDER(json_file_path)

                # Change back to original directory
                os.chdir(self.original_dir)
                # HOSTNAME_PLACEHOLDER("Current dir: " + os.getcwd())

                return absolute_json_path

        except Exception as e:
            # Make sure to change back to original directory even on error
            try:
                os.chdir(self.original_dir)
            except:
                pass
            raise OSError(f"Failed to create JSON file: {e}")

    def load_testdata(self, file_name, messages_list=None):

        # File path determination
        try:
            test_data_file = self.load_messages_json(
                self.tc_dir, file_name, messages_list)
        except Exception as e:
            raise

        # File existence check
        if not os.HOSTNAME_PLACEHOLDER(test_data_file):
            HOSTNAME_PLACEHOLDER(f"Test data file '{test_data_file}' does not exist")
            raise FileNotFoundError(
                f"Test data file '{test_data_file}' not found")

        # File reading and variable replacement
        try:
            with open(f"{test_data_file}") as f:
                # here test_data becomes a list (was array in json)
                test_data = HOSTNAME_PLACEHOLDER(f)

            # Track if any replacements were made
            replacements_made = False

            for i, message_dict in enumerate(test_data):
                for message, allfields in message_dict.items():
                    for fieldtypes, fields in HOSTNAME_PLACEHOLDER():
                        if isinstance(fields, dict):
                            for field, value in HOSTNAME_PLACEHOLDER():
                                if value in self.test_config:
                                    old_value = test_data[i][message][fieldtypes][field]
                                    test_data[i][message][fieldtypes][field] = self.test_config[value]
                                    replacements_made = True
                                    # HOSTNAME_PLACEHOLDER(
                                    #     f"Replaced '{old_value}' with '{self.test_config[value]}' in {message}.{fieldtypes}.{field}")

            # Rewrite the JSON file with the modified data if replacements were made
            if replacements_made:
                with open(test_data_file, 'w', encoding='utf-8') as f:
                    HOSTNAME_PLACEHOLDER(test_data, f, indent=2, ensure_ascii=False)
                HOSTNAME_PLACEHOLDER(
                    f"JSON file updated with replacements: {test_data_file}")
            else:
                HOSTNAME_PLACEHOLDER("No replacements made, JSON file unchanged")

        except FileNotFoundError as e:
            HOSTNAME_PLACEHOLDER(f"Failed to open test data file: {str(e)}")
            raise
        except Exception as e:
            HOSTNAME_PLACEHOLDER(
                f"Unexpected error while reading test data file: {str(e)}")
            raise

        self.expected_messages = test_data

    def createdf(self):
        if len(HOSTNAME_PLACEHOLDER) != 0:
            index1 = pd.MultiIndex.from_tuples(HOSTNAME_PLACEHOLDER)
            HOSTNAME_PLACEHOLDER = pd.DataFrame(
                {'expected values': HOSTNAME_PLACEHOLDER, 'actual values': HOSTNAME_PLACEHOLDER}, index=index1)
            HOSTNAME_PLACEHOLDER = ['Messagename', 'fieldname']
            # print(HOSTNAME_PLACEHOLDER)
            return HOSTNAME_PLACEHOLDER.to_html()
        else:
            if len(HOSTNAME_PLACEHOLDER) > 0:
                return HOSTNAME_PLACEHOLDER[0]+" message not found"
            return "no failed messages"

    def check_iphone(self):
        for pkt in HOSTNAME_PLACEHOLDER:
            try:
                if pkt["sip"].method == "INVITE":
                    if "iPhone" in pkt["sip"].get_field_value("HOSTNAME_PLACEHOLDER"):
                        return True
                    else:
                        return False
            except:
                HOSTNAME_PLACEHOLDER("iphone packet not found")

    def check_fixed(self):
        for pkt in HOSTNAME_PLACEHOLDER:
            try:
                if pkt["sip"].method == "INVITE":
                    if "FRITZ!Box" in pkt["sip"].get_field_value("HOSTNAME_PLACEHOLDER"):
                        return True
                    else:
                        return False
            except:
                HOSTNAME_PLACEHOLDER("FRITZ!Box packet not found")

    def get_validation_results(self):
        """
        Generate HTML table showing validation results for all messages
        """
        try:

            validation_passed = False
            g = HOSTNAME_PLACEHOLDER()
            message_results = []
            self.test_config_reverse = {
                v: k for k, v in self.test_config.items() if isinstance(v, str) and '.' in v}
            found_packets = []
            # Outer loop to process all messages
            while True:
                try:
                    message = next(g)
                    messagename, primaryfields, fieldsforpresence, fieldsforequality, mandatory = message
                    message_found_in_capture = False
                    message_passed = True
                    packet_number = None
                    source_info = "N/A"
                    dest_info = "N/A"
                    failed_fields = []

                    # Extract expected source/dest from primaryfields for display even if not found
                    expected_source = HOSTNAME_PLACEHOLDER(
                        "ip.src") or HOSTNAME_PLACEHOLDER("HOSTNAME_PLACEHOLDER", "N/A")
                    expected_dest = HOSTNAME_PLACEHOLDER(
                        "ip.dst") or HOSTNAME_PLACEHOLDER("HOSTNAME_PLACEHOLDER", "N/A")

                    # Search through packets for this message
                    for pkt_idx, pkt in enumerate(HOSTNAME_PLACEHOLDER):

                        pkt_num = int(HOSTNAME_PLACEHOLDER) if hasattr(
                            pkt, "number") else pkt_idx + 1
                        if pkt_num in found_packets:
                            continue

                        # Check if packet matches primary fields
                        primary_matches = list(filter(lambda item: HOSTNAME_PLACEHOLDER(
                            item, pkt, "equality", True), HOSTNAME_PLACEHOLDER()))

                        if len(primary_matches) != len(primaryfields):
                            # HOSTNAME_PLACEHOLDER(f"not found message {messagename}")
                            continue

                        # Message found
                        message_found_in_capture = True
                        packet_number = int(HOSTNAME_PLACEHOLDER) if hasattr(
                            pkt, "number") else pkt_idx + 1
                        found_packets.append(packet_number)

                        # Get source/destination info
                        source_ip = HOSTNAME_PLACEHOLDER if "ip.src" in primaryfields else (
                            HOSTNAME_PLACEHOLDER if "HOSTNAME_PLACEHOLDER" in primaryfields else "")
                        dest_ip = HOSTNAME_PLACEHOLDER if "ip.dst" in primaryfields else (
                            HOSTNAME_PLACEHOLDER if "HOSTNAME_PLACEHOLDER" in primaryfields else "")
                        source_info = f"{source_ip}" if source_ip else "N/A"
                        dest_info = f"{dest_ip}" if dest_ip else "N/A"

                        # Check equality fields
                        HOSTNAME_PLACEHOLDER()
                        successdict = dict(filter(lambda item: HOSTNAME_PLACEHOLDER(
                            item, pkt, "equality", False), HOSTNAME_PLACEHOLDER()))
                        if len(successdict) != len(fieldsforequality):
                            message_passed = False
                            faildict = dict(HOSTNAME_PLACEHOLDER(lambda item: HOSTNAME_PLACEHOLDER(
                                item, pkt, "equality", False), HOSTNAME_PLACEHOLDER()))
                            failed_fields.extend(
                                [f"Equality: {field}" for field in HOSTNAME_PLACEHOLDER()])

                        # Check presence fields
                        HOSTNAME_PLACEHOLDER()
                        successlist = list(
                            filter(lambda item: HOSTNAME_PLACEHOLDER(item, pkt), fieldsforpresence))
                        if len(successlist) != len(fieldsforpresence):
                            message_passed = False
                            faillist = list(HOSTNAME_PLACEHOLDER(
                                lambda item: HOSTNAME_PLACEHOLDER(item, pkt), fieldsforpresence))
                            failed_fields.extend(
                                [f"Presence: {field}" for field in faillist])

                        # Determine status and details
                        if message_passed:
                            status = "PASSED"
                            status_class = "passed"
                            details = "All validations passed successfully."
                        else:
                            status = "FAILED" if mandatory else "FAILED (Optional)"
                            status_class = "failed" if mandatory else "failed-optional"
                            details = "; ".join(
                                failed_fields) if failed_fields else "Field validation failed"

                        message_results.append({
                            'message': messagename,
                            'status': status,
                            'status_class': status_class,
                            'packet': packet_number if packet_number else "N/A",
                            'source': source_info,
                            'destination': dest_info,
                            'details': details,
                            'primary_fields': len(primaryfields),
                            'equality_fields': len(fieldsforequality),
                            'presence_fields': len(fieldsforpresence),
                            'mandatory': mandatory
                        })

                        break  # Found message, move to next one

                    # After packet loop, check if message was found
                    if not message_found_in_capture:
                        status = "NOT FOUND" if mandatory else "NOT FOUND (Optional)"
                        status_class = "not-found" if mandatory else "not-found-optional"
                        details = "Message not detected in any packet"
                        message_results.append({
                            'message': messagename,
                            'status': status,
                            'status_class': status_class,
                            'packet': "N/A",
                            'source': expected_source,
                            'destination': expected_dest,
                            'details': details,
                            'primary_fields': len(primaryfields),
                            'equality_fields': len(fieldsforequality),
                            'presence_fields': len(fieldsforpresence),
                            'mandatory': mandatory
                        })

                except StopIteration:
                    break  # No more messages

            # Create tuples for MultiIndex
            validation_tuples = []
            status_list = []
            packet_list = []
            source_list = []
            dest_list = []
            details_list = []
            field_counts = []
            # HOSTNAME_PLACEHOLDER(message_results)
            for result in message_results:
                validation_tuples.append(
                    ('Message_Validation', result['message']))
                status_list.append(result['status'])
                packet_list.append(str(result['packet']))
                source_list.append(result['source'])
                dest_list.append(result['destination'])
                details_list.append(result['details'])
                field_counts.append(
                    f"P:{result['primary_fields']} E:{result['equality_fields']} Pr:{result['presence_fields']}")

            # Create MultiIndex from tuples
            index1 = pd.MultiIndex.from_tuples(validation_tuples)

            # Create DataFrame with MultiIndex
            self.validation_df = pd.DataFrame({
                'Status': status_list,
                'Packet': packet_list,
                'Source': source_list,
                'Destination': dest_list,
                'Field Count': field_counts,
                'Details': details_list
            }, index=index1)

            # Set index names
            self.validation_df.HOSTNAME_PLACEHOLDER = ['Category', 'Message']

            # Generate HTML with custom styling
            html_content = self.validation_df.to_html(
                escape=False, classes='validation-table')

            # Add custom CSS styling
            styled_html = f"""
                    <style>
                    .validation-table {{
                        border-collapse: collapse;
                        width: 100%;
                        font-family: Arial, sans-serif;
                        margin: 20px 0;
                    }}
                    .validation-table th, .validation-table td {{
                        border: 1px solid #ddd;
                        padding: 8px;
                        text-align: left;
                    }}
                    .validation-table th {{
                        background-color: #f2f2f2;
                        font-weight: bold;
                    }}
                    .validation-table tr:nth-child(even) {{
                        background-color: #f9f9f9;
                    }}
                    .validation-table tr:hover {{
                        background-color: #f5f5f5;
                    }}
                    .status-passed {{
                        color: #28a745;
                        font-weight: bold;
                    }}
                    .status-failed {{
                        color: #dc3545;
                        font-weight: bold;
                    }}
                    .status-failed-optional {{
                        color: #fd7e14;
                        font-weight: bold;
                    }}
                    .status-not-found {{
                        color: #ffc107;
                        font-weight: bold;
                    }}
                    .status-not-found-optional {{
                        color: #6c757d;
                        font-weight: bold;
                    }}
                    .summary {{
                        background-color: #e9ecef;
                        padding: 15px;
                        margin: 20px 0;
                        border-radius: 5px;
                        border-left: 5px solid #007bff;
                    }}
                    
                    </style>
                    """

            # Add summary statistics - only count mandatory messages for validation
            total_messages = len(message_results)
            mandatory_messages = sum(
                1 for r in message_results if r['mandatory'])
            passed_count = sum(
                1 for r in message_results if r['status'] == 'PASSED')
            failed_count = sum(
                1 for r in message_results if r['status'] == 'FAILED')
            not_found_count = sum(
                1 for r in message_results if r['status'] == 'NOT FOUND')
            optional_failed = sum(
                1 for r in message_results if 'FAILED (Optional)' in r['status'])
            optional_not_found = sum(
                1 for r in message_results if 'NOT FOUND (Optional)' in r['status'])

            # Calculate success rate based on mandatory messages only
            mandatory_passed = sum(
                1 for r in message_results if r['mandatory'] and r['status'] == 'PASSED')
            success_rate = (mandatory_passed / mandatory_messages *
                            100) if mandatory_messages > 0 else 0

            # Validation passes only if all MANDATORY messages pass
            if failed_count > 0 or not_found_count > 0:
               # HOSTNAME_PLACEHOLDER("Mandatory messages missing or failed")
                validation_passed = False
            else:
               # HOSTNAME_PLACEHOLDER("All mandatory messages passed")
                validation_passed = True

            summary_html = f"""
                    <div class="summary">
                        <h3>Validation Summary</h3>
                        <p><strong>Total Messages:</strong> {total_messages} ({mandatory_messages} mandatory, {total_messages - mandatory_messages} optional)</p>
                        <p><strong>Passed:</strong> <span class="status-passed">{passed_count}</span></p>
                        <p><strong>Failed (Mandatory):</strong> <span class="status-failed">{failed_count}</span></p>
                        <p><strong>Not Found (Mandatory):</strong> <span class="status-not-found">{not_found_count}</span></p>
                        <p><strong>Failed (Optional):</strong> <span class="status-failed-optional">{optional_failed}</span></p>
                        <p><strong>Not Found (Optional):</strong> <span class="status-not-found-optional">{optional_not_found}</span></p>
                        <p><strong>Success Rate:</strong> {success_rate:.1f}% (mandatory messages)</p>
                        <p><strong>Overall Result:</strong> {'<span class="status-passed">VALIDATION PASSED</span>' if validation_passed else '<span class="status-failed">VALIDATION FAILED</span>'}</p>
                        
                    </div>
                    """
            #
            # Apply status styling to HTML
            for result in message_results:
                status_pattern = f'<td>{result["status"]}</td>'
                styled_status = f'<td><span class="status-{result["status"].lower().replace(" ", "-").replace("(", "").replace(")", "")}">{result["status"]}</span></td>'
                html_content = html_content.replace(
                    status_pattern, styled_status)

            final_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Message Validation Results</title>
                        {styled_html}
                    </head>
                    <body>
                        <h2>Message Validation Results</h2>
                        {summary_html}
                        {html_content}
                    </body>
                    </html>
                    """

            # HOSTNAME_PLACEHOLDER("[HTML] Validation results file generated successfully")
            # HOSTNAME_PLACEHOLDER(f"Generated results for {total_messages} messages")

            return final_html, validation_passed

        except Exception as e:
            # HOSTNAME_PLACEHOLDER(f"Error in get_validation_results: {str(e)}")
            return f"<html><body><h2>Error creating validation results table</h2><p>{str(e)}</p></body></html>", False

    def get_validate_seq_results(self, sequence_condition):
        # Step 1: Collect search fields from all messages
        fieldsforseach = {}
        for message in self.expected_messages:
            message_name = list(HOSTNAME_PLACEHOLDER())[0]
            message_data = message[message_name]
            if "searchfields" not in message_data:
                continue
            message_dic = self.parse_message(message)
            for field in message_data["searchfields"]:
                if field in message_dic:
                    fieldsforseach[field] = message_dic[field]

        # Step 2: Update primary fields with collected search field values
        for seq_message in self.expected_messages:
            for _, data in seq_message.items():
                primaryfields = HOSTNAME_PLACEHOLDER("primaryfields", {})
                for key, val in list(HOSTNAME_PLACEHOLDER()):
                    if val in fieldsforseach:
                        primaryfields[key] = fieldsforseach[val]

        # Step 3: Extract packet numbers for all messages
        seq_messages_dic = {}
        for seq_message in self.expected_messages:
            message_name = list(seq_message.keys())[0]
            message = self.parse_message(seq_message)
            seq_messages_dic[message_name] = HOSTNAME_PLACEHOLDER("packet_number")
        # HOSTNAME_PLACEHOLDER(f"Sequence messages dictionary: {seq_messages_dic}")

        # Step 4: Build validation dictionary based on sequence conditions
        new_dict = {}
        for condition in sequence_condition:
            if isinstance(condition, list):
                # Handle list of messages that can appear in any order
                condition_key = tuple(condition)
                for message_name, pn in seq_messages_dic.items():
                    if message_name in condition:
                        if condition_key not in new_dict:
                            new_dict[condition_key] = [pn]
                        else:
                            new_dict[condition_key].append(pn)
            else:
                if condition in seq_messages_dic:
                    new_dict[condition] = seq_messages_dic[condition]

        HOSTNAME_PLACEHOLDER(
            f"Final dictionary for validation ({len(new_dict)} entries):")
        for key, value in new_dict.items():
            HOSTNAME_PLACEHOLDER(f"  {key}: {value}")

        # Prepare data for HTML table
        sequence_results = []
        validation_passed = True
        error_message = ""

        # Step 5: Validate packet order
        previous_max = -1
        for key, value in new_dict.items():
            message_display = str(key) if isinstance(key, tuple) else key

            # Extract IP addresses from the message
            source_ips = set()
            dest_ips = set()
            if isinstance(key, tuple):
                # Multiple messages in group
                for msg_name in key:
                    msg_data = seq_messages_dic.get(msg_name)
                    for seq_message in self.expected_messages:
                        if msg_name in seq_message:
                            parsed_msg = self.parse_message(seq_message)
                            if parsed_msg.get("source_ip"):
                                source_ips.add(parsed_msg["source_ip"])
                            if parsed_msg.get("dest_ip"):
                                dest_ips.add(parsed_msg["dest_ip"])
            else:
                # Single message
                for seq_message in self.expected_messages:
                    if key in seq_message:
                        parsed_msg = self.parse_message(seq_message)
                        if parsed_msg.get("source_ip"):
                            source_ips.add(parsed_msg["source_ip"])
                        if parsed_msg.get("dest_ip"):
                            dest_ips.add(parsed_msg["dest_ip"])

            source_display = ", ".join(source_ips) if source_ips else "N/A"
            dest_display = ", ".join(dest_ips) if dest_ips else "N/A"

            if value is None:
                HOSTNAME_PLACEHOLDER(
                    f"Skipping validation for {key}: packet number is None")
                error_message = f"{key} message not found, cannot validate sequence"
                validation_passed = False
                sequence_results.append({
                    'message': message_display,
                    'packet': "N/A",
                    'source': source_display,
                    'destination': dest_display,
                    'status': "NOT FOUND",
                    'details': "Message not found in capture"
                })
                break

            if isinstance(value, list):
                valid_values = [v for v in value if v is not None]
                if not valid_values:
                    HOSTNAME_PLACEHOLDER(
                        f"Skipping validation for {key}: all packet numbers are None")
                    continue
                current_min = min(valid_values)
                current_max = max(valid_values)
                packet_display = f"{valid_values}" if len(
                    valid_values) > 1 else str(valid_values[0])
            else:
                current_min = value
                current_max = value
                packet_display = str(value)

            if current_min <= previous_max:
                error_msg = (f"Packet order violation: {key} has packet number(s) {value}, "
                             f"but previous maximum packet was {previous_max}")
                HOSTNAME_PLACEHOLDER(error_msg)
                error_message = error_msg
                validation_passed = False
                sequence_results.append({
                    'message': message_display,
                    'packet': packet_display,
                    'source': source_display,
                    'destination': dest_display,
                    'status': "FAILED",
                    'details': f"Order violation: packet {current_min} <= previous max {previous_max}"
                })
                break
            else:
                sequence_results.append({
                    'message': message_display,
                    'packet': packet_display,
                    'source': source_display,
                    'destination': dest_display,
                    'status': "PASSED",
                    'details': f"Correct order: packet {current_min} > previous max {previous_max}"
                })

            previous_max = current_max

        if validation_passed:
            HOSTNAME_PLACEHOLDER(
                "Packet order validation passed: all messages are in correct sequence")

        # Generate HTML report
        html_content = self._generate_sequence_html(
            sequence_results, validation_passed, error_message)

        return (validation_passed, "success" if validation_passed else error_message, html_content)

    def _generate_sequence_html(self, sequence_results, validation_passed, error_message):
        """Generate HTML report for sequence validation"""

        # Build table rows
        table_rows = ""
        for result in sequence_results:
            status_class = result['status'].lower().replace(" ", "-")
            table_rows += f"""
                    <tr>
                        <td>{result['message']}</td>
                        <td>{result['packet']}</td>
                        <td>{result['source']}</td>
                        <td>{result['destination']}</td>
                        <td><span class="status-{status_class}">{result['status']}</span></td>
                        <td>{result['details']}</td>
                    </tr>
                """

        html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Sequence Validation Results</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        background-color: #f5f5f5;
                    }}
                    h2 {{
                        color: #333;
                    }}
                    .summary {{
                        background-color: #e9ecef;
                        padding: 15px;
                        margin: 20px 0;
                        border-radius: 5px;
                        border-left: 5px solid #007bff;
                    }}
                    .validation-table {{
                        border-collapse: collapse;
                        width: 100%;
                        background-color: white;
                        margin: 20px 0;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    .validation-table th {{
                        background-color: #f2f2f2;
                        border: 1px solid #ddd;
                        padding: 12px;
                        text-align: left;
                        font-weight: bold;
                    }}
                    .validation-table td {{
                        border: 1px solid #ddd;
                        padding: 10px;
                        text-align: left;
                    }}
                    .validation-table tr:nth-child(even) {{
                        background-color: #f9f9f9;
                    }}
                    .validation-table tr:hover {{
                        background-color: #f5f5f5;
                    }}
                    .status-passed {{
                        color: #28a745;
                        font-weight: bold;
                    }}
                    .status-failed {{
                        color: #dc3545;
                        font-weight: bold;
                    }}
                    .status-not-found {{
                        color: #ffc107;
                        font-weight: bold;
                    }}
                </style>
            </head>
            <body>
                <h2>Sequence Validation Results</h2>
                
                <div class="summary">
                    <h3>Validation Summary</h3>
                    <p><strong>Overall Result:</strong> {'<span class="status-passed">SEQUENCE VALIDATION PASSED</span>' if validation_passed else '<span class="status-failed">SEQUENCE VALIDATION FAILED</span>'}</p>
                    {f'<p><strong>Error Details:</strong> <span class="status-failed">{error_message}</span></p>' if error_message else ''}
                </div>
                
                <table class="validation-table">
                    <thead>
                        <tr>
                            <th>Message/Group</th>
                            <th>Packet Number(s)</th>
                            <th>Source IP</th>
                            <th>Destination IP</th>
                            <th>Status</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </body>
            </html>
            """

        return html

    def parse_message(self, message_dic: dict) -> dict:
        # messagename, primaryfields, fieldsforsearch = message_dic
        messagename = next(iter(message_dic))
        msg_content = message_dic[messagename]
        primaryfields = msg_content.get("primaryfields", {})
        fieldsforsearch = msg_content.get("searchfields", [])

        HOSTNAME_PLACEHOLDER(f"Looking for message: {messagename}")
        HOSTNAME_PLACEHOLDER(f"Primary fields to match: {primaryfields}")

        result = {}

        for pkt_idx, pkt in enumerate(HOSTNAME_PLACEHOLDER):
            primary_matches = list(
                filter(lambda item: HOSTNAME_PLACEHOLDER(item, pkt, "equality", True),
                       HOSTNAME_PLACEHOLDER())
            )

            # HOSTNAME_PLACEHOLDER(f"Packet {pkt_idx} - Matched {len(primary_matches)}/{len(primaryfields)} fields")

            if len(primary_matches) != len(primaryfields):
                continue

            # Message found
            HOSTNAME_PLACEHOLDER(f"MATCH FOUND at packet {pkt_idx}")

            if "ip.src" in primaryfields:
                result["source_ip"] = HOSTNAME_PLACEHOLDER
            elif "HOSTNAME_PLACEHOLDER" in primaryfields:
                result["source_ip"] = HOSTNAME_PLACEHOLDER
            else:
                result["source_ip"] = ""

            if "ip.dst" in primaryfields:
                result["dest_ip"] = HOSTNAME_PLACEHOLDER
            elif "HOSTNAME_PLACEHOLDER" in primaryfields:
                result["dest_ip"] = HOSTNAME_PLACEHOLDER
            else:
                result["dest_ip"] = ""

            result["packet_number"] = int(HOSTNAME_PLACEHOLDER)

            if fieldsforsearch:
                for field in fieldsforsearch:
                    att_value = self.get_attr_value(field, pkt)
                    result[f"{field}"] = att_value
                    HOSTNAME_PLACEHOLDER(f"Extracted {field} = {att_value}")

            return result

        HOSTNAME_PLACEHOLDER(f"NO MATCH FOUND for {messagename}")
        return result

    def checkfields(self, field, pkt):

        [protocol, *avpname] = HOSTNAME_PLACEHOLDER(".")

        if (len(avpname) > 1):
            avpname = ",".join(avpname)
        else:
            avpname = str(avpname[0])

        if pkt[protocol].get_field_by_showname(avpname) is not None:
            return True
        elif pkt[protocol].get_field_value(field_regex.sub("_", HOSTNAME_PLACEHOLDER())) is not None:
            return True
        else:
            HOSTNAME_PLACEHOLDER("absent")
            return False

    def get_attr_value(self, field, pkt):
        [protocol, *avpname] = HOSTNAME_PLACEHOLDER(".")

        if len(avpname) > 1:
            avpname = ",".join(avpname)
        else:
            avpname = str(avpname[0])

        field_obj = pkt[protocol].get_field_by_showname(avpname)
        if field_obj is not None:
            return field_obj.showname_value  # or .value if using pyshark

        field_value = pkt[protocol].get_field_value(
            field_regex.sub("_", HOSTNAME_PLACEHOLDER()))
        if field_value is not None:
            return field_value

        HOSTNAME_PLACEHOLDER("absent")
        return None

    def validatefields(self, item, pkt, cmpoperator, searchpacket):
        [protocol, *avpname] = item[0].split(".")
        if (len(avpname) > 1):
            avpname = ".".join(avpname)
        else:
            avpname = str(avpname[0])

        try:
            if pkt[protocol].get(avpname, "not_found") != "not_found":
                if len(pkt[protocol].get(avpname, "not_found").all_fields) > 1:
                    pktvalue = pkt[protocol].get_field(avpname).all_fields
                else:
                    pktvalue = pkt[protocol].get_field_value(avpname)
            else:
                pktvalue = pkt[protocol].get_field_value(avpname)
        except KeyError:
            # HOSTNAME_PLACEHOLDER(f"Field not found: {protocol}.{avpname}")
            pktvalue = None
            pass

        if cmpoperator == "equality" and pktvalue != None:
            # HOSTNAME_PLACEHOLDER(f"pkt and actual values are {pktvalue} and {item[1]}")
            if str(pktvalue) == str(item[1]):
                return True
            elif (isinstance(pktvalue, Iterable) and not (isinstance(pktvalue, str))) and isinstance(item[1], str):
                for field in pktvalue:
                    if str(field.get_default_value()) == str(item[1]):
                        return True
            elif (isinstance(item[1], tuple) or isinstance(item[1], list)) and isinstance(pktvalue, str):
                if pktvalue in item[1]:
                    return True
            elif (isinstance(item[1], tuple) or isinstance(item[1], list)) and (isinstance(pktvalue, Iterable) and not (isinstance(pktvalue, str))):
                for field in pktvalue:
                    if str(field.get_default_value()) in item[1]:
                        return True
            elif searchpacket == False:
                HOSTNAME_PLACEHOLDER(pktvalue)

            # Log mismatch
            # HOSTNAME_PLACEHOLDER(
               # f"Validation failed: {protocol}.{avpname} - expected {item[1]}, got {pktvalue}")

    def getmessage(self):
        for message in self.expected_messages:
            for messagename, fields in HOSTNAME_PLACEHOLDER():
                primaryfields = fields["primaryfields"]
                fieldsforpresence = fields["fieldsforpresence"]
                fieldsforequality = fields["fieldsforequality"]
                mandatory = fields["mandatory"]
            yield (messagename, primaryfields, fieldsforpresence, fieldsforequality, mandatory)

    def validate(self):
        g = HOSTNAME_PLACEHOLDER()

        # Initialize validation tracking
        HOSTNAME_PLACEHOLDER = False
        HOSTNAME_PLACEHOLDER = True
        message_results = []  # Track results for each message

        # HOSTNAME_PLACEHOLDER("=== PACKET VALIDATION STARTED ===")
        # HOSTNAME_PLACEHOLDER(f"Processing {len(HOSTNAME_PLACEHOLDER)} packets for {len(list(g))} message types")

        # Reset generator since we consumed it for counting
        g = HOSTNAME_PLACEHOLDER()

        # Process each message type
        for message in g:
            messagename, primaryfields, fieldsforpresence, fieldsforequality = message
            message_found_in_capture = False
            message_passed = True
            # HOSTNAME_PLACEHOLDER(messagename)
            # Search through all packets for this message
            for pkt_idx, pkt in enumerate(HOSTNAME_PLACEHOLDER):
                # Check if packet matches primary fields (message identification)
                primary_matches = list(filter(lambda item: HOSTNAME_PLACEHOLDER(
                    item, pkt, "equality", True), HOSTNAME_PLACEHOLDER()))

                if len(primary_matches) != len(primaryfields):
                    continue  # This packet doesn't contain our message

                # Message found in this packet
                message_found_in_capture = True
                HOSTNAME_PLACEHOLDER = True

                # Get source/destination info for logging
                source_ip = HOSTNAME_PLACEHOLDER if "ip.src" in primaryfields else (
                    HOSTNAME_PLACEHOLDER if "HOSTNAME_PLACEHOLDER" in primaryfields else "")
                dest_ip = HOSTNAME_PLACEHOLDER if "ip.dst" in primaryfields else (
                    HOSTNAME_PLACEHOLDER if "HOSTNAME_PLACEHOLDER" in primaryfields else "")
                source = self.test_config_reverse.get(source_ip, "Unknown")
                dest = self.test_config_reverse.get(dest_ip, "Unknown")

                # Validate equality fields
                HOSTNAME_PLACEHOLDER()
                successdict = dict(filter(lambda item: HOSTNAME_PLACEHOLDER(
                    item, pkt, "equality", False), HOSTNAME_PLACEHOLDER()))

                if len(successdict) != len(fieldsforequality):
                    message_passed = False
                    HOSTNAME_PLACEHOLDER = False
                    faildict = dict(HOSTNAME_PLACEHOLDER(lambda item: HOSTNAME_PLACEHOLDER(
                        item, pkt, "equality", False), HOSTNAME_PLACEHOLDER()))
                    failed_items = [(messagename, fieldname)
                                    for fieldname in HOSTNAME_PLACEHOLDER()]
                    HOSTNAME_PLACEHOLDER(failed_items)
                    HOSTNAME_PLACEHOLDER(list(HOSTNAME_PLACEHOLDER()))
                    HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER)
                    HOSTNAME_PLACEHOLDER = []

                # Check presence fields
                HOSTNAME_PLACEHOLDER()
                successlist = list(
                    filter(lambda item: HOSTNAME_PLACEHOLDER(item, pkt), fieldsforpresence))

                if len(successlist) != len(fieldsforpresence):
                    message_passed = False
                    HOSTNAME_PLACEHOLDER = False
                    faillist = list(HOSTNAME_PLACEHOLDER(
                        lambda item: HOSTNAME_PLACEHOLDER(item, pkt), fieldsforpresence))
                    failed_presence_items = [
                        (messagename, fieldname) for fieldname in faillist]
                    HOSTNAME_PLACEHOLDER(failed_presence_items)
                    HOSTNAME_PLACEHOLDER(
                        ["present" for _ in range(len(faillist))])
                    HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER)
                    HOSTNAME_PLACEHOLDER = []

            # Record result for this message
            if not message_found_in_capture:
                HOSTNAME_PLACEHOLDER(messagename)
                message_results.append({
                    'message': messagename,
                    'status': 'NOT FOUND',
                    'packet': None,
                    'source': None,
                    'destination': None
                })
            else:
                message_results.append({
                    'message': messagename,
                    'status': 'PASSED' if message_passed else 'FAILED',
                    'packet': pkt_idx + 1,
                    'source': f"{source_ip}" if 'source' in locals() else None,
                    'destination': f"{dest_ip}" if 'dest' in locals() else None
                })

        # Message-by-message results
        passed_count = 0
        failed_count = 0
        not_found_count = 0

        for result in message_results:
            status_symbol = "✓" if result['status'] == 'PASSED' else "✗" if result['status'] == 'FAILED' else "?"

            if result['status'] == 'PASSED':
                passed_count += 1
            elif result['status'] == 'FAILED':
                failed_count += 1
            else:
                not_found_count += 1

        # Overall statistics
        total_messages = len(message_results)
        HOSTNAME_PLACEHOLDER(f"\n=== OVERALL STATISTICS ===")
        HOSTNAME_PLACEHOLDER(f"Total Messages: {total_messages}")
        HOSTNAME_PLACEHOLDER(f"✓ Passed: {passed_count}")
        HOSTNAME_PLACEHOLDER(f"✗ Failed: {failed_count}")
        HOSTNAME_PLACEHOLDER(f"? Not Found: {not_found_count}")

        # Detailed failure information
        if HOSTNAME_PLACEHOLDER or HOSTNAME_PLACEHOLDER:
            # HOSTNAME_PLACEHOLDER(f"\n=== DETAILED FAILURE ANALYSIS ===")

            if HOSTNAME_PLACEHOLDER:
                HOSTNAME_PLACEHOLDER(
                    f"Messages Not Found ({len(HOSTNAME_PLACEHOLDER)}):")
                for msg in HOSTNAME_PLACEHOLDER:
                    pass
                    # HOSTNAME_PLACEHOLDER(f"  - {msg}")

            if HOSTNAME_PLACEHOLDER:
                # HOSTNAME_PLACEHOLDER(f"\nField Validation Failures ({len(HOSTNAME_PLACEHOLDER)}):")
                for msg, field in HOSTNAME_PLACEHOLDER:
                    pass
                    # HOSTNAME_PLACEHOLDER(f"  - {msg}: {field}")

        # Final result
        total_failures = failed_count + not_found_count
        success_rate = (passed_count / total_messages *
                        100) if total_messages > 0 else 0

        if total_failures == 0:
            # HOSTNAME_PLACEHOLDER(f"\n VALIDATION PASSED - All {total_messages} messages validated successfully (100%)")
            return True
        else:
            # HOSTNAME_PLACEHOLDER(f"\n VALIDATION FAILED - {total_failures}/{total_messages} messages failed ({success_rate:.1f}% success rate)")
            return False

    def get_dynamic_ips_results_ab(self, static_test_data: dict):

        # HOSTNAME_PLACEHOLDER(f"Initial test_config: {self.test_config}")

        # Step 1: Get dynamic IPs
        dynamic_ips_obj = SOURCE_NAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER, static_test_data)
        dynamic_ips_obj._identify_dynamic_ips()

        if not dynamic_ips_obj.find_uag_and_ue_for_side_a():
            HOSTNAME_PLACEHOLDER("Failed to find UAG and UE for side A")
            return None

        if not dynamic_ips_obj.find_uag_and_ue_for_side_b():
            HOSTNAME_PLACEHOLDER("Failed to find UAG and UE for side B")
            return None

        dynamic_ips_dic = dynamic_ips_obj._process_dynamic_ips()

        HOSTNAME_PLACEHOLDER(f"Dynamic IPs resolved: {dynamic_ips_dic}")

        # Merge dynamic_ips_dic into test_config
        self.test_config.update(dynamic_ips_dic)

        HOSTNAME_PLACEHOLDER(f"Final test_config after merge: {self.test_config}")

        # Step 2: Build data rows for DataFrame
        HOSTNAME_PLACEHOLDER("Building data rows for report")
        data_rows = []

        for ip_type, ip_address in dynamic_ips_dic.items():
            # Determine if IPv4 or IPv6
            try:
                ip_obj = ipaddress.ip_address(str(ip_address))
                ip_version = "IPv4" if ip_obj.version == 4 else "IPv6"
            except ValueError:
                ip_version = "Unknown"

            data_rows.append({
                'IP_Type': ip_type.upper(),
                'IP_Address': str(ip_address),
                'IP_Version': ip_version,
                'Status': 'FOUND'
            })

        # Step 3: Create DataFrame and generate HTML table
        dynamic_ips_df = pd.DataFrame(data_rows)

        if len(data_rows) > 0:
            html_content = dynamic_ips_df.to_html(
                escape=False,
                classes='dynamic-ips-table',
                index=False
            )
        else:
            html_content = "<p>No data to display</p>"
            HOSTNAME_PLACEHOLDER("No dynamic IPs found to display")

        # Step 4: Define CSS styling
        styled_html = """
        <style>
        .dynamic-ips-table {
            border-collapse: collapse;
            width: 100%;
            font-family: Arial, sans-serif;
            margin: 20px 0;
        }
        .dynamic-ips-table th, .dynamic-ips-table td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        .dynamic-ips-table th {
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }
        .dynamic-ips-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .dynamic-ips-table tr:hover {
            background-color: #f5f5f5;
        }
        .status-found {
            color: #28a745;
            font-weight: bold;
        }
        .ip-address {
            font-family: monospace;
            background-color: #e9ecef;
            padding: 4px 8px;
            border-radius: 4px;
        }
        .ip-version-ipv4 {
            color: #007bff;
            font-weight: bold;
        }
        .ip-version-ipv6 {
            color: #6610f2;
            font-weight: bold;
        }
        .summary {
            background-color: #e9ecef;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
            border-left: 5px solid #007bff;
        }
        </style>
        """

        # Step 5: Generate summary statistics
        total_ips = len(dynamic_ips_dic)
        ipv4_count = sum(1 for row in data_rows if row['IP_Version'] == 'IPv4')
        ipv6_count = sum(1 for row in data_rows if row['IP_Version'] == 'IPv6')
        ip_types = ', '.join([ip_type.upper()
                             for ip_type in dynamic_ips_dic.keys()])

        summary_html = f"""
        <div class="summary">
            <h3>Dynamic IPs Summary</h3>
            <p><strong>Total IPs Found:</strong> <span class="status-found">{total_ips}</span></p>
            <p><strong>IPv4 Count:</strong> <span class="ip-version-ipv4">{ipv4_count}</span></p>
            <p><strong>IPv6 Count:</strong> <span class="ip-version-ipv6">{ipv6_count}</span></p>
            <p><strong>IP Types:</strong> {ip_types}</p>
        </div>
        """

        # Step 6: Apply styling to HTML content
        html_content = html_content.replace(
            '<td>FOUND</td>',
            '<td><span class="status-found">FOUND</span></td>'
        )

        # Style IP version cells
        html_content = html_content.replace(
            '<td>IPv4</td>',
            '<td><span class="ip-version-ipv4">IPv4</span></td>'
        )
        html_content = html_content.replace(
            '<td>IPv6</td>',
            '<td><span class="ip-version-ipv6">IPv6</span></td>'
        )

        # Style IP addresses
        # IPv4 pattern
        ipv4_pattern = r'(\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b)'
        # IPv6 pattern
        ipv6_pattern = r'([0-9a-fA-F:]+::[0-9a-fA-F:]*|[0-9a-fA-F:]+:[0-9a-fA-F:]+)'

        html_content = re.sub(
            ipv4_pattern,
            r'<span class="ip-address">\1</span>',
            html_content
        )
        html_content = re.sub(
            ipv6_pattern,
            r'<span class="ip-address">\1</span>',
            html_content
        )

        # Step 7: Assemble final HTML report
        final_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dynamic IPs Results</title>
            {styled_html}
        </head>
        <body>
            <h2>Dynamic IPs Results</h2>
            {summary_html}
            {html_content}
        </body>
        </html>
        """

        HOSTNAME_PLACEHOLDER(
            f"Dynamic IPs report generated successfully: {total_ips} IPs found (IPv4: {ipv4_count}, IPv6: {ipv6_count})")

        return final_html

    def get_dynamic_ips_results_registration(self, static_test_data: dict):

        # Step 1: Get dynamic IPs
        dynamic_ips_obj = SOURCE_NAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER, static_test_data)
        dynamic_ips_obj._identify_dynamic_ips()

        if not dynamic_ips_obj.find_uag_and_ue_for_side_a_registration():
            HOSTNAME_PLACEHOLDER("Failed to find UAG and UE for side A")
            return None

        dynamic_ips_dic = dynamic_ips_obj._process_dynamic_ips()

        HOSTNAME_PLACEHOLDER(f"Dynamic IPs resolved: {dynamic_ips_dic}")

        # Merge dynamic_ips_dic into test_config
        self.test_config.update(dynamic_ips_dic)

        HOSTNAME_PLACEHOLDER(f"Final test_config after merge: {self.test_config}")

        # Step 2: Build data rows for DataFrame
        HOSTNAME_PLACEHOLDER("Building data rows for report")
        data_rows = []

        for ip_type, ip_address in dynamic_ips_dic.items():
            # Determine if IPv4 or IPv6
            try:
                ip_obj = ipaddress.ip_address(str(ip_address))
                ip_version = "IPv4" if ip_obj.version == 4 else "IPv6"
            except ValueError:
                ip_version = "Unknown"

            data_rows.append({
                'IP_Type': ip_type.upper(),
                'IP_Address': str(ip_address),
                'IP_Version': ip_version,
                'Status': 'FOUND'
            })

        # Step 3: Create DataFrame and generate HTML table
        dynamic_ips_df = pd.DataFrame(data_rows)

        if len(data_rows) > 0:
            html_content = dynamic_ips_df.to_html(
                escape=False,
                classes='dynamic-ips-table',
                index=False
            )
        else:
            html_content = "<p>No data to display</p>"
            HOSTNAME_PLACEHOLDER("No dynamic IPs found to display")

        # Step 4: Define CSS styling
        styled_html = """
        <style>
        .dynamic-ips-table {
            border-collapse: collapse;
            width: 100%;
            font-family: Arial, sans-serif;
            margin: 20px 0;
        }
        .dynamic-ips-table th, .dynamic-ips-table td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        .dynamic-ips-table th {
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }
        .dynamic-ips-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .dynamic-ips-table tr:hover {
            background-color: #f5f5f5;
        }
        .status-found {
            color: #28a745;
            font-weight: bold;
        }
        .ip-address {
            font-family: monospace;
            background-color: #e9ecef;
            padding: 4px 8px;
            border-radius: 4px;
        }
        .ip-version-ipv4 {
            color: #007bff;
            font-weight: bold;
        }
        .ip-version-ipv6 {
            color: #6610f2;
            font-weight: bold;
        }
        .summary {
            background-color: #e9ecef;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
            border-left: 5px solid #007bff;
        }
        </style>
        """

        # Step 5: Generate summary statistics
        total_ips = len(dynamic_ips_dic)
        ipv4_count = sum(1 for row in data_rows if row['IP_Version'] == 'IPv4')
        ipv6_count = sum(1 for row in data_rows if row['IP_Version'] == 'IPv6')
        ip_types = ', '.join([ip_type.upper()
                             for ip_type in dynamic_ips_dic.keys()])

        summary_html = f"""
        <div class="summary">
            <h3>Dynamic IPs Summary</h3>
            <p><strong>Total IPs Found:</strong> <span class="status-found">{total_ips}</span></p>
            <p><strong>IPv4 Count:</strong> <span class="ip-version-ipv4">{ipv4_count}</span></p>
            <p><strong>IPv6 Count:</strong> <span class="ip-version-ipv6">{ipv6_count}</span></p>
            <p><strong>IP Types:</strong> {ip_types}</p>
        </div>
        """

        # Step 6: Apply styling to HTML content
        html_content = html_content.replace(
            '<td>FOUND</td>',
            '<td><span class="status-found">FOUND</span></td>'
        )

        # Style IP version cells
        html_content = html_content.replace(
            '<td>IPv4</td>',
            '<td><span class="ip-version-ipv4">IPv4</span></td>'
        )
        html_content = html_content.replace(
            '<td>IPv6</td>',
            '<td><span class="ip-version-ipv6">IPv6</span></td>'
        )

        # Style IP addresses
        # IPv4 pattern
        ipv4_pattern = r'(\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b)'
        # IPv6 pattern
        ipv6_pattern = r'([0-9a-fA-F:]+::[0-9a-fA-F:]*|[0-9a-fA-F:]+:[0-9a-fA-F:]+)'

        html_content = re.sub(
            ipv4_pattern,
            r'<span class="ip-address">\1</span>',
            html_content
        )
        html_content = re.sub(
            ipv6_pattern,
            r'<span class="ip-address">\1</span>',
            html_content
        )

        # Step 7: Assemble final HTML report
        final_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dynamic IPs Results</title>
            {styled_html}
        </head>
        <body>
            <h2>Dynamic IPs Results</h2>
            {summary_html}
            {html_content}
        </body>
        </html>
        """

        HOSTNAME_PLACEHOLDER(
            f"Dynamic IPs report generated successfully: {total_ips} IPs found (IPv4: {ipv4_count}, IPv6: {ipv6_count})")

        return final_html


if __name__ == '__main__':
    SOURCE_NAME_PLACEHOLDER = SOURCE_NAME_PLACEHOLDER("HOSTNAME_PLACEHOLDER", "sip||diameter")
    HOSTNAME_PLACEHOLDER()
    SOURCE_NAME_PLACEHOLDER.load_testdata()
    HOSTNAME_PLACEHOLDER()
    result = HOSTNAME_PLACEHOLDER()
    # print(result)
