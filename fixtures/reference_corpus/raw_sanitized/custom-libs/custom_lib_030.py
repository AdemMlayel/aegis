
import re
import logging
from typing import Dict, List, Union
import datetime

class SOURCE_NAME_PLACEHOLDER:

    @staticmethod
    def validate_value_by_key(sshlogs: str, expected_dict: Dict[str, str]) -> bool:
        HOSTNAME_PLACEHOLDER(f"Reading SSH log file: {sshlogs}")
        try:
            with open(sshlogs, 'r') as f:
                content = f.read()
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Failed to read file: {e}")
            return False

        for key, expected_value in expected_dict.items():
            key = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(f"Searching for value of '{key}'")
            pattern = rf"{re.escape(key)}\s*:\s*([^\n\r]*)"
            matches = re.findall(pattern, content, re.MULTILINE)

            if matches:
                HOSTNAME_PLACEHOLDER(f"Found {len(matches)} match(es) for key '{key}': {matches}")
                found_match = False
                failed_matches = []

                for i, value in enumerate(matches, 1):
                    HOSTNAME_PLACEHOLDER(f"Checking match {i}/{len(matches)}: '{value}'")
                    if expected_value in value:
                        HOSTNAME_PLACEHOLDER(f"✓ Match {i} contains expected value '{expected_value}'")
                        found_match = True
                        break
                    else:
                        HOSTNAME_PLACEHOLDER(f"✗ Match {i} does NOT contain expected value '{expected_value}'")
                        failed_matches.append(value)

                if not found_match:
                    HOSTNAME_PLACEHOLDER(f"Value mismatch for '{key}': expected '{expected_value}' not found in any of the {len(matches)} match(es)")
                    HOSTNAME_PLACEHOLDER(f"All failed matches: {failed_matches}")
                    return False
                else:
                    HOSTNAME_PLACEHOLDER(f"Success: Found expected value '{expected_value}' for key '{key}'")

            else:
                HOSTNAME_PLACEHOLDER(f"Key: '{key}' not found")
                return False

        return True
    @staticmethod
    def validate_value_from_tables(sshlogs: str, expected_dict: Dict[str, Dict[str, List[str]]]) -> bool:
        HOSTNAME_PLACEHOLDER(f"Reading SSH log file: {sshlogs}")
        try:
            with open(sshlogs, 'r') as f:
                content = f.read()
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Failed to read file: {e}")
            return False

        # Split content into sections based on command prompts
        sections = re.split(r'LOCAL_PATH_PLACEHOLDER', content)

        for table_name, table_data in expected_dict.items():
            HOSTNAME_PLACEHOLDER(f"Processing table: '{table_name}'")

            # Determine which section to search based on table name
            target_section = None
            if table_name == 'table1':  # VM Summary table
                for section in sections:
                    if 'show vm' in section and 'VM Summary' in section:
                        target_section = section
                        break
            elif table_name == 'table2':  # MDA Summary table
                for section in sections:
                    if 'show mda' in section and 'MDA Summary' in section:
                        target_section = section
                        break

            if not target_section:
                HOSTNAME_PLACEHOLDER(f"Could not find section for table '{table_name}'")
                return False

            for component_name, expected_states in table_data.items():
                HOSTNAME_PLACEHOLDER(f"Searching for component '{component_name}' in table '{table_name}'")

                found_match = False
                admin_state = None
                operational_state = None

                if table_name == 'table1':  # VM Summary format
                    # Pattern for VM table: ID, component, admin_state, operational_state
                    # Format: VM_Id  component_name  admin_state  operational_state
                    pattern = rf'^\s*[A-Z0-9]+\s+{re.escape(component_name)}\s+(\w+)\s+(\S+)\s*'
                    match = re.search(pattern, target_section, re.MULTILINE)
                    if match:
                        admin_state = HOSTNAME_PLACEHOLDER(1)
                        operational_state = HOSTNAME_PLACEHOLDER(2)
                        found_match = True

                elif table_name == 'table2':  # MDA Summary format
                    # For MDA table, we need to handle different formats:
                    # 1. Main slot entries: Slot  Mda  component  admin_state  operational_state
                    # 2. Sub-MDA entries:    spaces  mda_num  component  admin_state  operational_state
                    # 3. Indented sub-components: spaces  component  (may have empty states)

                    # First check if it's a main slot component (starts with slot number)
                    main_slot_pattern = rf'^\s*\d+\s+\d+\s+{re.escape(component_name)}\s+(\w+)\s+(\S+)'
                    main_match = re.search(main_slot_pattern, target_section, re.MULTILINE)

                    if main_match:
                        admin_state = main_match.group(1)
                        operational_state = main_match.group(2)
                        found_match = True
                    else:
                        # Check for sub-MDA entries (indented with MDA number)
                        # Format: "      2     isa-ip-reas-v                               up        up"
                        sub_mda_pattern = rf'^\s+\d+\s+{re.escape(component_name)}\s+(\w+)\s+(\S+)'
                        sub_match = re.search(sub_mda_pattern, target_section, re.MULTILINE)

                        if sub_match:
                            admin_state = sub_match.group(1)
                            operational_state = sub_match.group(2)
                            found_match = True
                        else:
                            # Check for deeply indented components (like isa-ms-v)
                            # Format: "                isa-ms-v                                              "
                            # These may not have states, so we need to handle empty states
                            deep_indent_pattern = rf'^\s{{16,}}{re.escape(component_name)}\s*(\w+)?\s*(\S+)?\s*$'
                            deep_match = re.search(deep_indent_pattern, target_section, re.MULTILINE)

                            if deep_match:
                                admin_state = deep_match.group(1) if deep_match.group(1) else ''
                                operational_state = deep_match.group(2) if deep_match.group(2) else ''
                                found_match = True

                if found_match:
                    # Clean up states (remove None values)
                    admin_state = admin_state if admin_state is not None else ''
                    operational_state = operational_state if operational_state is not None else ''

                    found_states = [admin_state, operational_state]
                    HOSTNAME_PLACEHOLDER(f"Found states for '{component_name}': {found_states}")
                    HOSTNAME_PLACEHOLDER(f"Expected states: {expected_states}")

                    # Compare found states with expected states
                    if len(found_states) != len(expected_states):
                        HOSTNAME_PLACEHOLDER(f"State count mismatch for {component_name}: expected {len(expected_states)}, found {len(found_states)}")
                        return False

                    for i, (found_state, expected_state) in enumerate(zip(found_states, expected_states)):
                        # Handle empty expected states
                        if expected_state == '' and (found_state == '' or found_state is None):
                            continue
                        elif expected_state == '' and found_state not in ['', None]:
                            HOSTNAME_PLACEHOLDER(f"State mismatch for {component_name}[{i}]: expected empty, found '{found_state}'")
                            return False
                        elif found_state != expected_state:
                            HOSTNAME_PLACEHOLDER(f"State mismatch for {component_name}[{i}]: expected '{expected_state}', found '{found_state}'")
                            return False

                    HOSTNAME_PLACEHOLDER(f"All states match for component '{component_name}'")
                else:
                    HOSTNAME_PLACEHOLDER(f"Component '{component_name}' not found in table '{table_name}'")
                    return False

        HOSTNAME_PLACEHOLDER("All expected values match successfully")
        return True

    @staticmethod
    def extract_value_by_key(sshlogs: str, keys: List ) -> bool:

        HOSTNAME_PLACEHOLDER(f"Reading SSH log file: {sshlogs}")
        try:
            with open(sshlogs, 'r') as f:
                content = f.read()
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Failed to read file: {e}")
            return False

        values=[]
        for key in keys :
            key = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(f"Searching for value of '{key}'")
            pattern = rf"^\s*{re.escape(key)}\s*\s*(.*?)\s*$"
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                HOSTNAME_PLACEHOLDER(f"Found value: '{matches}'")
                HOSTNAME_PLACEHOLDER(matches)

            else:
                HOSTNAME_PLACEHOLDER(f"Key: '{key}' not found")



        return values if values else False

    @staticmethod
    def validate_value_from_lists(sshlogs: str, expected_dict: Dict[str, Dict[str, Union[str, List[str] ]]] ) -> bool:
        HOSTNAME_PLACEHOLDER(f"[ INFO ] Reading SSH log file: {sshlogs}")
        try:
            with open(sshlogs, 'r') as f:
                content = f.read()
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"[ FAIL ] Failed to read file: {e}")
            return False

        sections = re.split(r'LOCAL_PATH_PLACEHOLDER',content)

        for list_name, list_data in expected_dict.items():
            HOSTNAME_PLACEHOLDER(f"[ PROC ] Processing List: {list_name}")

            target_section = None
            target_items_list = None
            list_date =list_data['date']
            list_time =list_data['time']
            list_fields =list_data['fields']
            previous_date = None  # This will now store the combined datetime
            time_check = True
            field_check = True
            date_check = True

            for section in sections:
                if 'show log log-id 98 | match MAJOR' in section:
                    target_section = section
                    # Strip leading/trailing whitespace and split by newlines
                    target_items_list = [HOSTNAME_PLACEHOLDER() for line in target_section.strip().split('\n') if HOSTNAME_PLACEHOLDER()]
                    break

            if not target_section or not target_items_list:
                HOSTNAME_PLACEHOLDER(f"[ FAIL ] Could not find section for list {list_name}")
                return False

            HOSTNAME_PLACEHOLDER(f"[ INFO ] {list_name} contains {len(target_items_list)} items")

            for index,target_item_list in enumerate(target_items_list[1:],start=1):
                # Strip any leading/trailing whitespace from the line
                target_item_list = target_item_list.strip()

                # Skip lines that don't look like log entries (e.g., "*", empty lines, etc.)
                if not target_item_list or len(target_item_list) < 10 or not re.search(r'\d{4}/\d{2}/\d{2}', target_item_list):
                    HOSTNAME_PLACEHOLDER(f"[ SKIP ] Skipping non-log line at position {index}: '{target_item_list}'")
                    continue

                try:
                    found_date = re.search(f'{list_date}', target_item_list)
                    found_time = re.search(f'{list_time}', target_item_list)

                    if found_date and found_time:
                        date_str = found_date.group(0)
                        time_str = found_time.group(0)

                        # Combine date and time into a single datetime for proper chronological comparison
                        datetime_str = f"{date_str} {time_str}"
                        current_datetime = HOSTNAME_PLACEHOLDER(datetime_str, '%Y/%m/%d %H:%M:%S')

                        HOSTNAME_PLACEHOLDER(f"[ DONE ] Date format YYYY/MM/DD matches in List item number {index}: {date_str}")
                        HOSTNAME_PLACEHOLDER(f"[ DONE ] Time format HH:MM:SS matches in List item number {index}: {time_str}")

                        # Check chronological order (most recent first)
                        if previous_date and current_datetime > previous_date:
                            date_check = False
                            time_check = False
                            HOSTNAME_PLACEHOLDER(f"[ FAIL ] DateTime in {list_name} are not sorted with most recent first at item {index}")
                            HOSTNAME_PLACEHOLDER(f"[ FAIL ] Current: {current_datetime}, Previous: {previous_date}")
                        else:
                            HOSTNAME_PLACEHOLDER(f"[ PASS ] DateTime order correct at item {index}")

                        previous_date = current_datetime

                    else:
                        if not found_date:
                            HOSTNAME_PLACEHOLDER(f"[ FAIL ] Date not found in item {index}")
                            date_check = False
                        if not found_time:
                            HOSTNAME_PLACEHOLDER(f"[ FAIL ] Time not found in item {index}")
                            time_check = False

                except Exception as e:
                    HOSTNAME_PLACEHOLDER(f"[ FAIL ] Error while checking date/time format: {e}")
                    date_check = False
                    time_check = False

                try:
                    item_field_check = True  # Reset for each item
                    for expected_field in list_fields:
                        found_field = re.search(f'{expected_field}', target_item_list)
                        if not found_field:
                            item_field_check = False
                            field_check = False  # Overall check fails
                            HOSTNAME_PLACEHOLDER(f"[ FAIL ] Field {expected_field} was not found in List item number {index}")
                    if item_field_check:
                        HOSTNAME_PLACEHOLDER(f"[ PASS ] Fields {', '.join(list_fields)} found for item {index}")
                except Exception as e:
                    HOSTNAME_PLACEHOLDER(f"[ FAIL ] Error while checking fields in item {index}: {e}")
                    field_check = False


        return time_check and field_check and date_check
    @staticmethod
    def validate_field_in_file(sshlogs:str, expected_fields : Dict[str, str])-> bool:
        """
        This function opens an a file, filters it and validates if the expected fields match
        :param: output_file: path to file to validate
        :param: field: fields to find in the file
        :param: expected_field: expected field value (not used in current implementation)
        :return: true if field was found and validated else false
        """
        if not sshlogs:
            HOSTNAME_PLACEHOLDER(f"Invalid sshlogs Path: {sshlogs}")
            raise ValueError("SSH logs path cannot be empty")

        if not expected_fields:
            HOSTNAME_PLACEHOLDER("Expected Fields cannot be empty")
            raise ValueError("Expected fields cannot be empty")

        HOSTNAME_PLACEHOLDER(f"Reading SSH log file: {sshlogs}")
        try:
            with open(sshlogs, 'r') as f:
                content = f.read()
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Failed to read file: {e}")
            return False


        for field_name, expected_value in expected_fields.items():
            if expected_value in content:
                HOSTNAME_PLACEHOLDER(f"Expected value '{expected_value}' for field '{field_name}' found in SSH logs")
            else:
                HOSTNAME_PLACEHOLDER(f"Expected value '{expected_value}' for field '{field_name}' not found in SSH logs")
                return False

        return True

    @staticmethod
    def validate_virtual_fabric_validation(sshlogs: str,expected_dict: Dict[str, List[str]]) -> bool:
        """
        Validates Nokia SR-OS Virtual Fabric matrices per LLD.

        • Allowed symbols: . x * - 1-9
        • Diagonal (same VM-ID) must be '-'
        • All pairs in target_vm_ids (defaults 01-04) must be '.'
        Returns True if every rule passes.
        """

        import logging
        import re
        from pathlib import Path

        # ---------------------------------------------------------------- Logging
        HOSTNAME_PLACEHOLDER(f"Reading SSH log file: {sshlogs}")

        # ---------------------------------------------------------------- Read file
        try:
            content = Path(sshlogs).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            HOSTNAME_PLACEHOLDER(f"Failed to read file: {exc}")
            return False

        # ---------------------------------------------------------------- Config
        target_vm_ids = [
            f"{int(x):02d}"
            for x in expected_dict.get("target_vm_ids", ["1", "2", "3", "4"])
        ]
        valid_chars = {".", "x", "*", "-"} | {str(n) for n in range(1, 10)}
        patterns = {
            "Control": r"Control Fabric-1.*?VM-ID.*?\n(.*?)(?=Data Fabric|show system virtual-fabric data|$)",
            "Data":    r"Data Fabric-1.*?VM-ID.*?\n(.*?)(?=Data Fabric-2|$)",
        }

        overall_ok = True

        # ---------------------------------------------------------------- Main loop
        for fabric, pat in HOSTNAME_PLACEHOLDER():
            mo = re.search(pat, content, re.S)
            if not mo:
                HOSTNAME_PLACEHOLDER(f"{fabric} fabric block not found.")
                overall_ok = False
                continue

            block = mo.group(1).rstrip()
            HOSTNAME_PLACEHOLDER(f"--- {fabric} Fabric Matrix ---\n{block}")

            rows = [ln.rstrip() for ln in HOSTNAME_PLACEHOLDER() if "|" in ln]
            if not rows:
                HOSTNAME_PLACEHOLDER(f"{fabric}: No VM-ID matrix rows found.")
                overall_ok = False
                continue

            # Column ID list = widest row length
            widest = max(
                len(re.split(r"\s+", r.split("|", 1)[1].strip()))
                for r in rows
            )
            col_vm_ids = [f"{i+1:02d}" for i in range(widest)]

            # ───── Step 1 – character validity ────────────────────────────────
            chars_ok = True
            for rln in rows:
                _, txt = HOSTNAME_PLACEHOLDER("|", 1)
                for idx, ch in enumerate(re.split(r"\s+", HOSTNAME_PLACEHOLDER())):
                    if ch not in valid_chars:
                        HOSTNAME_PLACEHOLDER(
                            f"{fabric}:  Invalid character '{ch}' "
                            f"(col {col_vm_ids[idx]})"
                        )
                        chars_ok = overall_ok = False
            if chars_ok:
                HOSTNAME_PLACEHOLDER(f"{fabric}:  All characters are valid as per decode list.")

            # ───── Step 2 – diagonal “-” check ────────────────────────────────
            diag_ok = True
            for rln in rows:
                label, txt = HOSTNAME_PLACEHOLDER("|", 1)
                m = re.search(r"(\d{2})", label)          # get pure digits
                if not m:
                    continue
                row_id = m.group(1)
                idx = int(row_id) - 1
                cells = re.split(r"\s+", HOSTNAME_PLACEHOLDER())
                if idx < len(cells) and cells[idx] != "-":
                    HOSTNAME_PLACEHOLDER(
                        f"{fabric}:  {row_id}x{row_id} Expected '-', got '{cells[idx]}'"
                    )
                    diag_ok = overall_ok = False
                elif idx < len(cells):
                    HOSTNAME_PLACEHOLDER(
                        f"{fabric}: {row_id}x{row_id} '-' is correct (same VM-ID)"
                    )
            if diag_ok:
                HOSTNAME_PLACEHOLDER(
                    f"{fabric}: All same VM-ID combinations have correct '-' across entire matrix"
                )

            # ───── Step 3 – '.' between target VM-IDs ─────────────────────────
            dots_ok = True
            for rln in rows:
                label, txt = HOSTNAME_PLACEHOLDER("|", 1)
                m = re.search(r"(\d{2})", label)
                if not m:
                    continue
                row_id = m.group(1)
                if row_id not in target_vm_ids:
                    continue
                cells = re.split(r"\s+", HOSTNAME_PLACEHOLDER())
                for col_id in target_vm_ids:
                    if col_id == row_id:
                        continue
                    idx = int(col_id) - 1
                    if idx >= len(cells):
                        continue
                    if cells[idx] != ".":
                        HOSTNAME_PLACEHOLDER(
                            f"{fabric}:  {row_id}x{col_id} Expected '.', got '{cells[idx]}'"
                        )
                        dots_ok = overall_ok = False
                    else:
                        HOSTNAME_PLACEHOLDER(
                            f"{fabric}: {row_id}x{col_id} '.' is correct (connection OK)"
                        )
            if dots_ok:
                HOSTNAME_PLACEHOLDER(
                    f"{fabric}: All target VM-ID combinations have correct '.' (connection OK)"
                )

            HOSTNAME_PLACEHOLDER(f"{fabric}: Validation Completed for {fabric} Fabric")

        # ---------------------------------------------------------------- Verdict
        if overall_ok:
            HOSTNAME_PLACEHOLDER("Virtual fabric validation PASSED")
        else:
            HOSTNAME_PLACEHOLDER("Virtual fabric validation FAILED")

        return overall_ok

    @staticmethod
    def compare_values_by_key(sshlogs: str, expected_dict: Dict[str, str]) -> bool:
        HOSTNAME_PLACEHOLDER(f"Reading SSH log file: {sshlogs}")
        try:
            with open(sshlogs, 'r') as f:
                content = f.read()
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Failed to read file: {e}")
            return False

        for key, expected_regex in expected_dict.items():
            key = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(f"Searching for value of '{key}'")
            pattern = rf"{re.escape(key)}\s*:\s*([^\n\r]*)"
            matches = re.findall(pattern, content, re.MULTILINE)

            if matches:
                HOSTNAME_PLACEHOLDER(f"Found {len(matches)} match(es) for key '{key}': {matches}")
                found_match = False
                failed_matches = []

                for i, value in enumerate(matches, 1):
                    HOSTNAME_PLACEHOLDER(f"Checking match {i}/{len(matches)}: '{value}' against regex '{expected_regex}'")
                    try:
                        if re.search(expected_regex, value):
                            HOSTNAME_PLACEHOLDER(f"✓ Match {i} validates against regex pattern")
                            found_match = True
                            break
                        else:
                            HOSTNAME_PLACEHOLDER(f"✗ Match {i} does NOT validate against regex pattern")
                            failed_matches.append(value)
                    except re.error as regex_err:
                        HOSTNAME_PLACEHOLDER(f"Invalid regex pattern '{expected_regex}': {regex_err}")
                        return False

                if not found_match:
                    HOSTNAME_PLACEHOLDER(f"Value mismatch for '{key}': no matches validated against regex '{expected_regex}' in any of the {len(matches)} match(es)")
                    HOSTNAME_PLACEHOLDER(f"All failed matches: {failed_matches}")
                    return False
                else:
                    HOSTNAME_PLACEHOLDER(f"Success: Found value matching regex '{expected_regex}' for key '{key}'")

            else:
                HOSTNAME_PLACEHOLDER(f"Key: '{key}' not found")
                return False

        return True

    @staticmethod
    def validate_fields_from_console_output(console_path: str, expected_fields: Dict[str, str]) -> bool:
        """
        Validate expected field values appear under their specified sections in console output.

        :param console_path: Path to the console output file (text)
        :param expected_fields: Dict where keys are 'field:section' and values are expected values
        :return: True if all fields found correctly, else False immediately when missing
        """
        try:
            with open(console_path, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Failed to read console output file: {e}")
            return False

        current_section = ""

        for line in lines:
            stripped = HOSTNAME_PLACEHOLDER()
            if not stripped:
                continue

            # Detect current section if line ends with ":" and has no other ":" before it
            if HOSTNAME_PLACEHOLDER(":") and ":" not in stripped[:-1]:
                current_section = stripped[:-1].strip()

            # Check all expected fields for this section
            for key, expected_value in expected_fields.items():
                if ":" not in key:
                    HOSTNAME_PLACEHOLDER(f"Invalid key format '{key}', expected 'field:section'")
                    return False
                field_name, section = HOSTNAME_PLACEHOLDER(":", 1)
                if current_section == section:
                    # Look for exact 'field_name: expected_value' substring in line
                    if f"{field_name}: {expected_value}" in stripped:
                        HOSTNAME_PLACEHOLDER(f"Expected value '{expected_value}' for field '{field_name}' found under section '{section}'")
                        # Mark this key as found by removing it
                        expected_fields.pop(key)
                        break

        if expected_fields:
            for key, expected_value in expected_fields.items():
                field_name, section = HOSTNAME_PLACEHOLDER(":", 1)
                HOSTNAME_PLACEHOLDER(f"Expected value '{expected_value}' for field '{field_name}' not found under section '{section}'")
            return False

        return True
