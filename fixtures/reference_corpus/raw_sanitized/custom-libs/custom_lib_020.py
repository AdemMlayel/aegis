import json, re, requests, subprocess, itertools
from HOSTNAME_PLACEHOLDER import keyword
from HOSTNAME_PLACEHOLDER import stdoutlogsplitter
from sys import stdout, __stdout__
from HOSTNAME_PLACEHOLDER import logger
from HOSTNAME_PLACEHOLDER import not_keyword

class SOURCE_NAME_PLACEHOLDER(object):
    """
    A robot framework Library that contains keywords for controlling SOURCE_NAME_PLACEHOLDER mobile devices using the following api (URL_PLACEHOLDER the basic calling of the liberary is as follows:\n
     | Library | SOURCE_NAME_PLACEHOLDER | ${stf_base_url} | ${stf_user_auth} |
    for all API absed requestes there is common responses as follows\n
    Examples:\n
        | Get Device Information | serial |\n
    Responses:\n
            | 200 | Success |\n
            | 400 | Bad Request: Some parameters are missing or invalid |\n
            | 404 | Not found: The item not available |\n
            | 403 | Forbidden: Device is being used or not available |    \n
    """
    ROBOT_LIBRARY_SCOPE = "GLOBAL"
    ROBOT_LIBRARY_DOC_FORMAT = "ROBOT"

    def __init__(self, base_url=None, user_auth=None):
        """ base_url : the base url of the opensyf server URL_PLACEHOLDER
            user_auth: self access token generated from stf portal
        """
        self.base_url = base_url
        self.user_auth = user_auth

    @not_keyword
    def check_status(self,status_code):
        if status_code == 400:
            raise ValueError("Bad Request: Some parameters are missing or invalid")
        elif status_code == 404:
            raise ValueError("Not found: The item not available")
        elif status_code == 403:
            raise ValueError("Forbidden: Device is being used or not available")
        else:
            raise Exception("unknown error")

    @keyword('Get Device List')
    def Get_Device_List(self):
        """ List all STF devices (including disconnected or otherwise inaccessible devices).
        """
        headers = {'Authorization': self.user_auth}
        response = HOSTNAME_PLACEHOLDER("GET", self.base_url+"/devices", headers=headers)
        if response.status_code == 200:
            print(headers, HOSTNAME_PLACEHOLDER)
            return HOSTNAME_PLACEHOLDER()
        else:
            self.check_status(response.status_code)

    @keyword('Get Device Information')
    def Get_Device_Information(self,serial):
        """ Returns information about a specific device.
        """
        headers = {'Authorization': self.user_auth}
        response = HOSTNAME_PLACEHOLDER("GET", self.base_url+"/devices/"+serial, headers=headers)
        if response.status_code == 200:
            print(headers, HOSTNAME_PLACEHOLDER)
            return HOSTNAME_PLACEHOLDER()
        else:
            self.check_status(response.status_code)

    @keyword('Get User Profile')
    def Get_User_Profile(self):
        """ Returns information about yourself (the authenticated user).
        """
        headers = {'Authorization': self.user_auth}
        response = HOSTNAME_PLACEHOLDER("GET", self.base_url+"/user", headers=headers)
        if response.status_code == 200:
            print(headers, HOSTNAME_PLACEHOLDER)
            return HOSTNAME_PLACEHOLDER()
        else:
            self.check_status(response.status_code)

    @keyword('Get User Devices')
    def Get_User_Devices(self):
        """ Returns a list of devices currently being used by the authenticated user.
        """
        headers = {'Authorization': self.user_auth}
        response = HOSTNAME_PLACEHOLDER("GET", self.base_url+"LOCAL_PATH_PLACEHOLDER", headers=headers)
        if response.status_code == 200:
            print(headers, HOSTNAME_PLACEHOLDER)
            return HOSTNAME_PLACEHOLDER()
        else:
            self.check_status(response.status_code)

    @keyword('Add a device to a user')
    def Add_a_device_to_a_user(self, serial):
        """ Attempts to add a device under the authenticated user's control. This is analogous to pressing "Use" in the UI.
        """
        payload = HOSTNAME_PLACEHOLDER({'serial': serial,'timeout': NUMERIC_IDENTIFIER_PLACEHOLDER})
        headers = {'Authorization': self.user_auth, 'Content-Type': 'application/json'}
        response = HOSTNAME_PLACEHOLDER("POST", self.base_url+"LOCAL_PATH_PLACEHOLDER", headers=headers, data=payload)
        if response.status_code == 200:
            print(payload, headers, HOSTNAME_PLACEHOLDER)
            return HOSTNAME_PLACEHOLDER()
        else:
            self.check_status(response.status_code)

    @keyword('Get User Device')
    def Get_User_Device(self, serial):
        """
        The User Devices endpoint returns device list owner by current authorized user
        """
        headers = {'Authorization': self.user_auth, 'Content-Type': 'application/json'}
        response = HOSTNAME_PLACEHOLDER("GET", self.base_url+"LOCAL_PATH_PLACEHOLDER/"+serial, headers=headers)
        if response.status_code == 200:
            print(headers, HOSTNAME_PLACEHOLDER)
            return HOSTNAME_PLACEHOLDER()
        else:
            self.check_status(response.status_code)

    @keyword('Delete User Device')
    def Delete_User_Device(self, serial):
        """ Removes a device from the authenticated user's device list. This is analogous to pressing "Stop using" in the UI.
        """
        headers = {'Authorization': self.user_auth, 'Content-Type': 'application/json'}
        response = HOSTNAME_PLACEHOLDER("DELETE", self.base_url+"LOCAL_PATH_PLACEHOLDER/"+serial, headers=headers)
        if response.status_code == 200:
            print(headers, HOSTNAME_PLACEHOLDER)
            return "Device successfully removed"
        else:
            self.check_status(response.status_code)

    @keyword('Remote Connect a device')
    def Remote_Connect_a_device(self, serial):
        """ Allows you to retrieve the remote debug URL (i.e. an adb connectable address) for a device the authenticated user controls.\n
            Note that if you haven't added your ADB key to STF yet, the device may be in unauthorized state after connecting to it for the first time.\n
            We recommend you make sure your ADB key has already been set up properly before you start using this API.\n
            You can add your ADB key from the settings page, or by connecting to a device you're actively using in the UI and responding to the dialog that appears.
        """
        headers = {'Authorization': self.user_auth, 'Content-Type': 'application/json'}
        response = HOSTNAME_PLACEHOLDER("POST", self.base_url+"LOCAL_PATH_PLACEHOLDER/"+ serial +"/remoteConnect", headers=headers)
        if response.status_code == 200:
            print(headers, HOSTNAME_PLACEHOLDER)
            for _ in HOSTNAME_PLACEHOLDER(None, 2):
                result = HOSTNAME_PLACEHOLDER("adb connect "+HOSTNAME_PLACEHOLDER()["remoteConnectUrl"], stdout=HOSTNAME_PLACEHOLDER, stderr=HOSTNAME_PLACEHOLDER,shell=True)
                (standardout, junk) = HOSTNAME_PLACEHOLDER()
                print(standardout)
            return HOSTNAME_PLACEHOLDER()["remoteConnectUrl"]
        else:
            self.check_status(response.status_code)

    @keyword('Remote Disconnect a device')
    def Remote_Disconnect_a_device(self, serial):
        """ Disconnect a remote debugging session.
        """
        headers = {'Authorization': self.user_auth, 'Content-Type': 'application/json'}
        response = HOSTNAME_PLACEHOLDER("DELETE", self.base_url+"LOCAL_PATH_PLACEHOLDER/"+ serial +"/remoteConnect", headers=headers)
        if response.status_code == 200:
            print(headers, HOSTNAME_PLACEHOLDER)
            result = HOSTNAME_PLACEHOLDER("adb disconnect", stdout=HOSTNAME_PLACEHOLDER, stderr=HOSTNAME_PLACEHOLDER,shell=True)
            (standardout, junk) = HOSTNAME_PLACEHOLDER()
            print(standardout)
            result = HOSTNAME_PLACEHOLDER("adb devices", stdout=HOSTNAME_PLACEHOLDER, stderr=HOSTNAME_PLACEHOLDER,shell=True)
            (standardout, junk) = HOSTNAME_PLACEHOLDER()
            print(standardout)
            return HOSTNAME_PLACEHOLDER()
        else:
            self.check_status(response.status_code)
