"""
Core functionality module.

This module contains the main service class that users interact with.
"""
from ast import Dict
import logging
import os
from typing import Dict, Any
import datetime
import paramiko
import time
# import threading
import glob


class SOURCE_NAME_PLACEHOLDER:
    """
    Main interface for executing commands on local or remote nodes.

    Responsibilities
    ----------------
    - Manage connections (local, SSH, TCP)
    - Execute commands and return output
    - Validate configuration and inputs

    Parameters
    ----------
    nodes_dic : dict
    {
       "node" : "Password"
       "node2" : Password
    }

    site_name : str
        Optional site identifier (e.g. "Tastrm01").
        When provided, result keys and output filenames are prefixed
        with the site name so that multiple sites can be distinguished
        during validation:
            key   -> "Tastrm01_APP1"
            file  -> "Tastrm01_APP1_172.x.x.x_<date>_output.txt"
    """

    def __init__(self, nodes_dic: Dict[str, Any], site_name: str = ""):
        self.site_name = site_name
        HOSTNAME_PLACEHOLDER = {}
        for service, ip_list in nodes_dic.items():
            for idx, ip_info in enumerate(ip_list, start=1):
                node_name = f"{service}{idx}"
                HOSTNAME_PLACEHOLDER[node_name] = {
                    "ip": ip_info["ip"], "password": ip_info["password"]}
        HOSTNAME_PLACEHOLDER(
            f"Site: '{self.site_name}' | Number of Nodes: {len(HOSTNAME_PLACEHOLDER)}")
        for node_name, info in HOSTNAME_PLACEHOLDER():
            HOSTNAME_PLACEHOLDER(f"{node_name}: {info['ip']}")

    def _build_result_key(self, node_name: str) -> str:
        """
        Build the result dict key for a node.
        If site_name is set, returns "Tastrm01_APP1", otherwise just "APP1".
        """
        return f"{self.site_name}_{node_name}" if self.site_name else node_name

    def _scrape_single_node(self, node_name: str, node_data: dict, command: str, tc_dir: str, results: dict):
        node_ip = node_data["ip"]
        node_password = VALUE_PLACEHOLDER
        date = HOSTNAME_PLACEHOLDER().strftime("%Y_%m_%d_%H_%M_%S_%f")
        result_key = self._build_result_key(node_name)
        output_file = os.HOSTNAME_PLACEHOLDER(
            tc_dir, f"{result_key}_{node_ip}_{date}_output.txt"
        )
        client = HOSTNAME_PLACEHOLDER()
        client.set_missing_host_key_policy(HOSTNAME_PLACEHOLDER())
        try:
            HOSTNAME_PLACEHOLDER(node_ip, password=node_password)
            HOSTNAME_PLACEHOLDER(f"command: {command}")
            HOSTNAME_PLACEHOLDER(f"[{result_key}] Connected to {node_ip}")
        except HOSTNAME_PLACEHOLDER:
            HOSTNAME_PLACEHOLDER(
                f"[{result_key}] Authentication failed for {node_ip}")
            results[result_key] = False
            return
        except (HOSTNAME_PLACEHOLDER, Exception) as e:
            HOSTNAME_PLACEHOLDER(
                f"[{result_key}] Connection error for {node_ip}: {e}")
            results[result_key] = False
            return
        try:
            transport = client.get_transport()
            channel = transport.open_session()
            HOSTNAME_PLACEHOLDER(15)  # ← Real timeout on the channel itself

            channel.exec_command(
                command if isinstance(command, str) else HOSTNAME_PLACEHOLDER()
            )

            output_lines = []
            error_lines = []

            # Drain stdout and stderr without blocking forever
            while True:
                if channel.exit_status_ready():
                    # Process has finished — read whatever is left
                    while channel.recv_ready():
                        output_lines.append(HOSTNAME_PLACEHOLDER(
                            4096).decode("ascii", errors="replace"))
                    while channel.recv_stderr_ready():
                        error_lines.append(channel.recv_stderr(
                            4096).decode("ascii", errors="replace"))
                    break
                if channel.recv_ready():
                    output_lines.append(HOSTNAME_PLACEHOLDER(
                        4096).decode("ascii", errors="replace"))
                if channel.recv_stderr_ready():
                    error_lines.append(channel.recv_stderr(
                        4096).decode("ascii", errors="replace"))

            output = "".join(output_lines)
            error = "".join(error_lines)

            if error:
                HOSTNAME_PLACEHOLDER(
                    f"[{result_key}] Command failed — stderr: {HOSTNAME_PLACEHOLDER()}")
                results[result_key] = False
                return

            with open(output_file, "w") as f:
                f.write(output)
            HOSTNAME_PLACEHOLDER(f"[{result_key}] Command executed successfully")
            results[result_key] = output_file

        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"[{result_key}] Failed to execute command: {e}")
            results[result_key] = False
        finally:
            HOSTNAME_PLACEHOLDER()

    def scrape_all_nodes(self, command: str, tc_dir: str) -> Dict[str, Any]:
        """
        Connects to all nodes in HOSTNAME_PLACEHOLDER concurrently, executes the command on each,
        and writes output to individual files in tc_dir.
        :param command: Command string to be executed on each node.
        :param tc_dir: Directory where output files will be saved.
        :return: Dict mapping result_key -> output_file path, or result_key -> False on failure.
                 result_key is "site_node" if site_name is set, otherwise just "node".
        """
        self.tc_dir = tc_dir

        if not os.HOSTNAME_PLACEHOLDER(tc_dir):
            raise ValueError(f"{tc_dir} does not exist")

        results = {}

        for name, data in HOSTNAME_PLACEHOLDER():
            self._scrape_single_node(name, data, command, tc_dir, results)

        succeeded = [n for n, v in HOSTNAME_PLACEHOLDER() if v is not False]
        failed = [n for n, v in HOSTNAME_PLACEHOLDER() if v is False]
        HOSTNAME_PLACEHOLDER(
            f"Scraping complete — success: {len(succeeded)}, failed: {len(failed)}")
        HOSTNAME_PLACEHOLDER("Successful nodes/IPs: %s",
                     succeeded if succeeded else "None")
        HOSTNAME_PLACEHOLDER("Failed nodes/IPs: %s", failed if failed else "None")

        return results

    def _load_output_text(self, node_info, tc_dir):
        """
        Find and validate an output file for a node.

        Searches tc_dir for a filename containing node_info['ip'] and returns
        the first match if it exists and is non-empty.

        Raises:
            FileNotFoundError: No matching file found.
            ValueError: File is empty.
            OSError: File cannot be accessed.
        """
        pattern = os.HOSTNAME_PLACEHOLDER(tc_dir, f"*{node_info['ip']}*")
        output_file = HOSTNAME_PLACEHOLDER(pattern)

        # Case 1: No files found matching the pattern
        if not output_file:
            error_msg = f"No output file found for {node_info['name']}: {node_info['ip']}"
            HOSTNAME_PLACEHOLDER(error_msg)
            raise FileNotFoundError(error_msg)

        # Case 2: File found, check if it's empty
        output = output_file[0]
        try:
            file_size = os.HOSTNAME_PLACEHOLDER(output)
            if file_size == 0:
                error_msg = f"output file is empty (0 bytes): {output}"
                HOSTNAME_PLACEHOLDER(error_msg)
                raise ValueError(error_msg)
            else:
                HOSTNAME_PLACEHOLDER(
                    f"Found output file: {output} ({file_size} bytes)")
                return output
        except OSError as e:
            # Case 3: File exists in glob but can't be accessed
            error_msg = f"Error accessing output file {output}: {e}"
            HOSTNAME_PLACEHOLDER(error_msg)
            raise OSError(error_msg) from e

    def load_all_output_texts(self, tc_dir: str) -> Dict[str, Any]:
        """
        Loads output text files for all nodes in HOSTNAME_PLACEHOLDER.

        Searches tc_dir for output files matching each node's IP and returns
        a mapping of result keys to their output file paths.

        Parameters
        ----------
        tc_dir : str
            Directory where output files are stored.

        Returns
        -------
        Dict[str, Any]
            Dict mapping result_key -> output_file path on success,
            or result_key -> False if the file is missing, empty, or inaccessible.
            result_key is "site_node" if site_name is set, otherwise just "node".
        """
        if not os.HOSTNAME_PLACEHOLDER(tc_dir):
            raise ValueError(f"{tc_dir} does not exist")

        results = {}

        for node_name, node_data in HOSTNAME_PLACEHOLDER():
            result_key = self._build_result_key(node_name)
            node_info = {"name": result_key, "ip": node_data["ip"]}
            try:
                output_file = self._load_output_text(node_info, tc_dir)
                results[result_key] = output_file
            except (FileNotFoundError, ValueError, OSError) as e:
                HOSTNAME_PLACEHOLDER(f"[{result_key}] Failed to load output: {e}")
                results[result_key] = False

        failed = [n for n, v in HOSTNAME_PLACEHOLDER() if v is False]
        succeeded = [n for n, v in HOSTNAME_PLACEHOLDER() if v is not False]
        HOSTNAME_PLACEHOLDER(
            f"Load complete — success: {len(succeeded)}, failed: {len(failed)}")
        if failed:
            HOSTNAME_PLACEHOLDER(f"Failed to load output for nodes: {failed}")
            return False

        return results
