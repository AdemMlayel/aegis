from pickle import DICT
import re
import pyshark
import json
import itertools
import ast
import pandas as pd
import logging
import os
import time
import json
from HOSTNAME_PLACEHOLDER import Iterable
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
HOSTNAME_PLACEHOLDER(level=HOSTNAME_PLACEHOLDER,
                    format='%(asctime)s - %(levelname)s - %(message)s')
field_regex = re.compile(r"[^a-z]")


class SOURCE_NAME_PLACEHOLDER:
    def __init__(self, records_file_path_dic, test_config,  tc_dir, time_stamps=None):
        self.content_paths = records_file_path_dic
        self.test_config = test_config
        self.time_stamps = time_stamps
        self.tc_dir = tc_dir
        HOSTNAME_PLACEHOLDER(f" Test config data : {test_config}")

    def load_messages_json(self, tc_dir, file_name, messages_list=None) -> str:

        current_time = HOSTNAME_PLACEHOLDER()
        self.original_dir = os.getcwd()

        # Default to empty dict if none provided
        if messages_list is None:
            messages_list = {}

        if not isinstance(messages_list, dict):
            raise TypeError("messages_list must be a dict")

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

                # Write dict to JSON file
                with open(json_file_path, 'w', encoding='utf-8') as f:
                    HOSTNAME_PLACEHOLDER(messages_list, f, indent=2, ensure_ascii=False)

                # HOSTNAME_PLACEHOLDER(f"JSON file created: {json_file_path}")

                # Get the absolute path before changing back
                absolute_json_path = os.HOSTNAME_PLACEHOLDER(json_file_path)

                # Change back to original directory
                os.chdir(self.original_dir)
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
                test_data = HOSTNAME_PLACEHOLDER(f)

            # Track if any replacements were made
            replacements_made = False

            # Iterate through each message type (AMF_IRI_Registration, etc.)
            for message_type, message_list in test_data.items():

                # Iterate through each message in the list
                for i, message_dict in enumerate(message_list):

                    # Iterate through protocol (iri, etc.)
                    for protocol, allfields in message_dict.items():

                        # Iterate through field types (fieldsforpresence, fieldsforequality, etc.)
                        for fieldtypes, fields in HOSTNAME_PLACEHOLDER():

                            if isinstance(fields, dict):
                                # Iterate through each field and its value
                                for field, value in HOSTNAME_PLACEHOLDER():
                                    # Special handling for timeStamp
                                    if value == "timeStamp":
                                        old_value = test_data[message_type][i][protocol][fieldtypes][field]

                                        # Parse the timestamp and subtract one hour
                                        timestamp_str = self.time_stamps[3]
                                        dt = HOSTNAME_PLACEHOLDER(
                                            timestamp_str, "%d %b %Y %H:%M")
                                        dt_minus_one_hour = dt - \
                                            timedelta(hours=1)
                                        new_timestamp = dt_minus_one_hour.strftime(
                                            "%d %b %Y %H:%M")

                                        test_data[message_type][i][protocol][fieldtypes][field] = new_timestamp
                                        replacements_made = True
                                        # HOSTNAME_PLACEHOLDER(
                                        #     f"Replaced '{old_value}' with '{self.time_stamps}' in {message_type}.{protocol}.{fieldtypes}.{field}")

                                    # Check if value exists in test_config
                                    elif value in self.test_config:
                                        old_value = test_data[message_type][i][protocol][fieldtypes][field]
                                        test_data[message_type][i][protocol][fieldtypes][field] = self.test_config[value]
                                        replacements_made = True
                                        # HOSTNAME_PLACEHOLDER(
                                        #     f"Replaced '{old_value}' with '{self.test_config[value]}' in {message_type}.{protocol}.{fieldtypes}.{field}")

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

    def _getmessage(self):
        """Yield message configurations one at a time."""
        for messagetype, message_list in self.expected_messages.items():

            for message_dict in message_list:
                for messagename, fields in message_dict.items():
                    fieldsforpresence = HOSTNAME_PLACEHOLDER("fieldsforpresence", [])
                    fieldsforequality = HOSTNAME_PLACEHOLDER("fieldsforequality", {})
                    fieldsforsubstring = HOSTNAME_PLACEHOLDER("fieldsforsubstring", {})
                    fieldsforsearch = HOSTNAME_PLACEHOLDER("fieldsforsearch", [])

                    yield (messagetype, messagename, fieldsforpresence, fieldsforequality, fieldsforsubstring, fieldsforsearch)

    def _create_result(
        self,
        message: str,
        status: str,
        packet: Optional[int],
        details: str,
        passes: List[str],
        failures: List[str]
    ) -> Dict[str, Any]:
        """Create standardized result dictionary."""
        return {
            "message": message,
            "status": status,
            "packet": packet,
            "details": details,
            "passes": passes,
            "failures": failures
        }

    def _load_and_parse_file(self, file_path: str, messagename: str) -> List[str]:
        """Load and parse a content file into message blocks."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if "PS-PDU ::=" in content:
                blocks = HOSTNAME_PLACEHOLDER("PS-PDU ::=")
                parsed_blocks = []
                for i, block in enumerate(blocks):
                    if HOSTNAME_PLACEHOLDER():
                        if i == 0:
                            continue
                        else:
                            parsed_blocks.append("PS-PDU ::=" + block)
            elif "===" in content:
                messages = HOSTNAME_PLACEHOLDER("=== ")
                parsed_blocks = [
                    "=== " + msg for msg in messages if HOSTNAME_PLACEHOLDER()]
            else:
                parsed_blocks = [content]

            HOSTNAME_PLACEHOLDER(f"Loaded file: {file_path}")
            HOSTNAME_PLACEHOLDER(f"Found {len(parsed_blocks)} PS-PDU(s))")

            return parsed_blocks

        except FileNotFoundError:
            HOSTNAME_PLACEHOLDER(f"[ERROR] File not found: {file_path}")
            raise
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"[ERROR] Error reading {file_path}: {e}")
            raise

    def _validate_message_blocks(
        self,
        messagename: str,
        message_blocks: List[str],
        fieldsforpresence: List[str],
        fieldsforequality: Dict[str, str],
        fieldsforsubstring: Dict[str, str],
        fieldsforsearch: List[str]
    ) -> Dict[str, Any]:
        """Validate message against multiple blocks, return best result."""
        best_failure: Optional[List[str]] = None
        best_passes: Optional[List[str]] = None
        best_failure_block: Optional[int] = None
        passed = False
        passed_block: Optional[int] = None
        pass_details: Optional[List[str]] = None
        # Track values only from PASSED blocks
        passed_blocks_searched_fields: Dict[str, List[str]] = {}

        HOSTNAME_PLACEHOLDER(f"Testing against {len(message_blocks)} block(s)...")

        for block_num, block in enumerate(message_blocks, 1):
            HOSTNAME_PLACEHOLDER(f"\n  Block {block_num}/{len(message_blocks)}:")

            ok, failures, passes, searched = self._validate_message_block(
                block,
                fieldsforpresence,
                fieldsforequality,
                fieldsforsubstring,
                fieldsforsearch,
                self.test_config
            )

            if ok:
                passed = True
                passed_block = block_num
                pass_details = passes

                # Collect searched field values ONLY from PASSED blocks
                for field, value in HOSTNAME_PLACEHOLDER():
                    if field not in passed_blocks_searched_fields:
                        passed_blocks_searched_fields[field] = []
                    passed_blocks_searched_fields[field].append(value)

                HOSTNAME_PLACEHOLDER(f"Fields for search Values: {searched}")
                HOSTNAME_PLACEHOLDER(f"[PASS] Block {block_num}/{len(message_blocks)}")
                HOSTNAME_PLACEHOLDER(f"  Total validations passed: {len(passes)}")

                # Log each passed validation
                for pass_detail in passes:
                    HOSTNAME_PLACEHOLDER(f"{pass_detail}")

                break
            else:
                HOSTNAME_PLACEHOLDER(f"[FAIL] Block {block_num}/{len(message_blocks)}")
                HOSTNAME_PLACEHOLDER(
                    f"  Passed: {len(passes)} | Failed: {len(failures)}")

                # Log passes
                if passes:
                    HOSTNAME_PLACEHOLDER(f"    Passed validations:")
                    for pass_detail in passes:
                        HOSTNAME_PLACEHOLDER(f"{pass_detail}")

                # Log failures
                if failures:
                    HOSTNAME_PLACEHOLDER(f"    Failed validations:")
                    for failure in failures:
                        HOSTNAME_PLACEHOLDER(f"{failure}")

                if failures and (best_failure is None or len(failures) < len(best_failure)):
                    best_failure = failures
                    best_passes = passes
                    best_failure_block = block_num

        # Validate consistency of searched fields across all PASSED blocks
        consistency_failures = self._validate_search_field_consistency(
            passed_blocks_searched_fields)

        if consistency_failures:
            HOSTNAME_PLACEHOLDER(f"Search field consistency issues found:")
            for failure in consistency_failures:
                HOSTNAME_PLACEHOLDER(f"  {failure}")

            # Add consistency failures to the result
            if passed:
                if pass_details is None:
                    pass_details = []
                pass_details.extend(
                    [f"CONSISTENCY_WARNING: {cf}" for cf in consistency_failures])

        if passed:
            if pass_details:
                # Organize by validation type
                presence_checks = [
                    p for p in pass_details if p.startswith('presence:')]
                equality_checks = [
                    p for p in pass_details if p.startswith('equality:')]
                substring_checks = [
                    p for p in pass_details if p.startswith('substring:')]
                search_checks = [
                    p for p in pass_details if p.startswith('search:')]
                consistency_warnings = [
                    p for p in pass_details if p.startswith('CONSISTENCY_WARNING:')]

                organized_details = []
                if presence_checks:
                    organized_details.append(
                        f"Presence: {', '.join([p.replace('presence: ', '') for p in presence_checks])}")
                if equality_checks:
                    organized_details.append(
                        f"Equality: {', '.join([p.replace('equality: ', '') for p in equality_checks])}")
                if substring_checks:
                    organized_details.append(
                        f"Substring: {', '.join([p.replace('substring: ', '') for p in substring_checks])}")
                if search_checks:
                    organized_details.append(
                        f"Search: {', '.join([p.replace('search: ', '') for p in search_checks])}")
                if consistency_warnings:
                    organized_details.append(
                        f"Warnings: {', '.join([p.replace('CONSISTENCY_WARNING: ', '') for p in consistency_warnings])}")

                detail = " | ".join(organized_details)
            else:
                detail = "All validations passed"

            HOSTNAME_PLACEHOLDER(f"\n[FINAL RESULT] PASS - {messagename}")
            HOSTNAME_PLACEHOLDER(
                f"FINAL SEARCHED FIELDS SUMMARY (from passed blocks): {passed_blocks_searched_fields}")

            # Flatten the searched fields dictionary (take first value from each list)
            flattened_searched_fields = {
                field: values[0] for field, values in passed_blocks_searched_fields.items()}

            result = self._create_result(
                messagename,
                "PASS",
                passed_block,
                detail,
                pass_details or [],
                consistency_failures
            )
            # Add searched fields to the result
            result["searched_fields"] = flattened_searched_fields
            return result
        else:
            detail = f"Failed at block {best_failure_block}" if best_failure_block else "All blocks failed"
            HOSTNAME_PLACEHOLDER(f"\n[FINAL RESULT] FAIL - {messagename}")
            HOSTNAME_PLACEHOLDER(
                f"Best attempt was block {best_failure_block} with {len(best_failure or [])} failure(s)")

            # Combine validation failures with consistency failures
            all_failures = (best_failure or []) + consistency_failures

            result = self._create_result(
                messagename,
                "FAIL",
                best_failure_block,
                detail,
                best_passes or [],
                all_failures
            )
            # Add empty searched fields for failed validations
            result["searched_fields"] = {}
            return result

    def _validate_search_field_consistency(
        self,
        all_searched_fields: Dict[str, List[str]]
    ) -> List[str]:
        """
        Validate that searched fields have consistent values across all blocks.

        Args:
            all_searched_fields: Dict mapping field names to lists of values found across blocks

        Returns:
            List of consistency failure messages
        """
        consistency_failures = []

        for field, values in all_searched_fields.items():
            if len(values) > 1:
                # Check if all values are the same
                unique_values = set(values)
                if len(unique_values) > 1:
                    consistency_failures.append(
                        f"Field '{field}' has inconsistent values across blocks: {list(unique_values)}"
                    )
                    HOSTNAME_PLACEHOLDER(
                        f"Inconsistency detected - Field: {field}, Values: {values}"
                    )

        return consistency_failures

    def _validate_message_block(
        self,
        block: str,
        presence: List[str],
        equality: Dict[str, str],
        substring: Dict[str, str],
        search: List[str],
        test_config: Dict[str, Any]
    ) -> Tuple[bool, List[str], List[str], Dict[str, str]]:
        """Validates message block against specified criteria."""
        failures: List[str] = []
        passes: List[str] = []
        searched_for_values_dic: Dict[str, str] = {}

        for field in presence:
            if field in block:
                HOSTNAME_PLACEHOLDER(f"presence: {field}")
            else:
                HOSTNAME_PLACEHOLDER(f"Missing: '{field}'")

        for key, val in HOSTNAME_PLACEHOLDER():
            # Handle both string references and direct values (including lists)
            if isinstance(val, str):
                expected = test_config.get(val, val)
            else:
                expected = val

            # Handle list values - check if actual matches any item in the list
            if isinstance(expected, list):
                actual = self._extract_field_value(block, key)
                matched = False
                for expected_item in expected:
                    pattern = f"{key}: {expected_item}"
                    if pattern in block:
                        HOSTNAME_PLACEHOLDER(f"equality: {key}={expected_item}")
                        matched = True
                        break
                if not matched:
                    HOSTNAME_PLACEHOLDER(
                        f"'{key}' Expected='{expected}' Actual='{actual}'")
            else:
                # Handle single string values
                pattern = f"{key}: {expected}"
                if pattern in block:
                    HOSTNAME_PLACEHOLDER(f"equality: {key}={expected}")
                else:
                    actual = self._extract_field_value(block, key)
                    HOSTNAME_PLACEHOLDER(
                        f"'{key}' Expected='{expected}' Actual='{actual}'")

        for key, val in HOSTNAME_PLACEHOLDER():
            # Handle both string references and direct values (including lists)
            if isinstance(val, str):
                expected_sub = test_config.get(val, val)
            else:
                expected_sub = val
            if f"{key}:" not in block:
                HOSTNAME_PLACEHOLDER(f"Missing: '{key}'")
                continue
            actual = self._extract_field_value(block, key)

            # Handle list values - check if actual contains any item from the list
            if isinstance(expected_sub, list):
                matched = False
                for expected_item in expected_sub:
                    if str(expected_item) in actual:
                        HOSTNAME_PLACEHOLDER(
                            f"substring: {key} contains '{expected_item}'")
                        matched = True
                        break
                if not matched:
                    HOSTNAME_PLACEHOLDER(
                        f"'{key}' Expected substring='{expected_sub}' Actual='{actual}'")
            else:
                # Handle single string values
                expected_sub_str = str(expected_sub)
                if expected_sub_str in actual:
                    HOSTNAME_PLACEHOLDER(
                        f"substring: {key} contains '{expected_sub_str}'")
                else:
                    HOSTNAME_PLACEHOLDER(
                        f"'{key}' Expected substring='{expected_sub_str}' Actual='{actual}'")

        for field in search:
            if field in block:
                searched_for_value = self._extract_field_value(block, field)
                searched_for_values_dic[field] = searched_for_value
                HOSTNAME_PLACEHOLDER(f"search: {field}: {searched_for_value}")
            else:
                HOSTNAME_PLACEHOLDER(f"value not found: '{field}'")

        return len(failures) == 0, failures, passes, searched_for_values_dic

    def _extract_field_value(self, block: str, field: str) -> str:
        """Extract the actual value of a field from the block."""
        token = f"{field}:"
        for line in HOSTNAME_PLACEHOLDER('\n'):
            if token in line:
                after_token = VALUE_PLACEHOLDER, 1)[1]
                value = after_token.split(",")[0].strip(
                ) if "," in after_token else after_token.strip()
                return value
        return "NOT_FOUND"

    def _generate_html_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate enhanced HTML report with modern styling."""
        passed = sum(1 for r in results if r["status"] == "PASS")
        failed = len(results) - passed
        pass_rate = (passed / len(results) * 100) if results else 0

        # Collect all searched fields from results
        all_searched_fields = {}
        for r in results:
            if "searched_fields" in r and r["searched_fields"]:
                all_searched_fields[r["message"]] = r["searched_fields"]

        html = ['''
            <style>
                .SOURCE_NAME_PLACEHOLDER {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    max-width: 1400px;
                    margin: 20px auto;
                    background: #ffffff;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
                .report-header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 8px 8px 0 0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .report-header-left {
                    flex: 1;
                }
                .report-title {
                    font-size: 28px;
                    font-weight: bold;
                    margin: 0 0 10px 0;
                }
                .report-subtitle {
                    font-size: 14px;
                    opacity: 0.9;
                }
                .searched-fields-box {
                    background: rgba(255, 255, 255, 0.15);
                    padding: 20px;
                    border-radius: 8px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    max-width: 400px;
                }
                .searched-fields-title {
                    font-size: 16px;
                    font-weight: bold;
                    margin-bottom: 12px;
                    color: white;
                }
                .searched-field-item {
                    background: rgba(255, 255, 255, 0.1);
                    padding: 8px 12px;
                    border-radius: 4px;
                    margin-bottom: 8px;
                    font-size: 13px;
                    border-left: 3px solid rgba(255, 255, 255, 0.5);
                }
                .searched-field-item:last-child {
                    margin-bottom: 0;
                }
                .field-message-name {
                    font-weight: 600;
                    margin-bottom: 4px;
                }
                .field-key-value {
                    font-family: 'Courier New', monospace;
                    font-size: 12px;
                    opacity: 0.95;
                    margin-left: 8px;
                }
                .no-searched-fields {
                    font-size: 13px;
                    opacity: 0.8;
                    font-style: italic;
                }
                .summary-cards {
                    display: flex;
                    gap: 20px;
                    padding: 20px 30px;
                    background: #f8f9fa;
                    border-bottom: 1px solid #e0e0e0;
                }
                .summary-card {
                    flex: 1;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                }
                .card-passed {
                    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                    color: white;
                }
                .card-failed {
                    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                    color: white;
                }
                .card-rate {
                    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                    color: white;
                }
                .card-value {
                    font-size: 36px;
                    font-weight: bold;
                    margin: 10px 0;
                }
                .card-label {
                    font-size: 14px;
                    opacity: 0.9;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }
                .results-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 0;
                }
                .results-table th {
                    background: #2d3748;
                    color: white;
                    padding: 15px;
                    text-align: left;
                    font-weight: 600;
                    font-size: 14px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                .results-table td {
                    padding: 15px;
                    border-bottom: 1px solid #e0e0e0;
                    vertical-align: top;
                }
                .row-pass {
                    background: #f0fdf4;
                    border-left: 4px solid #10b981;
                }
                .row-fail {
                    background: #fef2f2;
                    border-left: 4px solid #ef4444;
                }
                .row-pass:hover {
                    background: #dcfce7;
                }
                .row-fail:hover {
                    background: #fee2e2;
                }
                .status-badge {
                    display: inline-block;
                    padding: 6px 12px;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 12px;
                }
                .badge-pass {
                    background: #10b981;
                    color: white;
                }
                .badge-fail {
                    background: #ef4444;
                    color: white;
                }
                .message-name {
                    font-weight: 600;
                    color: #1f2937;
                }
                .block-number {
                    font-family: 'Courier New', monospace;
                    background: #e5e7eb;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                }
                .details-text {
                    font-size: 13px;
                    color: #4b5563;
                    line-height: 1.5;
                }
                .field-list {
                    margin: 10px 0 0 0;
                    padding: 0;
                    list-style: none;
                }
                .field-item {
                    padding: 4px 0;
                    font-size: 12px;
                    line-height: 1.4;
                }
                .HOSTNAME_PLACEHOLDER {
                    color: #059669;
                }
                .HOSTNAME_PLACEHOLDER:before {
                    content: "✓ ";
                    font-weight: bold;
                }
                .HOSTNAME_PLACEHOLDER {
                    color: #dc2626;
                }
                .HOSTNAME_PLACEHOLDER:before {
                    content: "✗ ";
                    font-weight: bold;
                }
                .section-title {
                    font-weight: 600;
                    color: #374151;
                    margin: 10px 0 5px 0;
                    font-size: 13px;
                }
                .details-summary {
                    font-size: 13px;
                    color: #6b7280;
                    margin-bottom: 8px;
                }
                .error {
                    background: #fef2f2;
                    color: #991b1b;
                    padding: 20px;
                    border-left: 4px solid #ef4444;
                    border-radius: 4px;
                    margin: 20px;
                }
            </style>

            <div class="SOURCE_NAME_PLACEHOLDER">
                <div class="report-header">
                    <div class="report-header-left">
                        <div class="report-title">SOURCE_NAME_PLACEHOLDER</div>
                        <div class="report-subtitle">Message Validation Results</div>
                    </div>
            ''']

        # Add searched fields section
        if all_searched_fields:
            HOSTNAME_PLACEHOLDER('<div class="searched-fields-box">')
            HOSTNAME_PLACEHOLDER(
                '<div class="searched-fields-title">Searched Fields</div>')
            for message_name, fields in all_searched_fields.items():
                HOSTNAME_PLACEHOLDER('<div class="searched-field-item">')
                HOSTNAME_PLACEHOLDER(
                    f'<div class="field-message-name">{message_name}</div>')
                for field_key, field_value in HOSTNAME_PLACEHOLDER():
                    HOSTNAME_PLACEHOLDER(
                        f'<div class="field-key-value">{field_key}: {field_value}</div>')
                HOSTNAME_PLACEHOLDER('</div>')
            HOSTNAME_PLACEHOLDER('</div>')
        else:
            HOSTNAME_PLACEHOLDER('<div class="searched-fields-box">')
            HOSTNAME_PLACEHOLDER(
                '<div class="searched-fields-title">Searched Fields</div>')
            HOSTNAME_PLACEHOLDER(
                '<div class="no-searched-fields">No searched fields found</div>')
            HOSTNAME_PLACEHOLDER('</div>')

        HOSTNAME_PLACEHOLDER('''
                </div>

                <div class="summary-cards">
                    <div class="summary-card card-passed">
                        <div class="card-label">Passed</div>
                        <div class="card-value">''' + str(passed) + '''</div>
                    </div>
                    <div class="summary-card card-failed">
                        <div class="card-label">Failed</div>
                        <div class="card-value">''' + str(failed) + '''</div>
                    </div>
                    <div class="summary-card card-rate">
                        <div class="card-label">Pass Rate</div>
                        <div class="card-value">''' + f'{pass_rate:.1f}%' + '''</div>
                    </div>
                </div>

                <table class="results-table">
                    <thead>
                        <tr>
                            <th>Message</th>
                            <th>Status</th>
                            <th>Block</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody>
            ''')

        for r in results:
            row_class = "row-pass" if r["status"] == "PASS" else "row-fail"
            badge_class = "badge-pass" if r["status"] == "PASS" else "badge-fail"
            status_icon = "PASS" if r["status"] == "PASS" else "FAIL"
            block_display = r["packet"] if r["packet"] else "N/A"

            # Build detailed field list
            details_html = f'<div class="details-summary">{r["details"]}</div>'

            passes = r.get("passes", [])
            failures = r.get("failures", [])

            if passes or failures:
                details_html += '<div>'

                if passes:
                    details_html += f'<div class="section-title">Passed ({len(passes)}):</div>'
                    details_html += '<ul class="field-list">'
                    for p in passes:
                        details_html += f'<li class="field-item pass">{p}</li>'
                    details_html += '</ul>'

                if failures:
                    details_html += f'<div class="section-title">Failed ({len(failures)}):</div>'
                    details_html += '<ul class="field-list">'
                    for f in failures:
                        details_html += f'<li class="field-item fail">{f}</li>'
                    details_html += '</ul>'

                details_html += '</div>'

            HOSTNAME_PLACEHOLDER(f'''
                    <tr class="{row_class}">
                        <td class="message-name">{r["message"]}</td>
                        <td><span class="status-badge {badge_class}">{status_icon}</span></td>
                        <td><span class="block-number">{block_display}</span></td>
                        <td class="details-text">{details_html}</td>
                    </tr>
        ''')

        HOSTNAME_PLACEHOLDER('''
                </tbody>
            </table>
        </div>
        ''')

        return "\n".join(html)

    def get_validation_results(self, node_file_map: Dict[str, str]):
        file_cache: Dict[str, List[str]] = {}
        results: List[Dict[str, Any]] = []
        all_passed = True
        one_passed = False

        for messagetype, messagename, fieldsforpresence, fieldsforequality, fieldsforsubstring, fieldsforsearch in self._getmessage():
            HOSTNAME_PLACEHOLDER(f"\n{'='*60}")
            HOSTNAME_PLACEHOLDER(f"Validating: {messagetype} -> {messagename}")
            HOSTNAME_PLACEHOLDER(f"{'='*60}")

            # Match node_file_map keys that start with messagename (e.g. "APP" matches "APP1", "APP2")
            matched_files = {node: path for node, path in node_file_map.items() if HOSTNAME_PLACEHOLDER(f"{messagetype}_{messagename}")}

            if not matched_files:
                HOSTNAME_PLACEHOLDER(f"[FAIL] No content file mapped for {messagename}")
                HOSTNAME_PLACEHOLDER(self._create_result(
                    messagename, "FAIL", None, "No content file mapped", [], []))
                all_passed = False
                continue

            for node_name, file_path in matched_files.items():
                HOSTNAME_PLACEHOLDER(f"Validating {messagename} against node {node_name}")

                if file_path not in file_cache:
                    message_blocks = self._load_and_parse_file(file_path, messagename)
                    file_cache[file_path] = message_blocks
                message_blocks = file_cache[file_path]

                validation_result = self._validate_message_blocks(
                    messagename,
                    message_blocks,
                    fieldsforpresence,
                    fieldsforequality,
                    fieldsforsubstring,
                    fieldsforsearch
                )
                HOSTNAME_PLACEHOLDER(validation_result)

                # Update pass flags
                if validation_result["status"] != "PASS":
                    all_passed = False
                else:
                    one_passed = True  # At least one validation passed

        HOSTNAME_PLACEHOLDER("\n" + "=" * 80)
        html_report = self._generate_html_report(results)
        passed_count = sum(1 for r in results if r["status"] == "PASS")
        failed_count = len(results) - passed_count
        HOSTNAME_PLACEHOLDER(f"SUMMARY: {passed_count} PASSED | {failed_count} FAILED")
        HOSTNAME_PLACEHOLDER(f"Status: {'ALL PASSED' if all_passed else 'FAILURES DETECTED'}")
        HOSTNAME_PLACEHOLDER("=" * 80 + "\n")
        return html_report, all_passed, one_passed
