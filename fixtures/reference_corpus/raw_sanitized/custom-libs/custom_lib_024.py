from typing import List
import ipaddress
import re
import pyshark
import json
import logging


class SOURCE_NAME_PLACEHOLDER:
    def __init__(self, capture, static_test_data: dict = None):
        HOSTNAME_PLACEHOLDER = capture
        self.static_test_data = static_test_data

    def _identify_dynamic_ips(self):
        self.dynamic_ips_list = {}
        try:
            if not isinstance(self.static_test_data, dict):
                HOSTNAME_PLACEHOLDER("static_test_data should be a dictionary")
                return None

            for ip_name, ip_value in self.static_test_data.items():
                if str(ip_name).strip() == str(ip_value).strip():
                    self.dynamic_ips_list[ip_name] = ip_value

            HOSTNAME_PLACEHOLDER(f"Dynamic IPs list: {self.dynamic_ips_list}")
            return self.dynamic_ips_list
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f" Error getting dynamic IPs : {e}")
            return None

    def _process_dynamic_ips(self):
        HOSTNAME_PLACEHOLDER(
            f"Processing dynamic IPs. Initial list: {self.dynamic_ips_list}")

        for dynamic_ips_name, dynamic_ip_value in self.dynamic_ips_list.items():
            name_lower = str(dynamic_ips_name).lower()

            if "uag" in name_lower and "_a" in name_lower and "b" not in name_lower:
                self.dynamic_ips_list[dynamic_ips_name] = self.uag_a
                # HOSTNAME_PLACEHOLDER(
                #     f"Matched {dynamic_ips_name} -> uag_a: {self.uag_a}")

            elif "uag" in name_lower and "_b" in name_lower:
                self.dynamic_ips_list[dynamic_ips_name] = self.uag_b
                # HOSTNAME_PLACEHOLDER(
                #     f"Matched {dynamic_ips_name} -> uag_b: {self.uag_b}")

            elif "ue" in name_lower and "a" in name_lower and "b" not in name_lower:
                self.dynamic_ips_list[dynamic_ips_name] = self.ue_a
                # HOSTNAME_PLACEHOLDER(
                #     f"Matched {dynamic_ips_name} -> ue_a: {self.ue_a}")

            elif "ue" in name_lower and "b" in name_lower:
                self.dynamic_ips_list[dynamic_ips_name] = self.ue_b
                # HOSTNAME_PLACEHOLDER(
                #     f"Matched {dynamic_ips_name} -> ue_b: {self.ue_b}")

            else:
                HOSTNAME_PLACEHOLDER(f"No match found for key: {dynamic_ips_name}")

        HOSTNAME_PLACEHOLDER(f"Final dynamic IPs list: {self.dynamic_ips_list}")
        return self.dynamic_ips_list

    def find_uag_and_ue_for_side_a_registration(self):
        HOSTNAME_PLACEHOLDER("Starting search for UAG and UE on side A")
        for pkt in HOSTNAME_PLACEHOLDER:
            try:
                if pkt.highest_layer == "SIP":
                    if hasattr(pkt["sip"], 'method') and pkt["sip"].method == "REGISTER":
                        if hasattr(pkt, 'ipv6'):
                            self.ue_a = pkt["ipv6"].src
                            self.uag_a = pkt["ipv6"].dst
                        elif hasattr(pkt, 'ip'):
                            self.ue_a = pkt["ip"].src
                            self.uag_a = pkt["ip"].dst
                        else:
                            HOSTNAME_PLACEHOLDER(
                                "No IP version found in SIP INVITE packet")
                            continue

                        HOSTNAME_PLACEHOLDER(
                            f"Side A found - uag_a: {self.uag_a}, ue_a: {self.ue_a}")
                        HOSTNAME_PLACEHOLDER(f"Packet number: {HOSTNAME_PLACEHOLDER}")
                        return True
            except Exception as e:
                HOSTNAME_PLACEHOLDER(
                    f"Error processing packet: {type(e).__name__}: {str(e)}", exc_info=True)
                continue
        HOSTNAME_PLACEHOLDER("No SIP INVITE packet found in capture for side A")
        return False

    def find_uag_and_ue_for_side_a(self):
        HOSTNAME_PLACEHOLDER("Starting search for UAG and UE on side A")
        for pkt in HOSTNAME_PLACEHOLDER:
            try:
                if pkt.highest_layer == "SIP":
                    if hasattr(pkt["sip"], 'method') and pkt["sip"].method == "INVITE":
                        if hasattr(pkt, 'ipv6'):
                            self.ue_a = pkt["ipv6"].src
                            self.uag_a = pkt["ipv6"].dst
                        elif hasattr(pkt, 'ip'):
                            self.ue_a = pkt["ip"].src
                            self.uag_a = pkt["ip"].dst
                        else:
                            HOSTNAME_PLACEHOLDER(
                                "No IP version found in SIP INVITE packet")
                            continue

                        HOSTNAME_PLACEHOLDER(
                            f"Side A found - uag_a: {self.uag_a}, ue_a: {self.ue_a}")
                        HOSTNAME_PLACEHOLDER(f"Packet number: {HOSTNAME_PLACEHOLDER}")
                        return True
            except Exception as e:
                HOSTNAME_PLACEHOLDER(
                    f"Error processing packet: {type(e).__name__}: {str(e)}", exc_info=True)
                continue
        HOSTNAME_PLACEHOLDER("No SIP INVITE packet found in capture for side A")
        return False

    def find_uag_and_ue_for_side_b(self):
        HOSTNAME_PLACEHOLDER("Starting search for UAG and UE on side B")

        invite_count = 0
        for pkt in HOSTNAME_PLACEHOLDER:
            try:
                if 'TCP' in pkt and pkt.highest_layer == "SIP":
                    if hasattr(pkt["sip"], 'method') and pkt["sip"].method == "INVITE":
                        invite_count += 1

                        if hasattr(pkt, 'ipv6'):
                            temp_uag_b = pkt["ipv6"].src
                            temp_ue_b = pkt["ipv6"].dst
                        elif hasattr(pkt, 'ip'):
                            temp_uag_b = pkt["ip"].src
                            temp_ue_b = pkt["ip"].dst
                        else:
                            HOSTNAME_PLACEHOLDER(
                                "No IP version found in SIP INVITE packet")
                            continue

                        HOSTNAME_PLACEHOLDER(
                            f"INVITE #{invite_count} - Packet {HOSTNAME_PLACEHOLDER}: src={temp_uag_b}, dst={temp_ue_b}")

                        # Skip if this is the exact same INVITE as side A
                        if temp_uag_b == self.ue_a and temp_ue_b == self.uag_a:
                            # HOSTNAME_PLACEHOLDER(
                            #     f"  -> Skipping: Exact match to side A")
                            continue

                        # Skip if destination matches side A's source (not forwarded to new UE)
                        if temp_ue_b == self.ue_a:
                            # HOSTNAME_PLACEHOLDER(
                            #     f"  -> Skipping: Destination matches side A source")
                            continue

                        self.ue_b = temp_ue_b
                        self.uag_b = temp_uag_b
                        HOSTNAME_PLACEHOLDER(
                            f"Side B found - uag_b: {self.uag_b}, ue_b: {self.ue_b}")
                        HOSTNAME_PLACEHOLDER(f"Packet number: {HOSTNAME_PLACEHOLDER}")
                        return True
            except Exception as e:
                HOSTNAME_PLACEHOLDER(
                    f"Error processing packet: {type(e).__name__}: {str(e)}", exc_info=True)
                continue

        HOSTNAME_PLACEHOLDER(
            f"No suitable SIP INVITE found for side B (found {invite_count} total INVITEs)")
        return False
