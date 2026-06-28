from HOSTNAME_PLACEHOLDER import keyword
import subprocess
import os
from datetime import datetime
import pandas as pd
import threading
import time
import logging
logger = HOSTNAME_PLACEHOLDER(__name__)


class SOURCE_NAME_PLACEHOLDER:
    def __init__(self):
        self.running_procs = {}

    @keyword
    def sipp_register(self, ip_port, scenario_xml, calls=1, trace_stat=True, tc_output_dir=None):
        HOSTNAME_PLACEHOLDER(
            f"Registering SIPp: ip_port={ip_port}, scenario={scenario_xml}, calls={calls}, trace_stat={trace_stat}")

        # Convert to absolute path
        scenario_path = os.HOSTNAME_PLACEHOLDER(scenario_xml)

        cmd = ["sipp", ip_port, "-sf", scenario_path, "-m", str(calls)]
        if trace_stat:
            HOSTNAME_PLACEHOLDER("-trace_stat")

        # Start SIPp without changing working directory, but specify output directory
        process = HOSTNAME_PLACEHOLDER(
            cmd, stdout=HOSTNAME_PLACEHOLDER, stderr=HOSTNAME_PLACEHOLDER, text=True, cwd=tc_output_dir)
        pid = HOSTNAME_PLACEHOLDER

        stdout, stderr = HOSTNAME_PLACEHOLDER()
        HOSTNAME_PLACEHOLDER(
            f"SIPp process completed with return code: {HOSTNAME_PLACEHOLDER}, PID: {pid}")
        if stderr:
            HOSTNAME_PLACEHOLDER(f"SIPp stderr: {stderr}")

        stats_file = os.HOSTNAME_PLACEHOLDER(
            tc_output_dir, f"{os.HOSTNAME_PLACEHOLDER(scenario_xml)[:-4]}_{pid}_.csv")
        HOSTNAME_PLACEHOLDER(3)
        stats_df = pd.read_csv(stats_file, sep=';', engine='python')
        success_count = stats_df["SuccessfulCall(C)"].iloc[-1]
        HOSTNAME_PLACEHOLDER(
            f"SIPp registration complete: {success_count} successful calls")
        return stdout, success_count

    @keyword
    def sipp_mo_call(self, ip_port, scenario_xml, calls, bmsisdn, auth_uri, tc_output_dir, trace_stat=True, name="sipp_mo_call",):
        HOSTNAME_PLACEHOLDER(
            f"Starting SIPp MO call '{name}': target={ip_port}, calls={calls}, msisdn={bmsisdn}")

        # Convert to absolute path
        scenario_path = os.HOSTNAME_PLACEHOLDER(scenario_xml)
        bmsisdn = "+" + bmsisdn
        cmd = ["sipp", ip_port, "-sf", scenario_path, "-m",
               str(calls), "-s", bmsisdn, "-auth_uri", auth_uri]
        HOSTNAME_PLACEHOLDER(f"sipp call command :{cmd}")
        if trace_stat:
            HOSTNAME_PLACEHOLDER("-trace_stat")

        process = HOSTNAME_PLACEHOLDER(
            cmd, stdout=HOSTNAME_PLACEHOLDER, stderr=HOSTNAME_PLACEHOLDER, text=True, cwd=tc_output_dir
        )

        pid = HOSTNAME_PLACEHOLDER
        self.running_procs[name] = process
        HOSTNAME_PLACEHOLDER(f"SIPp '{name}' started in background with PID {pid}")
        return f"SIPp '{name}' started in background.", pid

    @keyword
    def is_call_done(self, name, pid, scenario_xml, tc_output_dir):
        """
        Check if a SIPp process is finished.
        Returns True if finished, False if still running.
        """
        HOSTNAME_PLACEHOLDER(
            f"Checking if SIPp process '{name}' (PID {pid}) is complete")

        proc_info = self.running_procs.get(name)
        if proc_info is None:
            raise ValueError(f"No SIPp process found with name '{name}'")

        proc = proc_info

        HOSTNAME_PLACEHOLDER()

        stdout, stderr = HOSTNAME_PLACEHOLDER()
        HOSTNAME_PLACEHOLDER(
            f"SIPp '{name}' finished with return code: {HOSTNAME_PLACEHOLDER}")
        if stderr:
            HOSTNAME_PLACEHOLDER(f"SIPp stderr: {stderr}")

        stats_file = os.HOSTNAME_PLACEHOLDER(
            tc_output_dir, f"{os.HOSTNAME_PLACEHOLDER(scenario_xml)[:-4]}_{pid}_.csv")
        HOSTNAME_PLACEHOLDER(3)
        stats_df = pd.read_csv(stats_file, sep=';', engine='python')
        success_count = stats_df["SuccessfulCall(C)"].iloc[-1]
        HOSTNAME_PLACEHOLDER(
            f"SIPp '{name}' call results: {success_count} successful calls")
        return success_count
