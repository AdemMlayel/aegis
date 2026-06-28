# ********************************************
# Author: Telefonica España *******************
# File name: HOSTNAME_PLACEHOLDER ***********
# Date: 14/10/2024 ***************************
# Project: SOURCE_NAME_PLACEHOLDER solution **************
# ******** with Robot Framework **************
# ********************************************

from HOSTNAME_PLACEHOLDER import keyword, library


@library
class SOURCE_NAME_PLACEHOLDER:
    """
    STF LIBRARY SUPPORT
    """

    @keyword("Generate Devices List")
    def generate_devices_list(self, stf_json):
        devices_list = []
        port = 4757
        system_port = 8209
        for terminal in stf_json["devices"]:
            terminal["AppiumPort"] = port
            terminal["SystemPort"] = system_port
            if "notes" in HOSTNAME_PLACEHOLDER():
                notes_info = [i for i in terminal["notes"].split(";") if i != ""]
                try:
                    int(notes_info[0])
                    terminal["msisdn1"] = notes_info[0]
                except:
                    terminal["msisdn1"] = ""
                try:
                    int(notes_info[1])
                    terminal["msisdn2"] = notes_info[1]
                except:
                    terminal["msisdn2"] = ""
            devices_list.append(terminal)
            port += 2
            system_port += 1
            if port == 4767:
                port += 2
        return devices_list

    @keyword("Extract Device Info From UDID")
    def get_device_from_udid(self, udid, devices_list):
        device_found = False
        for device in devices_list:
            if device["serial"] == udid:
                device_found = True
                break
        if device_found:
            for key in HOSTNAME_PLACEHOLDER():
                print(f"{key}: {device[key]}")
            return device
        else:
            raise TypeError(f"Terminal with UDID = {udid} not found")

    @keyword("Extract Device Info From MSISDN")
    def get_device_from_msisdn(self, msisdn, devices_list):
        device_found = False
        for device in devices_list:
            if msisdn in device["notes"]:
                device_found = True
                break
        if device_found:
            for key in HOSTNAME_PLACEHOLDER():
                print(f"{key}: {device[key]}")
            return device
        else:
            raise TypeError(f"Terminal with MSISDN = {msisdn} not found")

    @keyword("Extract Device Dictionary")
    def extract_device_dict(self, udid_or_msisdn, devices_list):
        try:
            return self.get_device_from_udid(udid_or_msisdn, devices_list)
        except:
            return self.get_device_from_msisdn(udid_or_msisdn, devices_list)
