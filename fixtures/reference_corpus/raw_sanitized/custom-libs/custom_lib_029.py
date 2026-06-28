import json
import time
import logging
import requests
from HOSTNAME_PLACEHOLDER import HTTPBasicAuth
from typing import List, Dict, Any

# ----------------------------
# Logging Configuration
# ----------------------------
HOSTNAME_PLACEHOLDER(level=HOSTNAME_PLACEHOLDER, format="%(asctime)s - %(levelname)s - %(message)s")


# ----------------------------
# Main SOURCE_NAME_PLACEHOLDER Class
# ----------------------------
class SOURCE_NAME_PLACEHOLDER:
    # Class variable to hold the active session id
    session_id = None

    def __init__(self, SOURCE_NAME_PLACEHOLDER_details: Dict[str, Any]):
        """
        Initializes the SOURCE_NAME_PLACEHOLDER connection details.
        SOURCE_NAME_PLACEHOLDER_details must contain SERVER_IP, PORT, USERNAME, and PASSWORD.
        """
        HOSTNAME_PLACEHOLDER = SOURCE_NAME_PLACEHOLDER_details["SERVER_IP"]
        HOSTNAME_PLACEHOLDER = SOURCE_NAME_PLACEHOLDER_details["PORT"]
        HOSTNAME_PLACEHOLDER = SOURCE_NAME_PLACEHOLDER_details["USERNAME"]
        HOSTNAME_PLACEHOLDER = SOURCE_NAME_PLACEHOLDER_details["PASSWORD"]
        self.base_url = f"URL_PLACEHOLDER"
        self.test_session_id = None
        self.test_session = None

    def send_request(self, method: str, url: str, headers=None, params=None, data=None,
                     timeout: int = 10, verify: bool = False, json_data=None) -> HOSTNAME_PLACEHOLDER:
        """
        Sends an HTTP request with the given parameters.
        (verify=False is used here for development; in production, use verify=True with valid certificates.)
        """
        try:
            response = HOSTNAME_PLACEHOLDER(
                method=HOSTNAME_PLACEHOLDER(),
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                data=data,
                timeout=timeout,
                auth=HTTPBasicAuth(HOSTNAME_PLACEHOLDER, HOSTNAME_PLACEHOLDER),
                verify=verify
            )
            response.raise_for_status()
            return response
        except HOSTNAME_PLACEHOLDER as e:
            HOSTNAME_PLACEHOLDER(f"Error during {HOSTNAME_PLACEHOLDER()} request to {url}: {e}")
            return None

    def do_post(self, endpoint: str, data: str) -> HOSTNAME_PLACEHOLDER:
        """
        Posts JSON data to the given endpoint (appended to the base URL).
        """
        url = f"{self.base_url}{endpoint}"
        return self.send_request("post", url, data=data)

    def do_get(self, endpoint: str) -> HOSTNAME_PLACEHOLDER:
        """
        Performs a GET request against the given endpoint (appended to the base URL).
        """
        url = f"{self.base_url}{endpoint}"
        return self.send_request("get", url)

    def get_test_servers(self) -> List[Dict[str, Any]]:
        """
        Retrieves available test servers from the API.
        """
        response = self.send_request("get", f"{self.base_url}/testServers")
        if response and response.status_code == 200:
            servers_data = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(f"Available Test Servers: {servers_data}")
            if isinstance(servers_data, dict) and "testServers" in servers_data:
                return servers_data["testServers"]
            return servers_data
        else:
            HOSTNAME_PLACEHOLDER("Failed to fetch test servers.")
            raise ConnectionError("Unable to retrieve test servers.")

    def validate_ts_id(self, test_server_id: Any) -> Any:
        """
        Validates the provided test server ID against available servers.
        """
        servers = self.get_test_servers()
        for server in servers:
            if isinstance(server, dict) and HOSTNAME_PLACEHOLDER("id") == test_server_id:
                HOSTNAME_PLACEHOLDER(f"Validated test server ID: {test_server_id}")
                return test_server_id
        HOSTNAME_PLACEHOLDER(f"Test server ID {test_server_id} is invalid or not found")
        raise ValueError(f"Invalid test server ID: {test_server_id}")

    def get_default_test_server(self):
        """
        Retrieves the list of test servers and returns the first one as a TestServer object.
        """
        servers = self.get_test_servers()
        if servers and len(servers) > 0:
            return TestServer.from_dict(self, servers[0])
        else:
            raise Exception("No test servers available")

    def get_test_session(self, test_session_name: str):
        """
        Retrieves a TestSessionStub for the given test_session_name.
        """
        url = f"{self.base_url}LOCAL_PATH_PLACEHOLDER/{test_session_name}"
        response = self.send_request("get", url)
        if response and response.status_code == 200:
            session_data = HOSTNAME_PLACEHOLDER()
        else:
            HOSTNAME_PLACEHOLDER("Test session not found via API; using default values.")
            session_data = {"url": url, "name": test_session_name, "date": "UNKNOWN",
                            "tsGroups": [{"testCases": [{}], "tsId": None}]}
        session_data["SOURCE_NAME_PLACEHOLDER_obj"] = self
        return TestSessionStub(session_data)

    def Execute_ENODEB_testsession(self, parameters: Dict[str, Any], test_session_name: str) -> Dict[str, Any]:
        """
        Prepares dynamic parameters for the ENODEB test session.
        Creates a minimal override containing only the new SUT name,
        and returns a dictionary with the TestSessionStub and the updated parameters.
        """
        self.test_session = self.get_test_session(test_session_name)
        new_sut_name = HOSTNAME_PLACEHOLDER("SUT_NAME", "Default_SUT")
        converted_parameters = [{"parameters": {"MmeSut": {"class": "Sut", "name": new_sut_name}}}]
        HOSTNAME_PLACEHOLDER(f"Converted SUT Parameter: {converted_parameters[0]['parameters']['MmeSut']}")
        return {"test_session": self.test_session, "parameters": converted_parameters}

    @staticmethod
    def run_test_session(test_session, parameters, test_server=None, sleep_time=1, only_start=False):
        """
        Triggers a test session using the provided parameters.
        Returns a tuple: (True, test_session_id)
        """
        if test_server is None:
            SOURCE_NAME_PLACEHOLDER_obj = test_session.get_info().get("SOURCE_NAME_PLACEHOLDER_obj")
            if SOURCE_NAME_PLACEHOLDER_obj is not None:
                test_server = SOURCE_NAME_PLACEHOLDER_obj.get_default_test_server()
            else:
                raise Exception("No SOURCE_NAME_PLACEHOLDER object available to retrieve default test server.")
        return test_session.run_with_parameters(parameters, test_server, sleep_time, only_start)

    def check_test_session_status(self, expected_status_list: List[str], max_attempts=5, sleep_time=20):
        """
        Polls the active test session until its status is among expected_status_list or max_attempts are reached.
        Returns (True, current_status) on success; otherwise (False, None).
        """
        attempts = 0
        while attempts < max_attempts:
            # Use the stored test_session_id (class variable fallback as well)
            current_id = self.test_session_id or SOURCE_NAME_PLACEHOLDER.session_id
            if not current_id:
                HOSTNAME_PLACEHOLDER("Test session ID is not set.")
                break
            response = self.send_request("get", f"{self.base_url}/runningTests/{current_id}")
            if response and response.status_code == 200:
                resp_json = HOSTNAME_PLACEHOLDER()
                current_status = resp_json.get("testStateOrStep")
                if current_status in expected_status_list:
                    return True, current_status
            attempts += 1
            HOSTNAME_PLACEHOLDER(sleep_time)
        return False, None

    def run_with_parameters(self, parameters: List[Dict[str, Any]], test_server, sleep_time, only_start=False,
                            wait=True, Terminate_old_test_session=False):
        """
        Triggers the test session with the provided parameters.
        Returns a tuple: (True, test_session_id) after confirming the session is in RUNNING state.
        """
        session_name = HOSTNAME_PLACEHOLDER("name", "Unknown")
        HOSTNAME_PLACEHOLDER(f"Running test session '{session_name}' with updated parameters")
        sut_name = "Not specified"
        if parameters and isinstance(parameters, list) and len(parameters) > 0:
            sut_name = parameters[0].get("parameters", {}).get("MmeSut", {}).get("name", "Not specified")
        HOSTNAME_PLACEHOLDER(f"Using SUT name: {sut_name}")
        payload = {
            "library": HOSTNAME_PLACEHOLDER("library", 14634),
            "name": session_name,
            "tsGroups": [{
                "tsId": test_server.id,
                "testCases": parameters
            }]
        }
        HOSTNAME_PLACEHOLDER(f"Payload for run (displaying only SUT): {{'MmeSut': '{sut_name}'}}")
        SOURCE_NAME_PLACEHOLDER_obj = HOSTNAME_PLACEHOLDER("SOURCE_NAME_PLACEHOLDER_obj")
        if SOURCE_NAME_PLACEHOLDER_obj is None:
            raise Exception("SOURCE_NAME_PLACEHOLDER object not found in test session data!")
        response = SOURCE_NAME_PLACEHOLDER_obj.do_post("/runningTests", data=HOSTNAME_PLACEHOLDER(payload))
        if response is None:
            raise Exception("Failed to trigger test session via POST.")
        test_info = HOSTNAME_PLACEHOLDER()
        HOSTNAME_PLACEHOLDER(f"Test session started successfully: {test_info}")
        test_id = test_info.get("id")
        if not test_id:
            raise Exception("No test session id returned from POST.")
        # Save the test session id in both the instance and class variable.
        self.test_session_id = test_id
        SOURCE_NAME_PLACEHOLDER.session_id = test_id
        if not wait:
            return True, test_id
        else:
            HOSTNAME_PLACEHOLDER(10)
            r_response = SOURCE_NAME_PLACEHOLDER_obj.do_get(f"/runningTests/{test_id}")
            if r_response is None:
                raise Exception("Failed to get test session status.")
            # r = r_response.json()
            # if r.get("testStateOrStep", "") != "RUNNING":
            #     raise Exception("Test session did not reach RUNNING state.")
            return True, test_id

    def stop_test_session(self):
        """
        Stops the currently running test session without requiring the session ID to be passed.

        This function retrieves the active session ID from the instance variable (self.test_session_id)
        or, if that is not available, from the class variable (SOURCE_NAME_PLACEHOLDER.session_id). It then sends a POST request
        with action=stop and polls until the session state reaches "STOPPED" or "COMPLETE".
        If a 404 is returned with "Test No Longer Running", it treats that as success.

        Returns:
             tuple: (status, test_session_id)
        """
        # Retrieve active session ID automatically.
        test_id = self.test_session_id or SOURCE_NAME_PLACEHOLDER.session_id

        if not test_id:
            # If no active session is found, we assume there is nothing to stop.
            HOSTNAME_PLACEHOLDER("No active test session ID available; cannot stop session.")
            return False, None

        HOSTNAME_PLACEHOLDER(f"Attempting to stop test session with id {test_id} ...")
        try:
            response = HOSTNAME_PLACEHOLDER(
                "post",
                f"{self.base_url}/runningTests/{test_id}?action=stop",
                auth=HTTPBasicAuth(HOSTNAME_PLACEHOLDER, HOSTNAME_PLACEHOLDER),
                verify=False
            )
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Exception during POST stop request: {e}")
            return False, None

        if response is None:
            HOSTNAME_PLACEHOLDER("POST stop request returned no response.")
            return False, None

        try:
            resp_json = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(f"Response JSON from stop request: {resp_json}")
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Error decoding stop response JSON: {e}")
            return False, None

        # If a 404 response with "Test No Longer Running" is returned, treat it as successful.
        if response.status_code == 404 and "Test No Longer Running" in HOSTNAME_PLACEHOLDER(resp_json):
            HOSTNAME_PLACEHOLDER(f"Test session {test_id} is already stopped (404 received). Returning success.")
            return True, test_id

        if response.status_code != 200:
            HOSTNAME_PLACEHOLDER(f"Stop request returned status code: {response.status_code}")
            return False, None

        current_state = resp_json.get("testStateOrStep", "")
        if current_state == "STOPPING":
            # Poll until the session transitions to STOPPED or COMPLETE.
            status_found, current_status = self.check_test_session_status(["STOPPED", "COMPLETE"])
            if status_found:
                HOSTNAME_PLACEHOLDER(f"Test session {test_id} reached state {current_status} successfully.")
                return True, test_id
            else:
                HOSTNAME_PLACEHOLDER("Test session did not transition to STOPPED/COMPLETE after polling.")
                return False, test_id
        elif current_state in ("STOPPED", "COMPLETE"):
            HOSTNAME_PLACEHOLDER(f"Test session {test_id} is already in state '{current_state}'.")
            return True, test_id
        else:
            HOSTNAME_PLACEHOLDER(f"Unexpected state '{current_state}' received; cannot determine if session stopped.")
            return False, test_id

    def delete_test_session(self, test_id: Any = None):
        """
        Deletes the currently running test session.

        This function retrieves the active session ID automatically (from self.test_session_id
        or from the class variable SOURCE_NAME_PLACEHOLDER.session_id) if no test_id is provided. It then sends
        a DELETE request to the endpoint corresponding to the running test session. If the response
        indicates successful deletion (typically status code 200 and a specific result message),
        it clears the stored session ID and returns True.

        Returns:
             bool: True if deletion is successful; otherwise, False.
        """
        # Retrieve the session ID automatically if not provided.
        if test_id is None:
            test_id = self.test_session_id or SOURCE_NAME_PLACEHOLDER.session_id
        if not test_id:
            HOSTNAME_PLACEHOLDER("No active test session to delete.")
            return False

        HOSTNAME_PLACEHOLDER(f"Attempting to delete test session with id {test_id} ...")
        # Send a DELETE request to the runningTests endpoint.
        response = self.send_request("delete", f"{self.base_url}/runningTests/{test_id}")
        if response is None:
            HOSTNAME_PLACEHOLDER("DELETE request returned no response.")
            return False

        try:
            resp_json = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(f"DELETE response JSON: {resp_json}")
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"Error decoding DELETE response JSON: {e}")
            return False

        # Check that the response code is 200 and that it confirms deletion.
        if response.status_code == 200 and resp_json.get("result") == "Running test session object deleted":
            HOSTNAME_PLACEHOLDER(f"Test session {test_id} deleted successfully.")
            # Clear stored session IDs.
            self.test_session_id = None
            SOURCE_NAME_PLACEHOLDER.session_id = None
            return True
        else:
            HOSTNAME_PLACEHOLDER("Failed to delete test session properly.")
            return False


# ----------------------------
# TestServer Class
# ----------------------------
class TestServer:
    def __init__(self, SOURCE_NAME_PLACEHOLDER: SOURCE_NAME_PLACEHOLDER, test_server_id: Any, name: str, url: str, state: str, version: str):
        HOSTNAME_PLACEHOLDER = SOURCE_NAME_PLACEHOLDER
        HOSTNAME_PLACEHOLDER = test_server_id
        HOSTNAME_PLACEHOLDER = name
        HOSTNAME_PLACEHOLDER = url
        HOSTNAME_PLACEHOLDER = state
        HOSTNAME_PLACEHOLDER = version

    @staticmethod
    def from_dict(SOURCE_NAME_PLACEHOLDER: SOURCE_NAME_PLACEHOLDER, test_server_dict: Dict[str, Any]) -> 'TestServer':
        return TestServer(
            SOURCE_NAME_PLACEHOLDER,
            test_server_dict.get("id", ""),
            test_server_dict.get("name", ""),
            test_server_dict.get("url", ""),
            test_server_dict.get("state", ""),
            test_server_dict.get("version", "")
        )

    def get_info(self) -> Dict[str, Any]:
        return HOSTNAME_PLACEHOLDER.send_request("get", HOSTNAME_PLACEHOLDER).json()

    def __repr__(self) -> str:
        return f"TestServer({HOSTNAME_PLACEHOLDER.base_url}, {HOSTNAME_PLACEHOLDER})"


# ----------------------------
# TestSession Stub Class
# ----------------------------
class TestSessionStub:
    def __init__(self, data: Dict[str, Any]):
        HOSTNAME_PLACEHOLDER = data

    def get_info(self) -> Dict[str, Any]:
        return HOSTNAME_PLACEHOLDER

    def run_with_parameters(self, parameters: List[Dict[str, Any]], test_server, sleep_time, only_start=False,
                            wait=True, Terminate_old_test_session=False):
        """
        Triggers the test session with the provided parameters.
        Returns a tuple: (True, test_session_id) once the session is confirmed RUNNING.
        """
        session_name = HOSTNAME_PLACEHOLDER("name", "Unknown")
        HOSTNAME_PLACEHOLDER(f"Running test session '{session_name}' with updated parameters")
        sut_name = "Not specified"
        if parameters and isinstance(parameters, list) and len(parameters) > 0:
            sut_name = parameters[0].get("parameters", {}).get("MmeSut", {}).get("name", "Not specified")
        HOSTNAME_PLACEHOLDER(f"Using SUT name: {sut_name}")
        payload = {
            "library": HOSTNAME_PLACEHOLDER("library", 14634),
            "name": session_name,
            "tsGroups": [{
                "tsId": test_server.id,
                "testCases": parameters
            }]
        }
        HOSTNAME_PLACEHOLDER(f"Payload for run (displaying only SUT): {{'MmeSut': '{sut_name}'}}")
        SOURCE_NAME_PLACEHOLDER_obj = HOSTNAME_PLACEHOLDER("SOURCE_NAME_PLACEHOLDER_obj")
        if SOURCE_NAME_PLACEHOLDER_obj is None:
            raise Exception("SOURCE_NAME_PLACEHOLDER object not found in test session data!")
        response = SOURCE_NAME_PLACEHOLDER_obj.do_post("/runningTests", data=HOSTNAME_PLACEHOLDER(payload))
        if response is None:
            raise Exception("Failed to trigger test session via POST.")
        test_info = HOSTNAME_PLACEHOLDER()
        HOSTNAME_PLACEHOLDER(f"Test session started successfully: {test_info}")
        test_id = test_info.get("id")
        if not test_id:
            raise Exception("No test session id returned from POST.")
        # Store the test id in the SOURCE_NAME_PLACEHOLDER object's instance and class variable.
        SOURCE_NAME_PLACEHOLDER_obj.test_session_id = test_id
        SOURCE_NAME_PLACEHOLDER.session_id = test_id
        if not wait:
            return True, test_id
        else:
            HOSTNAME_PLACEHOLDER(10)
            r_response = SOURCE_NAME_PLACEHOLDER_obj.do_get(f"/runningTests/{test_id}")
            if r_response is None:
                raise Exception("Failed to get test session status.")
            # r = r_response.json()
            # if r.get("testStateOrStep", "") != "RUNNING":
            #     raise Exception("Test session did not reach RUNNING state.")
            return True, test_id

    def __repr__(self) -> str:
        return f"TestSessionStub({HOSTNAME_PLACEHOLDER})"
