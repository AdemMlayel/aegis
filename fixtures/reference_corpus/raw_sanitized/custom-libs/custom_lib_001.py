"""
	This module connects robot framework and the remote applications using APIs.

	This script requires that `requests==2.28.1` `urllib3==1.26.11` be installed within the Python
	environment you are running this script in.

	This file can also be imported as a module and contains the following
	Classes:

	* SOURCE_NAME_PLACEHOLDER - This class establishes connection to the any application and
	            execute some functions using APIs.
"""

from __future__ import annotations
import sys
import time
import logging
import json
from typing import Dict, Any, Tuple
from os.path import dirname, abspath
import requests
import urllib3
import io
import HOSTNAME_PLACEHOLDER
import pycurl
debug = True
import jwt
import requests,os,logging
import uuid
#from libraries import SOURCE_NAME_PLACEHOLDER
from . import SOURCE_NAME_PLACEHOLDER
HOSTNAME_PLACEHOLDER("..")
HOSTNAME_PLACEHOLDER(dirname(dirname(abspath(__file__))))

urllib3.disable_warnings(HOSTNAME_PLACEHOLDER)
class SOURCE_NAME_PLACEHOLDER:
    """
     This class establishes connection to the any application and execute some functions using APIs.
		Args:
			app_url (str): application url
		Functions:
			* __build_api_url__ - Returns the URL of SOURCE_NAME_PLACEHOLDER Landslide.
			* do_get - Get API call with given path and returns dictionary.
			* do_get_with_full_url - Get API call to the given URL and returns dictionary.
			* do_post - POST API call with given path and data, then returns dictionary.
			* do_post_with_full_url - POST API call with given URL and data, then returns dictionary.
			* do_delete - DELETE API call with given path and data, then returns dictionary.
			* do_delete_with_full_url - DELETE API call with URL and data, then returns dictionary.
	"""

    def __init__(self, app_url, headers):
        """
			A constructor to build a connection with any application using app_url and APIs
			Args:
				app_url (str): application url
		"""
        self.app_url = app_url
        HOSTNAME_PLACEHOLDER = headers
        HOSTNAME_PLACEHOLDER("Application URL: %s", app_url)

    def __build_api_url__(self, path: str) -> str:
        """
			Returns the URL of an endpoint
			Args:
				path(str): Path that needs to be appended at the end of the url
			Returns:
				str: Full URL of the endpoint
		"""
        return "{url}{path}".format(url=self.app_url, path=path)

    def do_get(self, path: str, parameters = None):
        """
			Get API call with given path and returns dictionary.
			Args:
				path(str): Path that needs to be appended at the end of the url
			Returns:
				dict: Output of the call
		"""
        return self.do_get_with_full_url(self.__build_api_url__(path), parameters)

    def do_get_with_full_url(self, url: str, parameters=None):
        """
			Get API call to the given URL and returns dictionary.
			Args:
				url(str): URL to be fired.
			Returns:
				dict: Output of the call.
		"""
        HOSTNAME_PLACEHOLDER(f"paramters inside get {parameters}")
        return HOSTNAME_PLACEHOLDER(url, headers=HOSTNAME_PLACEHOLDER, verify=False, timeout=50, params=parameters)

    def do_post(self, path: str, data: Dict, parameters=None,gme_headers=False):
        """
			POST API call with given path and returns dictionary.
			Args:
				path(str): Path that needs to be appended at the end of the url
				data(dict): data to be passed along with the request.
			Returns:
				dict: Output of the call.
		"""
        url = self.__build_api_url__(path)

        if gme_headers:
                custom_headers = {"Accept": "application/json","Content-Type": "application/x-www-form-urlencoded"}
                return self.do_post_with_full_url(url=url, data=data, parameters=parameters, headers=custom_headers)

        return self.do_post_with_full_url(url=url, data=data, parameters=parameters)

    def do_post_with_full_url(self, url: str, data, parameters=None,headers=None):
        """
			POST API call to the given URL and data then returns dictionary.
			Args:
				url(str): URL to be fired.
				data(dict): data to be passed along with the request.
			Returns:
				dict: Output of the call.
		"""
        final_headers = headers if headers else HOSTNAME_PLACEHOLDER
        HOSTNAME_PLACEHOLDER("The endpoint url is: %s", url)
        HOSTNAME_PLACEHOLDER(f"Request header is: {final_headers}")
        HOSTNAME_PLACEHOLDER(f"Request payload is: {data}")
        return HOSTNAME_PLACEHOLDER(
            url, headers=final_headers, data=data, verify=False, timeout=50, params=parameters
        )

    def do_post_no_data(self, path: str, parameters=None):
        """
			POST API call with given path and returns dictionary.
			Args:
				path(str): Path that needs to be appended at the end of the url
				data(dict): data to be passed along with the request.
			Returns:
				dict: Output of the call.
		"""
        return self.do_post_with_full_url_no_data(self.__build_api_url__(path), \
                                          parameters=parameters)
    def do_post_with_full_url_no_data(self, url: str, parameters=None):
        """
			POST API call to the given URL and data then returns dictionary.
			Args:
				url(str): URL to be fired.
				data(dict): data to be passed along with the request.
			Returns:
				dict: Output of the call.
		"""
        HOSTNAME_PLACEHOLDER("The endpoint url is: %s",{url})
        HOSTNAME_PLACEHOLDER(f"Request header is: {HOSTNAME_PLACEHOLDER}")

        return HOSTNAME_PLACEHOLDER(
            url, headers=HOSTNAME_PLACEHOLDER,  verify=False, timeout=50, params=parameters
        )


    def do_delete(self, path: str,parameters=None):
        """
			DELETE API call with given path and returns dictionary.
			Args:
				path(str): Path that needs to be appended at the end of the url
				data(dict): data to be passed along with the request.
			Returns:
				dict: Output of the call.
		"""
        return self.do_delete_with_full_url(self.__build_api_url__(path), \
                                             parameters=parameters)

    def do_delete_with_full_url(self, url: str, parameters=None):
        """
			DELETE API call to the given URL and data, then returns dictionary.
			Args:
				url(str): URL to be fired.
				data(dict): data to be passed along with the request.
			Returns:
				dict: Output of the call.
		"""
        HOSTNAME_PLACEHOLDER("Inside delte wih full url")
        HOSTNAME_PLACEHOLDER(f"url is {url} parameters are {parameters}")
        HOSTNAME_PLACEHOLDER(f"headers for delete are {HOSTNAME_PLACEHOLDER}")
        return HOSTNAME_PLACEHOLDER(

            url,headers=HOSTNAME_PLACEHOLDER,\
            verify=False, timeout=22, params=parameters
        )

    #Code for latenecy dashboard start
    def do_post_curl(self,path: str, data: Dict, parameters=None,response_buffer=None,header_buffer=None,curl_obj=None,gme_headers=False):
        """
			POST API call with given path and returns dictionary.
			Args:
				path(str): Path that needs to be appended at the end of the url
				data(dict): data to be passed along with the request.
			Returns:
				dict: Output of the call.
		"""
        url = self.__build_api_url__(path)
        if gme_headers:
            custom_headers = {"Accept": "application/json","Content-Type": "application/x-www-form-urlencoded"}
            return self.do_post_curl_with_full_url(url=url, data=data, parameters=parameters,response_buffer=response_buffer,header_buffer=header_buffer,curl_obj=curl_obj,headers=custom_headers)

        return self.do_post_curl_with_full_url(url=url, data=data, \
                                          parameters=parameters,response_buffer=response_buffer,header_buffer=header_buffer,curl_obj=curl_obj)

    def do_post_curl_with_full_url(self,url: str,data,parameters=None,response_buffer=None,header_buffer=None,curl_obj=None,headers=None):
        if curl_obj is None:
            curl = HOSTNAME_PLACEHOLDER()
        else:
            curl = curl_obj
        HOSTNAME_PLACEHOLDER(pycurl.FORBID_REUSE, 1)  # Forzar cierre de conexión tras uso
        HOSTNAME_PLACEHOLDER(pycurl.FRESH_CONNECT, 1)  # Forzar nueva conexión
        HOSTNAME_PLACEHOLDER(pycurl.DNS_CACHE_TIMEOUT, 0)  # Deshabilitar caché de DNS completamente
        # Set url, headers and postfields
        if headers:
            if HOSTNAME_PLACEHOLDER('Content-Type')=="application/x-www-form-urlencoded" or HOSTNAME_PLACEHOLDER('content-type')=="application/x-www-form-urlencoded":
                data=HOSTNAME_PLACEHOLDER(data)
        else:
            if HOSTNAME_PLACEHOLDER('Content-Type')=="application/x-www-form-urlencoded" or HOSTNAME_PLACEHOLDER('content-type')=="application/x-www-form-urlencoded":
                data=HOSTNAME_PLACEHOLDER(data)
        final_headers = headers if headers else HOSTNAME_PLACEHOLDER
        if debug == True:
            HOSTNAME_PLACEHOLDER( f"~~~~~~~~~~ URL: {url}")
            HOSTNAME_PLACEHOLDER( f"~~~~~~~~~~ headers: {final_headers}")
            HOSTNAME_PLACEHOLDER( f"~~~~~~~~~~ postfields: {data}")
        HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER, url)
        if final_headers:
            if isinstance(final_headers, dict):
                header_list = [f'{key}: {value}' for key, value in final_headers.items()]
            elif isinstance(final_headers, list):
                header_list = final_headers
            else:
                raise ValueError("Headers must be either a dictionary or a list")
            HOSTNAME_PLACEHOLDER(f"{header_list}")
            HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER, header_list)
            HOSTNAME_PLACEHOLDER(f"hello")
        start_time = HOSTNAME_PLACEHOLDER()
        HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER, data)
            # Prepare the buffer to capture response body
        HOSTNAME_PLACEHOLDER(f"hello data")
        HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER, response_buffer)
        HOSTNAME_PLACEHOLDER(f"hello buffer")


        HOSTNAME_PLACEHOLDER(pycurl.SSL_VERIFYPEER, 0)
        HOSTNAME_PLACEHOLDER(pycurl.SSL_VERIFYHOST, 0)
        HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER, header_buffer.write)
        #HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER, True)


        HOSTNAME_PLACEHOLDER()


        # Total latency (manual calculation)
        latency = HOSTNAME_PLACEHOLDER() - start_time

        status_code = HOSTNAME_PLACEHOLDER(pycurl.HTTP_CODE)

        pool_stablishment=False
        latency_details = self.get_curl_timing_information(curl, latency, pool_stablishment)

        latency_total_time = HOSTNAME_PLACEHOLDER(curl.TOTAL_TIME)

        return response_buffer, latency_total_time, status_code, latency_details,header_buffer


    def do_get_curl(self, path: str, parameters = None,response_buffer=None,header_buffer=None,curl_obj=None):
        """
			Get API call with given path and returns dictionary.
			Args:
				path(str): Path that needs to be appended at the end of the url
			Returns:
				dict: Output of the call
		"""
        return self.do_get_curl_with_full_url(self.__build_api_url__(path), parameters,response_buffer=response_buffer,header_buffer=header_buffer,curl_obj=curl_obj)
    def do_get_curl_with_full_url(self, url: str, parameters=None,response_buffer=None,header_buffer=None,curl_obj=None):
        if curl_obj is None:
            curl = HOSTNAME_PLACEHOLDER()
        else:
            curl = curl_obj
        HOSTNAME_PLACEHOLDER(pycurl.FORBID_REUSE, 1)  # Forzar cierre de conexión tras uso
        HOSTNAME_PLACEHOLDER(pycurl.FRESH_CONNECT, 1)  # Forzar nueva conexión
        HOSTNAME_PLACEHOLDER(pycurl.DNS_CACHE_TIMEOUT, 0)  # Deshabilitar caché de DNS completamente
        # Set url, headers

        if debug == True:
            HOSTNAME_PLACEHOLDER( f"~~~~~~~~~~ URL: {url}")
            HOSTNAME_PLACEHOLDER( f"~~~~~~~~~~ headers: {HOSTNAME_PLACEHOLDER}")
        HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER, url)
        if HOSTNAME_PLACEHOLDER:
            if isinstance(HOSTNAME_PLACEHOLDER, dict):
                header_list = [f'{key}: {value}' for key, value in HOSTNAME_PLACEHOLDER()]
            elif isinstance(HOSTNAME_PLACEHOLDER, list):
                header_list = HOSTNAME_PLACEHOLDER
            else:
                raise ValueError("Headers must be either a dictionary or a list")
            HOSTNAME_PLACEHOLDER(f"{header_list}")
            HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER, header_list)
            HOSTNAME_PLACEHOLDER(f"hello")
        start_time = HOSTNAME_PLACEHOLDER()
        HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER, response_buffer)
        HOSTNAME_PLACEHOLDER(f"hello buffer")


        HOSTNAME_PLACEHOLDER(pycurl.SSL_VERIFYPEER, 0)
        HOSTNAME_PLACEHOLDER(pycurl.SSL_VERIFYHOST, 0)
        HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER, header_buffer.write)
        #HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER, True)


        HOSTNAME_PLACEHOLDER()


        # Total latency (manual calculation)
        latency = HOSTNAME_PLACEHOLDER() - start_time

        status_code = HOSTNAME_PLACEHOLDER(pycurl.HTTP_CODE)

        pool_stablishment=False
        latency_details = self.get_curl_timing_information(curl, latency, pool_stablishment)

        latency_total_time = HOSTNAME_PLACEHOLDER(curl.TOTAL_TIME)

        return response_buffer, latency_total_time, status_code, latency_details,header_buffer
    def get_curl_timing_information(self,curl, latency, pool_stablishment=False):
        # Get timing information
        namelookup_time = HOSTNAME_PLACEHOLDER(curl.NAMELOOKUP_TIME)
        connect_time = HOSTNAME_PLACEHOLDER(curl.CONNECT_TIME)
        appconnect_time = HOSTNAME_PLACEHOLDER(curl.APPCONNECT_TIME)
        pretransfer_time = HOSTNAME_PLACEHOLDER(curl.PRETRANSFER_TIME)
        starttransfer_time = HOSTNAME_PLACEHOLDER(curl.STARTTRANSFER_TIME)
        total_time = HOSTNAME_PLACEHOLDER(curl.TOTAL_TIME)
        # Calculate specific timings. If connect_time = 0, TCP and SSL handshake set to 0
        dns_time = namelookup_time
        tcp_handshake_time = max(connect_time - namelookup_time, 0)
        ssl_handshake_time = max(appconnect_time - connect_time, 0 )
        server_processing_time = starttransfer_time - pretransfer_time
        content_transfer_time = total_time - starttransfer_time
        total_time_sumatorio = dns_time + tcp_handshake_time + ssl_handshake_time + server_processing_time + content_transfer_time

        # Print results
        if not pool_stablishment:
            print(" ··········· Latency Hops ···········")
            print(f" · DNS Lookup: {dns_time:.6f} seconds")
            print(f" · TCP Handshake: {tcp_handshake_time:.6f} seconds")
            print(f" · SSL Handshake: {ssl_handshake_time:.6f} seconds")
            print(f" · Server Processing (Transfer Start): {server_processing_time:.6f} seconds")
            print(f" · Content Transfer: {content_transfer_time:.6f} seconds")
            print(f" ·· (1) Total Time Var: {total_time:.6f} seconds")
            print(f" ·· (2) Manual latency time: {latency:.6f} seconds")
            print("·····································")

        latency_details = {
            'DNS_Lookup': f"{dns_time:.6f}",
            'TCP_Handshake': f"{tcp_handshake_time:.6f}",
            'SSL_Handshake': f"{ssl_handshake_time:.6f}",
            'Server_Processing': f"{server_processing_time:.6f}",
            'Content_Transfer': f"{content_transfer_time:.6f}",
            'Total_Time': f"{total_time:.6f}"
        }
        return latency_details
    #Code for latenecy dashboard end
class OpenGW:

    __slots__ = [
        'SOURCE_NAME_PLACEHOLDER',
        'url',
        'headers',
        'auth_endpoint',
        'token_endpoint',
        'kyc_endpoint',
        'kyc_endpoint_0_2_1',
        'consents_endpoint',
        'check_sim_swap_endpoint',
        'check_sim_swap_endpoint_v1',
        'sim_swap_retrieve_date_endpoint',
        'sim_swap_retrieve_date_endpoint_v1',
        'number_verification_endpoint',
        'number_verification_verify_endpoint',
        'resolve_network_id_endpoint',
        'telco_finder_search_endpoint',
        'get_telco_id_endpoint',
        'get_telco_routing_endpoint',
        'get_qos_profile_endpoint',
        'qod_qos_sessions_endpoint',
        'verify_location_endpoint',
        'verify_device_status',
        'send_sms_endpoint'
    ]

    def __init__(self, SOURCE_NAME_PLACEHOLDER: SOURCE_NAME_PLACEHOLDER):
        self.SOURCE_NAME_PLACEHOLDER = SOURCE_NAME_PLACEHOLDER
        self.auth_endpoint = '/bc-authorize'
        self.token_endpoint = '/token'
        self.kyc_endpoint = 'LOCAL_PATH_PLACEHOLDER'
        self.kyc_endpoint_0_2_1 = 'LOCAL_PATH_PLACEHOLDER'
        self.consents_endpoint = 'LOCAL_PATH_PLACEHOLDER'
        self.check_sim_swap_endpoint = 'LOCAL_PATH_PLACEHOLDER'
        self.check_sim_swap_endpoint_v1 = 'LOCAL_PATH_PLACEHOLDER'
        self.sim_swap_retrieve_date_endpoint = 'LOCAL_PATH_PLACEHOLDER'
        self.sim_swap_retrieve_date_endpoint_v1 = 'LOCAL_PATH_PLACEHOLDER'
        self.number_verification_endpoint = 'LOCAL_PATH_PLACEHOLDER'
        #self.number_verification_verify_endpoint = 'LOCAL_PATH_PLACEHOLDER'
        self.number_verification_verify_endpoint = 'LOCAL_PATH_PLACEHOLDER'
        self.resolve_network_id_endpoint = 'LOCAL_PATH_PLACEHOLDER'
        self.telco_finder_search_endpoint = 'LOCAL_PATH_PLACEHOLDER'
        self.get_telco_id_endpoint = 'LOCAL_PATH_PLACEHOLDER'
        self.get_telco_routing_endpoint = 'LOCAL_PATH_PLACEHOLDER'
        self.get_qos_profile_endpoint = 'LOCAL_PATH_PLACEHOLDER'
        self.qod_qos_sessions_endpoint = 'LOCAL_PATH_PLACEHOLDER'
        self.verify_location_endpoint = 'LOCAL_PATH_PLACEHOLDER'
        self.verify_device_status = 'LOCAL_PATH_PLACEHOLDER'
        self.send_sms_endpoint = 'LOCAL_PATH_PLACEHOLDER'

    def generate_auth_request_id(self, payload: Dict, parameters: Dict = None,with_curl=False,dashboard_dict=None,curl_obj=None,jwt=False,app='automation-testing') -> Any:
        gme=False
        if jwt :
            encodded_jwt = SOURCE_NAME_PLACEHOLDER. gen_jwt_token(jwt,app)
            payload['client_assertion']=encodded_jwt
            payload['client_assertion_type']= 'urn:ietf:params:oauth:client-assertiontype:jwt-bearer'
            # Fix the login_hint prefix
            payload["login_hint"] = payload["login_hint"].replace("phone_number:", "tel:")
            gme=True
            HOSTNAME_PLACEHOLDER(f"the payload {payload} in jwt if in generate_auth_request")
        if with_curl:
            #HOSTNAME_PLACEHOLDER(f"Entered curl")
            try:
                response_buffer = io.BytesIO()
                header_buffer = io.BytesIO()
                response_buffer,latency_auth, status_code, latency_auth_details,header_buffer = self.SOURCE_NAME_PLACEHOLDER.do_post_curl(self.auth_endpoint,payload, parameters,response_buffer,header_buffer,curl_obj,gme)
                response_body = response_buffer.getvalue().decode('utf-8')
                raw_headers = header_buffer.getvalue().decode('iso-8859-1')
                header_lines = raw_headers.split('\r\n')
                response_headers = {}
                HOSTNAME_PLACEHOLDER(f"latency auth details are {latency_auth_details}")
                HOSTNAME_PLACEHOLDER(f"latency auth time is {latency_auth}")
                dashboard_dict["latency_auth_details"]=latency_auth_details
                dashboard_dict["latency_auth"]=str(latency_auth)
                dashboard_dict["status_code_auth"]=status_code

                for line in header_lines:
                    if ": " in line:
                        key, value = HOSTNAME_PLACEHOLDER(": ", 1)
                        response_headers[HOSTNAME_PLACEHOLDER()] = HOSTNAME_PLACEHOLDER()
                response_json = HOSTNAME_PLACEHOLDER(response_body)
                return True,response_json,status_code
            except Exception as ex:
                HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex}")
                return False, {}, 1000

            finally:
                pass
        try:
            response=None
            response = self.SOURCE_NAME_PLACEHOLDER.do_post(self.auth_endpoint, payload, parameters,gme_headers=gme)
            json_resp = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER("Post operation response is %s",{response})
            HOSTNAME_PLACEHOLDER(f"The url is: {HOSTNAME_PLACEHOLDER()}")
            HOSTNAME_PLACEHOLDER(f"The header is: {HOSTNAME_PLACEHOLDER}")
            if response.status_code == 200:
                HOSTNAME_PLACEHOLDER(f"Post operation is successful: {response.status_code}")
                return True, json_resp, response.status_code
            else:
                HOSTNAME_PLACEHOLDER(f"Post operation failed: {response.status_code} - {json_resp})")
                return False, json_resp, response.status_code
        except Exception as ex:
            if response:

               HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex} (or) Failed with HTTP status code: {response.status_code}")
               return False, None, response.status_code
            else:
               HOSTNAME_PLACEHOLDER(f"Exception occurred:{ex}")
               return False,None,0

    def generate_token(self, payload: Dict, parameters: Dict = None,with_curl=False,dashboard_dict=None,curl_obj=None,jwt=False,app='automation-testing') -> Tuple:
        gme=False
        if jwt :
            encodded_jwt = SOURCE_NAME_PLACEHOLDER. gen_jwt_token(jwt,app)
            payload['client_assertion']=encodded_jwt
            payload['client_assertion_type']= 'urn:ietf:params:oauth:client-assertiontype:jwt-bearer'
            # Fix the login_hint prefix
            #payload["login_hint"] = payload["login_hint"].replace("phone_number:", "tel:")
            gme=True
        if with_curl:
            try:
                response_buffer = io.BytesIO()
                header_buffer = io.BytesIO()
                response_buffer,latency_token, status_code, latency_token_details,header_buffer = self.SOURCE_NAME_PLACEHOLDER.do_post_curl(self.token_endpoint,payload, parameters,response_buffer,header_buffer,curl_obj,gme)
                response_body = response_buffer.getvalue().decode('utf-8')
                raw_headers = header_buffer.getvalue().decode('iso-8859-1')
                header_lines = raw_headers.split('\r\n')
                response_headers = {}
                HOSTNAME_PLACEHOLDER(f"latency token details are {latency_token_details}")
                HOSTNAME_PLACEHOLDER(f"latency token time is {latency_token}")
                dashboard_dict["latency_token_details"]=latency_token_details
                dashboard_dict["latency_token"]=str(latency_token)
                dashboard_dict["status_code_token"]=status_code
                for line in header_lines:
                    if ": " in line:
                        key, value = HOSTNAME_PLACEHOLDER(": ", 1)
                        response_headers[HOSTNAME_PLACEHOLDER()] = HOSTNAME_PLACEHOLDER()
                response_json = HOSTNAME_PLACEHOLDER(response_body)
                return True,response_json,status_code
            except Exception as ex:
                HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex}")
                return False, {}, 1000

            finally:
                pass
        try:
            response = self.SOURCE_NAME_PLACEHOLDER.do_post(self.token_endpoint, payload, parameters,gme_headers=gme)
            json_resp = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER("Post operation response is %s",{response})
            HOSTNAME_PLACEHOLDER(f"The url is: {HOSTNAME_PLACEHOLDER()}")
            HOSTNAME_PLACEHOLDER(f"The header is: {HOSTNAME_PLACEHOLDER}")
            if response.status_code == 200:
                HOSTNAME_PLACEHOLDER(f"Post operation is successful: {response.status_code}")
                return True, json_resp, response.status_code
            else:
                HOSTNAME_PLACEHOLDER(f"Post operation failed: {response.status_code} - {json_resp})")
                return False, json_resp, response.status_code
        except Exception as ex:
            HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex} (or) Failed with HTTP status code: {response.status_code}")
            return False, None, response.status_code


    def perform_kyc_match(self, url: str, payload: Dict, headers: Dict = None, \
                          parameters: Dict = None,version=None,with_curl=False,dashboard_dict=None,curl_obj=None) -> Tuple:
        if with_curl:
            try:
                default_url = self.SOURCE_NAME_PLACEHOLDER.app_url
                self.SOURCE_NAME_PLACEHOLDER.app_url = url
                default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
                self.SOURCE_NAME_PLACEHOLDER.headers = headers
                endpoint = self.kyc_endpoint  if version is None  else self.kyc_endpoint_0_2_1
                response_buffer = io.BytesIO()
                header_buffer = io.BytesIO()
                response_buffer,latency_total_time, status_code, latency_details,header_buffer = self.SOURCE_NAME_PLACEHOLDER.do_post_curl(endpoint, HOSTNAME_PLACEHOLDER(payload), parameters,response_buffer,header_buffer,curl_obj)
                response_body = response_buffer.getvalue().decode('utf-8')
                raw_headers = header_buffer.getvalue().decode('iso-8859-1')
                header_lines = raw_headers.split('\r\n')
                response_headers = {}
                HOSTNAME_PLACEHOLDER(f"latency details are {latency_details}")
                HOSTNAME_PLACEHOLDER(f"latency time s {latency_total_time}")
                dashboard_dict["latency_api_details"]=latency_details
                dashboard_dict["latency_api"]=str(latency_total_time)
                dashboard_dict["status_code_api"]=status_code

                for line in header_lines:
                    if ": " in line:
                        key, value = HOSTNAME_PLACEHOLDER(": ", 1)
                        response_headers[HOSTNAME_PLACEHOLDER()] = HOSTNAME_PLACEHOLDER()
                response_json = HOSTNAME_PLACEHOLDER(response_body)
                return True, response_json, status_code,response_headers,100
            except Exception as ex:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex}")
                return False, {}, 1000,{},100

            finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url
        try:
            default_url = self.SOURCE_NAME_PLACEHOLDER.app_url
            self.SOURCE_NAME_PLACEHOLDER.app_url = url
            default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
            self.SOURCE_NAME_PLACEHOLDER.headers = headers
            endpoint = self.kyc_endpoint  if version is None  else self.kyc_endpoint_0_2_1
            response = self.SOURCE_NAME_PLACEHOLDER.do_post(endpoint, HOSTNAME_PLACEHOLDER(payload), parameters)
            json_resp = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(f"Post operation response is {response}", )
            HOSTNAME_PLACEHOLDER(f"The url is: {HOSTNAME_PLACEHOLDER()}")
            HOSTNAME_PLACEHOLDER(f"The header is: {HOSTNAME_PLACEHOLDER}")
            self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
            self.SOURCE_NAME_PLACEHOLDER.app_url = default_url
            if response.status_code == 200:
                HOSTNAME_PLACEHOLDER(f"Post operation is successful: {response.status_code}")
                return True, json_resp, response.status_code,HOSTNAME_PLACEHOLDER,HOSTNAME_PLACEHOLDER.total_seconds()
            else:
                HOSTNAME_PLACEHOLDER(f"Post operation failed: {response.status_code} - {json_resp})")
                return False, json_resp, response.status_code,HOSTNAME_PLACEHOLDER,HOSTNAME_PLACEHOLDER.total_seconds()
        except Exception as ex:
            HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex} (or) Failed with HTTP status code: {response.status_code}")
            return False, None, response.status_code,HOSTNAME_PLACEHOLDER,HOSTNAME_PLACEHOLDER.total_seconds()
        finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url

    def verify_user_consents(self, app_url, headers: Dict = None, parameters: Dict = None) -> Tuple:
        try:
            default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
            self.SOURCE_NAME_PLACEHOLDER.app_url = app_url
            self.SOURCE_NAME_PLACEHOLDER.headers = headers
            response = self.SOURCE_NAME_PLACEHOLDER.do_get(self.consents_endpoint, parameters)
            json_resp = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(f"Get operation response is {response}", )
            HOSTNAME_PLACEHOLDER(f"The url is: {HOSTNAME_PLACEHOLDER()}")
            HOSTNAME_PLACEHOLDER(f"The header is: {HOSTNAME_PLACEHOLDER}")
            self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
            if response.status_code == 200:
                HOSTNAME_PLACEHOLDER(f"Get operation is successful: {response.status_code}")
                return True, json_resp, response.status_code
            else:
                HOSTNAME_PLACEHOLDER(f"Get operation failed: {response.status_code} - {json_resp})")
                return False, json_resp, response.status_code
        except Exception as ex:
            HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex} (or) Failed with HTTP status code: {response.status_code}")
            return False, None, response.status_code
        finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url

    def perform_sim_swap_check(self, url: str, payload: Dict, headers: Dict = None, \
                               parameters: Dict = None,version=None,with_curl=False,dashboard_dict=None,curl_obj=None) -> Tuple:
        if with_curl:
            try:
                default_url = self.SOURCE_NAME_PLACEHOLDER.app_url
                self.SOURCE_NAME_PLACEHOLDER.app_url = url
                default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
                self.SOURCE_NAME_PLACEHOLDER.headers = headers
                endpoint = self.check_sim_swap_endpoint  if version is None  else self.check_sim_swap_endpoint_v1
                response_buffer = io.BytesIO()
                header_buffer = io.BytesIO()
                response_buffer,latency_total_time, status_code, latency_details,header_buffer = self.SOURCE_NAME_PLACEHOLDER.do_post_curl(endpoint, HOSTNAME_PLACEHOLDER(payload), parameters,response_buffer,header_buffer,curl_obj)
                response_body = response_buffer.getvalue().decode('utf-8')
                raw_headers = header_buffer.getvalue().decode('iso-8859-1')
                header_lines = raw_headers.split('\r\n')
                response_headers = {}
                HOSTNAME_PLACEHOLDER(f"latency details are {latency_details}")
                HOSTNAME_PLACEHOLDER(f"latency time s {latency_total_time}")
                dashboard_dict["latency_api_details"]=latency_details
                dashboard_dict["latency_api"]=str(latency_total_time)
                dashboard_dict["status_code_api"]=status_code

                for line in header_lines:
                    if ": " in line:
                        key, value = HOSTNAME_PLACEHOLDER(": ", 1)
                        response_headers[HOSTNAME_PLACEHOLDER()] = HOSTNAME_PLACEHOLDER()
                response_json = HOSTNAME_PLACEHOLDER(response_body)
                return True, response_json, status_code,100,response_headers
            except Exception as ex:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex}")
                return False, {}, 1000,100,{}

            finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url
        try:
            default_url = self.SOURCE_NAME_PLACEHOLDER.app_url
            self.SOURCE_NAME_PLACEHOLDER.app_url = url
            default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
            self.SOURCE_NAME_PLACEHOLDER.headers = headers
            endpoint = self.check_sim_swap_endpoint  if version is None  else self.check_sim_swap_endpoint_v1
            response = self.SOURCE_NAME_PLACEHOLDER.do_post(endpoint,HOSTNAME_PLACEHOLDER(payload), parameters)
            HOSTNAME_PLACEHOLDER(response)
            json_resp = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(json_resp)
            HOSTNAME_PLACEHOLDER(f"Post operation response is {response}", )
            HOSTNAME_PLACEHOLDER(f"The url is: {HOSTNAME_PLACEHOLDER()}")
            HOSTNAME_PLACEHOLDER(f"The header is: {HOSTNAME_PLACEHOLDER}")
            self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
            self.SOURCE_NAME_PLACEHOLDER.app_url = default_url
            if response.status_code == 200:
                HOSTNAME_PLACEHOLDER(f"Post operation is successful: {response.status_code}")
                return True, json_resp, response.status_code,HOSTNAME_PLACEHOLDER.total_seconds(),HOSTNAME_PLACEHOLDER
            else:
                HOSTNAME_PLACEHOLDER(f"Post operation failed: {response.status_code} - {json_resp})")
                return False, json_resp, response.status_code,HOSTNAME_PLACEHOLDER.total_seconds(),HOSTNAME_PLACEHOLDER
        except Exception as ex:
            HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex}")
            return False, None, 1000,1000,{}
        finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url

    def retrieve_sim_swap_date(self, url: str, payload: Dict, headers: Dict = None, \
                               parameters: Dict = None,version=None,with_curl=False,dashboard_dict=None,curl_obj=None) -> Tuple:
        if with_curl:
            try:
                default_url = self.SOURCE_NAME_PLACEHOLDER.app_url
                self.SOURCE_NAME_PLACEHOLDER.app_url = url
                default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
                self.SOURCE_NAME_PLACEHOLDER.headers = headers
                endpoint = self.sim_swap_retrieve_date_endpoint  if version is None  else self.sim_swap_retrieve_date_endpoint_v1
                response_buffer = io.BytesIO()
                header_buffer = io.BytesIO()
                response_buffer,latency_total_time, status_code, latency_details,header_buffer = self.SOURCE_NAME_PLACEHOLDER.do_post_curl(endpoint, HOSTNAME_PLACEHOLDER(payload), parameters,response_buffer,header_buffer,curl_obj)
                response_body = response_buffer.getvalue().decode('utf-8')
                raw_headers = header_buffer.getvalue().decode('iso-8859-1')
                header_lines = raw_headers.split('\r\n')
                response_headers = {}
                HOSTNAME_PLACEHOLDER(f"latency details are {latency_details}")
                HOSTNAME_PLACEHOLDER(f"latency time s {latency_total_time}")
                dashboard_dict["latency_api_details"]=latency_details
                dashboard_dict["latency_api"]=str(latency_total_time)
                dashboard_dict["status_code_api"]=status_code

                for line in header_lines:
                    if ": " in line:
                        key, value = HOSTNAME_PLACEHOLDER(": ", 1)
                        response_headers[HOSTNAME_PLACEHOLDER()] = HOSTNAME_PLACEHOLDER()
                response_json = HOSTNAME_PLACEHOLDER(response_body)
                return True, response_json, status_code,100,response_headers
            except Exception as ex:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex}")
                return False, {}, 1000,100,{}

            finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url
        try:
            default_url = self.SOURCE_NAME_PLACEHOLDER.app_url
            self.SOURCE_NAME_PLACEHOLDER.app_url = url
            default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
            self.SOURCE_NAME_PLACEHOLDER.headers = headers
            endpoint = self.sim_swap_retrieve_date_endpoint  if version is None  else self.sim_swap_retrieve_date_endpoint_v1
            response = self.SOURCE_NAME_PLACEHOLDER.do_post(endpoint,HOSTNAME_PLACEHOLDER(payload), parameters)
            HOSTNAME_PLACEHOLDER(response)
            json_resp = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(json_resp)
            HOSTNAME_PLACEHOLDER(f"Post operation response is {response}", )
            HOSTNAME_PLACEHOLDER(f"The url is: {HOSTNAME_PLACEHOLDER()}")
            HOSTNAME_PLACEHOLDER(f"The header is: {HOSTNAME_PLACEHOLDER}")
            self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
            self.SOURCE_NAME_PLACEHOLDER.app_url = default_url
            if response.status_code == 200:
                HOSTNAME_PLACEHOLDER(f"Post operation is successful: {response.status_code}")
                return True, json_resp, response.status_code,HOSTNAME_PLACEHOLDER.total_seconds(),HOSTNAME_PLACEHOLDER
            else:
                HOSTNAME_PLACEHOLDER(f"Post operation failed: {response.status_code} - {json_resp})")
                return False, json_resp, response.status_code,HOSTNAME_PLACEHOLDER.total_seconds(),HOSTNAME_PLACEHOLDER
        except Exception as ex:
            HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex}")
            return False, None, 1000,1000,{}
        finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url

    def perform_number_verification(self, url: str,payload: Dict,headers: Dict = None,\
                                    parameters: Dict = None) -> Tuple:
        try:
            default_url = self.SOURCE_NAME_PLACEHOLDER.app_url
            self.SOURCE_NAME_PLACEHOLDER.app_url = url
            default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
            self.SOURCE_NAME_PLACEHOLDER.headers = headers
            response = self.SOURCE_NAME_PLACEHOLDER.do_get(self.number_verification_endpoint, parameters)
            HOSTNAME_PLACEHOLDER(response)
            json_resp = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(json_resp)
            HOSTNAME_PLACEHOLDER(f"Get operation response is {response}", )
            HOSTNAME_PLACEHOLDER(f"The url is: {HOSTNAME_PLACEHOLDER()}")
            HOSTNAME_PLACEHOLDER(f"The header is: {HOSTNAME_PLACEHOLDER}")
            self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
            self.SOURCE_NAME_PLACEHOLDER.app_url = default_url

            if response.status_code == 200:
                HOSTNAME_PLACEHOLDER(f"Get operation is successful: {response.status_code}")
                return True, json_resp, response.status_code
            else:
                HOSTNAME_PLACEHOLDER(f"Get operation failed: {response.status_code} - {json_resp})")
                return False, json_resp, response.status_code
        except Exception as ex:
            HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex} (or) Failed with HTTP status code: {response.status_code}")
            return False, None, response.status_code
        finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url

    def verify_number(self, url: str, payload: Dict, headers: Dict = None, \
                      parameters: Dict = None,with_curl=False,dashboard_dict=None,curl_obj=None) -> Tuple:
        if with_curl:
            try:
                default_url = self.SOURCE_NAME_PLACEHOLDER.app_url
                self.SOURCE_NAME_PLACEHOLDER.app_url = url
                default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
                self.SOURCE_NAME_PLACEHOLDER.headers = headers

                response_buffer = io.BytesIO()
                header_buffer = io.BytesIO()
                response_buffer,latency_total_time, status_code, latency_details,header_buffer = self.SOURCE_NAME_PLACEHOLDER.do_post_curl(self.number_verification_verify_endpoint, HOSTNAME_PLACEHOLDER(payload), parameters,response_buffer,header_buffer,curl_obj)
                response_body = response_buffer.getvalue().decode('utf-8')
                raw_headers = header_buffer.getvalue().decode('iso-8859-1')
                header_lines = raw_headers.split('\r\n')
                response_headers = {}
                HOSTNAME_PLACEHOLDER(f"latency details are {latency_details}")
                HOSTNAME_PLACEHOLDER(f"latency time s {latency_total_time}")
                dashboard_dict["latency_api_details"]=latency_details
                dashboard_dict["latency_api"]=str(latency_total_time)
                dashboard_dict["status_code_api"]=status_code

                for line in header_lines:
                    if ": " in line:
                        key, value = HOSTNAME_PLACEHOLDER(": ", 1)
                        response_headers[HOSTNAME_PLACEHOLDER()] = HOSTNAME_PLACEHOLDER()
                response_json = HOSTNAME_PLACEHOLDER(response_body)
                return True, response_json, status_code,100,response_headers
            except Exception as ex:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex}")
                return False, {}, 1000,100,{}

            finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url
        try:
            default_url = self.SOURCE_NAME_PLACEHOLDER.app_url
            response = None
            self.SOURCE_NAME_PLACEHOLDER.app_url = url
            default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
            self.SOURCE_NAME_PLACEHOLDER.headers = headers
            response = self.SOURCE_NAME_PLACEHOLDER.do_post(self.number_verification_verify_endpoint, \
                                              HOSTNAME_PLACEHOLDER(payload), parameters)
            HOSTNAME_PLACEHOLDER(response)
            json_resp = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(json_resp)
            HOSTNAME_PLACEHOLDER(f"Post operation response is {response}",)
            HOSTNAME_PLACEHOLDER(f"The url is: {HOSTNAME_PLACEHOLDER()}")
            HOSTNAME_PLACEHOLDER(f"The header is: {HOSTNAME_PLACEHOLDER}")
            self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
            self.SOURCE_NAME_PLACEHOLDER.app_url = default_url
            if response.status_code == 200:
                HOSTNAME_PLACEHOLDER(f"Post operation is successful: {response.status_code}")
                return True, json_resp, response.status_code
            else:
                HOSTNAME_PLACEHOLDER(f"Post operation failed: {response.status_code} - {json_resp})")
                return False, json_resp, response.status_code
        except Exception as ex:
            if response:
                HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex} (or) Failed with HTTP status code: {response.status_code}")
            else:
                HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex}")
                return False,None,0
            return False, None, response.status_code
        finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url

    def check_number_id(self, url: str, payload: Dict, headers: Dict = None, \
                        parameters: Dict = None,with_curl=False,dashboard_dict=None,curl_obj=None) -> Tuple:
        if with_curl:
            try:
                default_url = self.SOURCE_NAME_PLACEHOLDER.app_url
                self.SOURCE_NAME_PLACEHOLDER.app_url = url
                default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
                self.SOURCE_NAME_PLACEHOLDER.headers = headers
                response_buffer = io.BytesIO()
                header_buffer = io.BytesIO()
                response_buffer,latency_total_time, status_code, latency_details,header_buffer = self.SOURCE_NAME_PLACEHOLDER.do_post_curl(self.resolve_network_id_endpoint, HOSTNAME_PLACEHOLDER(payload), parameters,response_buffer,header_buffer,curl_obj)
                response_body = response_buffer.getvalue().decode('utf-8')
                raw_headers = header_buffer.getvalue().decode('iso-8859-1')
                header_lines = raw_headers.split('\r\n')
                response_headers = {}
                HOSTNAME_PLACEHOLDER(f"latency details are {latency_details}")
                HOSTNAME_PLACEHOLDER(f"latency time s {latency_total_time}")
                dashboard_dict["latency_api_details"]=latency_details
                dashboard_dict["latency_api"]=str(latency_total_time)
                dashboard_dict["status_code_api"]=status_code

                for line in header_lines:
                    if ": " in line:
                        key, value = HOSTNAME_PLACEHOLDER(": ", 1)
                        response_headers[HOSTNAME_PLACEHOLDER()] = HOSTNAME_PLACEHOLDER()
                response_json = HOSTNAME_PLACEHOLDER(response_body)
                return True, response_json, status_code,100,response_headers
            except Exception as ex:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex}")
                return False, {}, 1000,100,{}

            finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url
        try:
            default_url = self.SOURCE_NAME_PLACEHOLDER.app_url
            self.SOURCE_NAME_PLACEHOLDER.app_url = url
            default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
            self.SOURCE_NAME_PLACEHOLDER.headers = headers
            response = self.SOURCE_NAME_PLACEHOLDER.do_post(self.resolve_network_id_endpoint,\
                                              HOSTNAME_PLACEHOLDER(payload), parameters)
            HOSTNAME_PLACEHOLDER(response)
            json_resp = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(json_resp)
            HOSTNAME_PLACEHOLDER(f"Post operation response is {response}", )
            HOSTNAME_PLACEHOLDER(f"The url is: {HOSTNAME_PLACEHOLDER()}")
            HOSTNAME_PLACEHOLDER(f"The header is: {HOSTNAME_PLACEHOLDER}")
            self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
            HOSTNAME_PLACEHOLDER(2)
            self.SOURCE_NAME_PLACEHOLDER.app_url = default_url
            if response.status_code == 200:
                HOSTNAME_PLACEHOLDER(f"Post operation is successful: {response.status_code}")
                return True, json_resp, response.status_code
            else:
                HOSTNAME_PLACEHOLDER(f"Post operation failed: {response.status_code} - {json_resp})")
                return False, json_resp, response.status_code
        except Exception as ex:
            HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex} (or) Failed with HTTP status code: {response.status_code}")
            return False, None, response.status_code
        finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url

    def search_telco_finder(self, url: str, payload: Dict, headers: Dict = None,\
                            parameters: Dict = None,with_curl=False,dashboard_dict=None,curl_obj=None) -> Tuple:
        if with_curl:
            try:
                default_url = self.SOURCE_NAME_PLACEHOLDER.app_url
                self.SOURCE_NAME_PLACEHOLDER.app_url = url
                default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
                self.SOURCE_NAME_PLACEHOLDER.headers = headers
                response_buffer = io.BytesIO()
                header_buffer = io.BytesIO()
                response_buffer,latency_total_time, status_code, latency_details,header_buffer = self.SOURCE_NAME_PLACEHOLDER.do_post_curl(self.telco_finder_search_endpoint, HOSTNAME_PLACEHOLDER(payload), parameters,response_buffer,header_buffer,curl_obj)
                response_body = response_buffer.getvalue().decode('utf-8')
                raw_headers = header_buffer.getvalue().decode('iso-8859-1')
                header_lines = raw_headers.split('\r\n')
                response_headers = {}
                HOSTNAME_PLACEHOLDER(f"latency details are {latency_details}")
                HOSTNAME_PLACEHOLDER(f"latency time s {latency_total_time}")
                dashboard_dict["latency_api_details"]=latency_details
                dashboard_dict["latency_api"]=str(latency_total_time)
                dashboard_dict["status_code_api"]=status_code

                for line in header_lines:
                    if ": " in line:
                        key, value = HOSTNAME_PLACEHOLDER(": ", 1)
                        response_headers[HOSTNAME_PLACEHOLDER()] = HOSTNAME_PLACEHOLDER()
                response_json = HOSTNAME_PLACEHOLDER(response_body)
                return True, response_json, status_code,100,response_headers
            except Exception as ex:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex}")
                return False, {}, 1000,100,{}

            finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url

        try:
            default_url = self.SOURCE_NAME_PLACEHOLDER.app_url
            self.SOURCE_NAME_PLACEHOLDER.app_url = url
            default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
            self.SOURCE_NAME_PLACEHOLDER.headers = headers
            # response = None
            response = self.SOURCE_NAME_PLACEHOLDER.do_post(self.telco_finder_search_endpoint, \
                                              HOSTNAME_PLACEHOLDER(payload), parameters)
            HOSTNAME_PLACEHOLDER(response)
            json_resp = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(json_resp)
            HOSTNAME_PLACEHOLDER(f"Post operation response is {response}", )
            HOSTNAME_PLACEHOLDER(f"The url is: {HOSTNAME_PLACEHOLDER()}")
            HOSTNAME_PLACEHOLDER(f"The header is: {HOSTNAME_PLACEHOLDER}")
            self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
            self.SOURCE_NAME_PLACEHOLDER.app_url = default_url
            HOSTNAME_PLACEHOLDER(2)
            if response.status_code == 200:
                HOSTNAME_PLACEHOLDER(f"Post operation is successful: {response.status_code}")
                return True, json_resp, response.status_code
            else:
                HOSTNAME_PLACEHOLDER(f"Post operation failed: {response.status_code} - {json_resp})")
                return False, json_resp, response.status_code
        except Exception as ex:
            HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex} (or) Failed with HTTP status code: {response.status_code}")
            return False, None, response.status_code
        finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url

    def get_telco_id(self, url: str, headers: Dict = None, \
                     parameters: Dict = None) -> Tuple:
        try:
            default_url = self.SOURCE_NAME_PLACEHOLDER.app_url
            self.SOURCE_NAME_PLACEHOLDER.app_url = url
            default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
            self.SOURCE_NAME_PLACEHOLDER.headers = headers
            response = self.SOURCE_NAME_PLACEHOLDER.do_get(self.get_telco_id_endpoint, parameters)
            HOSTNAME_PLACEHOLDER(response)
            json_resp = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(json_resp)
            HOSTNAME_PLACEHOLDER(f"Get operation response is {response}", )
            HOSTNAME_PLACEHOLDER(f"The url is: {HOSTNAME_PLACEHOLDER()}")
            HOSTNAME_PLACEHOLDER(f"The header is: {HOSTNAME_PLACEHOLDER}")
            self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
            self.SOURCE_NAME_PLACEHOLDER.app_url = default_url
            if response.status_code == 200:
                HOSTNAME_PLACEHOLDER(f"Get operation is successful: {response.status_code}")
                return True, json_resp, response.status_code
            else:
                HOSTNAME_PLACEHOLDER(f"Get operation failed: {response.status_code} - {json_resp})")
                return False, json_resp, response.status_code
        except Exception as ex:
            HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex} (or) Failed with HTTP status code: {response.status_code}")
            return False, None, response.status_code
        finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url

    def get_telco_routing(self, url: str, headers: Dict = None,\
                          parameters: Dict = None,with_curl=False,dashboard_dict=None,curl_obj=None) -> Tuple:
        if with_curl:
            try:
                default_url = self.SOURCE_NAME_PLACEHOLDER.app_url
                self.SOURCE_NAME_PLACEHOLDER.app_url = url
                default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
                self.SOURCE_NAME_PLACEHOLDER.headers = headers

                response_buffer = io.BytesIO()
                header_buffer = io.BytesIO()
                response_buffer,latency_total_time, status_code, latency_details,header_buffer = self.SOURCE_NAME_PLACEHOLDER.do_get_curl(self.get_telco_routing_endpoint, parameters,response_buffer,header_buffer,curl_obj)
                response_body = response_buffer.getvalue().decode('utf-8')
                raw_headers = header_buffer.getvalue().decode('iso-8859-1')
                header_lines = raw_headers.split('\r\n')
                response_headers = {}
                HOSTNAME_PLACEHOLDER(f"latency details are {latency_details}")
                HOSTNAME_PLACEHOLDER(f"latency time s {latency_total_time}")
                dashboard_dict["latency_api_details"]=latency_details
                dashboard_dict["latency_api"]=str(latency_total_time)
                dashboard_dict["status_code_api"]=status_code
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                for line in header_lines:
                    if ": " in line:
                        key, value = HOSTNAME_PLACEHOLDER(": ", 1)
                        response_headers[HOSTNAME_PLACEHOLDER()] = HOSTNAME_PLACEHOLDER()
                response_json = HOSTNAME_PLACEHOLDER(response_body)
                return True, response_json, status_code,response_headers,100
            except Exception as ex:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex}")
                return False, {}, 1000,{},100

            finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url
        try:
            default_url = self.SOURCE_NAME_PLACEHOLDER.app_url
            self.SOURCE_NAME_PLACEHOLDER.app_url = url
            default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
            self.SOURCE_NAME_PLACEHOLDER.headers = headers
            response = self.SOURCE_NAME_PLACEHOLDER.do_get(self.get_telco_routing_endpoint, parameters)
            HOSTNAME_PLACEHOLDER(response)
            json_resp = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(json_resp)
            HOSTNAME_PLACEHOLDER(f"Get operation response is {response}", )
            HOSTNAME_PLACEHOLDER(f"The url is: {HOSTNAME_PLACEHOLDER()}")
            HOSTNAME_PLACEHOLDER(f"The header is: {HOSTNAME_PLACEHOLDER}")
            self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
            self.SOURCE_NAME_PLACEHOLDER.app_url = default_url
            if response.status_code == 200:
                HOSTNAME_PLACEHOLDER(f"Get operation is successful: {response.status_code}")
                return True, json_resp, response.status_code
            else:
                HOSTNAME_PLACEHOLDER(f"Get operation failed: {response.status_code} - {json_resp})")
                return False, json_resp, response.status_code
        except Exception as ex:
            HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex} (or) Failed with HTTP status code: {response.status_code}")
            return False, None, response.status_code
        finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url


    def create_qod_qos_session(self, url: str, payload: Dict, headers: Dict = None,\
                            parameters: Dict = None) -> Tuple:
        try:
            default_url = self.SOURCE_NAME_PLACEHOLDER.app_url
            self.SOURCE_NAME_PLACEHOLDER.app_url = url
            default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
            self.SOURCE_NAME_PLACEHOLDER.headers = headers
            # response = None
            response = self.SOURCE_NAME_PLACEHOLDER.do_post(self.qod_qos_sessions_endpoint, \
                                              HOSTNAME_PLACEHOLDER(payload), parameters)
            HOSTNAME_PLACEHOLDER(response)
            json_resp = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(json_resp)
            HOSTNAME_PLACEHOLDER(f"Post operation response is {response}", )
            HOSTNAME_PLACEHOLDER(f"The url is: {HOSTNAME_PLACEHOLDER()}")
            HOSTNAME_PLACEHOLDER(f"The header is: {HOSTNAME_PLACEHOLDER}")
            self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
            self.SOURCE_NAME_PLACEHOLDER.app_url = default_url
            HOSTNAME_PLACEHOLDER(2)
            if response.status_code == 201:
                HOSTNAME_PLACEHOLDER(f"Post operation is successful: {response.status_code}")
                return True, json_resp, response.status_code,HOSTNAME_PLACEHOLDER.total_seconds(),HOSTNAME_PLACEHOLDER
            else:
                HOSTNAME_PLACEHOLDER(f"Post operation failed: {response.status_code} - {json_resp})")
                return False, json_resp, response.status_code,HOSTNAME_PLACEHOLDER.total_seconds(),HOSTNAME_PLACEHOLDER
        except Exception as ex:
            HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex} (or) Failed with HTTP status code: {response.status_code}")
            return False, None, response.status_code,HOSTNAME_PLACEHOLDER.total_seconds(),HOSTNAME_PLACEHOLDER
        finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url

    def extend_the_duration_of_a_qod_qos_session(self, url: str, session_id: str, payload: Dict, headers: Dict = None,\
                            parameters: Dict = None) -> Tuple:
        try:
            default_url = self.SOURCE_NAME_PLACEHOLDER.app_url
            self.SOURCE_NAME_PLACEHOLDER.app_url = url
            default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
            self.SOURCE_NAME_PLACEHOLDER.headers = headers
            # response = None
            response = self.SOURCE_NAME_PLACEHOLDER.do_post(self.qod_qos_sessions_endpoint+"/"+session_id + "/extend/", \
                                              HOSTNAME_PLACEHOLDER(payload), parameters)
            HOSTNAME_PLACEHOLDER(response)
            json_resp = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(json_resp)
            HOSTNAME_PLACEHOLDER(f"Post operation response is {response}", )
            HOSTNAME_PLACEHOLDER(f"The url is: {HOSTNAME_PLACEHOLDER()}")
            HOSTNAME_PLACEHOLDER(f"The header is: {HOSTNAME_PLACEHOLDER}")
            self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
            self.SOURCE_NAME_PLACEHOLDER.app_url = default_url
            HOSTNAME_PLACEHOLDER(2)
            if response.status_code == 200:
                HOSTNAME_PLACEHOLDER(f"Post operation is successful: {response.status_code}")
                return True, json_resp, response.status_code,HOSTNAME_PLACEHOLDER.total_seconds(),HOSTNAME_PLACEHOLDER
            else:
                HOSTNAME_PLACEHOLDER(f"Post operation failed: {response.status_code} - {json_resp})")
                return False, json_resp, response.status_code,HOSTNAME_PLACEHOLDER.total_seconds(),HOSTNAME_PLACEHOLDER
        except Exception as ex:
            HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex} (or) Failed with HTTP status code: {response.status_code}")
            return False, None, response.status_code,HOSTNAME_PLACEHOLDER.total_seconds(),HOSTNAME_PLACEHOLDER
        finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url

    def get_qos_session_information(self, url: str, session_id: str, headers: Dict = None,\
                          parameters: Dict = None) -> Tuple:
        try:
            default_url = self.SOURCE_NAME_PLACEHOLDER.app_url
            self.SOURCE_NAME_PLACEHOLDER.app_url = url
            default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
            self.SOURCE_NAME_PLACEHOLDER.headers = headers
            response = self.SOURCE_NAME_PLACEHOLDER.do_get(self.qod_qos_sessions_endpoint+'/'+session_id, parameters)
            HOSTNAME_PLACEHOLDER(response)
            json_resp = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(json_resp)
            HOSTNAME_PLACEHOLDER(f"Get operation response is {response}", )
            HOSTNAME_PLACEHOLDER(f"The url is: {HOSTNAME_PLACEHOLDER()}")
            HOSTNAME_PLACEHOLDER(f"The header is: {HOSTNAME_PLACEHOLDER}")
            self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
            self.SOURCE_NAME_PLACEHOLDER.app_url = default_url
            if response.status_code == 200:
                HOSTNAME_PLACEHOLDER(f"Get operation is successful: {response.status_code}")
                return True, json_resp, response.status_code,HOSTNAME_PLACEHOLDER.total_seconds(),HOSTNAME_PLACEHOLDER
            else:
                HOSTNAME_PLACEHOLDER(f"Get operation failed: {response.status_code} - {json_resp})")
                return False, json_resp, response.status_code,HOSTNAME_PLACEHOLDER.total_seconds(),HOSTNAME_PLACEHOLDER
        except Exception as ex:
            HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex} (or) Failed with HTTP status code: {response.status_code}")
            return False, None, response.status_code,HOSTNAME_PLACEHOLDER.total_seconds(),HOSTNAME_PLACEHOLDER
        finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url

    def delete_qos_session_using_session_id(self, url: str, session_id: str, headers: Dict = None,\
                          parameters: Dict = None) -> Tuple:
        HOSTNAME_PLACEHOLDER("entered delete qos")
        try:
            default_url = self.SOURCE_NAME_PLACEHOLDER.app_url
            self.SOURCE_NAME_PLACEHOLDER.app_url = url
            default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
            self.SOURCE_NAME_PLACEHOLDER.headers = headers
            response = self.SOURCE_NAME_PLACEHOLDER.do_delete(self.qod_qos_sessions_endpoint+'/'+session_id,parameters)
            HOSTNAME_PLACEHOLDER(response)
            #fix for delete session failure
            if response.status_code!=204:
                json_resp = HOSTNAME_PLACEHOLDER()
                HOSTNAME_PLACEHOLDER(json_resp)
            HOSTNAME_PLACEHOLDER(f"Delete operation response is {response}", )
            HOSTNAME_PLACEHOLDER(f"The url is: {HOSTNAME_PLACEHOLDER()}")
            HOSTNAME_PLACEHOLDER(f"The header is: {HOSTNAME_PLACEHOLDER}")
            self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
            self.SOURCE_NAME_PLACEHOLDER.app_url = default_url
            if response.status_code == 204:
                HOSTNAME_PLACEHOLDER(f"Delete operation is successful: {response.status_code}")
                return True, {}, response.status_code,HOSTNAME_PLACEHOLDER.total_seconds(),HOSTNAME_PLACEHOLDER
            else:
                HOSTNAME_PLACEHOLDER(f"Delete operation failed: {response.status_code} - {json_resp})")
                return False, json_resp, response.status_code,HOSTNAME_PLACEHOLDER.total_seconds(),HOSTNAME_PLACEHOLDER
        except Exception as ex:
            HOSTNAME_PLACEHOLDER(f"Exception occured {ex}")
            #HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex} (or) Failed with HTTP status code: {response.status_code}")
            return False, None, 1000,100,{}
        finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url

    def get_qos_profile(self, url: str, session_name: str, headers: Dict = None,\
                          parameters: Dict = None) -> Tuple:
        HOSTNAME_PLACEHOLDER(f"parameters are {parameters}")
        try:
            default_url = self.SOURCE_NAME_PLACEHOLDER.app_url
            self.SOURCE_NAME_PLACEHOLDER.app_url = url
            default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
            self.SOURCE_NAME_PLACEHOLDER.headers = headers
            start_time = time.perf_counter()
            if session_name is None:
                response = self.SOURCE_NAME_PLACEHOLDER.do_get(self.get_qos_profile_endpoint, parameters)
            else:
                response = self.SOURCE_NAME_PLACEHOLDER.do_get(self.get_qos_profile_endpoint + '/' + session_name, parameters)
            end_time = time.perf_counter()

            total_time = end_time - start_time

            HOSTNAME_PLACEHOLDER(f"High Precision Request Time: {total_time:.6f} seconds")
            HOSTNAME_PLACEHOLDER(response)
            json_resp = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(json_resp)
            HOSTNAME_PLACEHOLDER(f"Get operation response is {response}", )
            HOSTNAME_PLACEHOLDER(f"The url is: {HOSTNAME_PLACEHOLDER()}")
            HOSTNAME_PLACEHOLDER(f"The header is: {HOSTNAME_PLACEHOLDER}")
            self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
            self.SOURCE_NAME_PLACEHOLDER.app_url = default_url
            if response.status_code == 200:
                HOSTNAME_PLACEHOLDER(f"Get operation is successful: {response.status_code}")
                return True, json_resp, response.status_code,HOSTNAME_PLACEHOLDER.total_seconds(),HOSTNAME_PLACEHOLDER
            else:
                HOSTNAME_PLACEHOLDER(f"Get operation failed: {response.status_code} - {json_resp})")
                return False, json_resp, response.status_code,HOSTNAME_PLACEHOLDER.total_seconds(),HOSTNAME_PLACEHOLDER
        except Exception as ex:
            HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex} (or) Failed with HTTP status code: {response.status_code}")
            return False, None, response.status_code,HOSTNAME_PLACEHOLDER.total_seconds(),HOSTNAME_PLACEHOLDER
        finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url



    def verify_location(self,url: str,payload: Dict,headers: Dict=None,parameters: Dict=None)-> Tuple:
        try:
            default_url = self.SOURCE_NAME_PLACEHOLDER.app_url
            self.SOURCE_NAME_PLACEHOLDER.app_url = url
            default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
            self.SOURCE_NAME_PLACEHOLDER.headers = headers
            start_time = time.perf_counter()
            response = self.SOURCE_NAME_PLACEHOLDER.do_post(self.verify_location_endpoint, \
                                              HOSTNAME_PLACEHOLDER(payload), parameters)
            HOSTNAME_PLACEHOLDER(response)
            json_resp = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(json_resp)
            HOSTNAME_PLACEHOLDER(f"Post operation response is {response}", )
            HOSTNAME_PLACEHOLDER(f"The url is: {HOSTNAME_PLACEHOLDER()}")
            HOSTNAME_PLACEHOLDER(f"The header is: {HOSTNAME_PLACEHOLDER}")
            self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
            self.SOURCE_NAME_PLACEHOLDER.app_url = default_url
            HOSTNAME_PLACEHOLDER(2)
            if response.status_code == 200:
                HOSTNAME_PLACEHOLDER(f"Post operation is successful: {response.status_code}")
                return True, json_resp, response.status_code,HOSTNAME_PLACEHOLDER,HOSTNAME_PLACEHOLDER.total_seconds()
            else:
                HOSTNAME_PLACEHOLDER(f"Post operation failed: {response.status_code} - {json_resp})")
                return False, json_resp, response.status_code,HOSTNAME_PLACEHOLDER,HOSTNAME_PLACEHOLDER.total_seconds()
        except Exception as ex:
            HOSTNAME_PLACEHOLDER(f"Exception occurred: {ex}")
            return False, None, 1000,{},100
        finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url

    def device_connectivity(self,url: str,payload, headers: Dict=None,parameters: Dict=None)-> Tuple:
        try:
            default_url = self.SOURCE_NAME_PLACEHOLDER.app_url
            self.SOURCE_NAME_PLACEHOLDER.app_url = url
            default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
            self.SOURCE_NAME_PLACEHOLDER.headers = headers
            start_time = time.perf_counter()
            HOSTNAME_PLACEHOLDER(f'_____________________>>>>{payload}  and type{type(payload)}')
            if HOSTNAME_PLACEHOLDER('device', {}).get('missing_request') == 'True':
                HOSTNAME_PLACEHOLDER(f'in side the IF with no data in payload')
                response= self.SOURCE_NAME_PLACEHOLDER.do_post_no_data(self.verify_device_status, parameters)


            else:
                HOSTNAME_PLACEHOLDER(f'in side the ELSE with payload data in payload')
                response = self.SOURCE_NAME_PLACEHOLDER.do_post(self.verify_device_status, \
                                                HOSTNAME_PLACEHOLDER(payload), parameters)




            HOSTNAME_PLACEHOLDER(response)
            json_resp = HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(json_resp)
            HOSTNAME_PLACEHOLDER(f"Post operation response is {response}", )
            HOSTNAME_PLACEHOLDER(f"The url is: {HOSTNAME_PLACEHOLDER()}")
            HOSTNAME_PLACEHOLDER(f"The header is: {HOSTNAME_PLACEHOLDER}")
            HOSTNAME_PLACEHOLDER(f"The payload is: {payload}")

            self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
            self.SOURCE_NAME_PLACEHOLDER.app_url = default_url
            HOSTNAME_PLACEHOLDER(2)
            if response.status_code == 201:
                HOSTNAME_PLACEHOLDER(f"Post operation is successful: {response.status_code}")
                return True, json_resp, response.status_code,HOSTNAME_PLACEHOLDER.total_seconds(),HOSTNAME_PLACEHOLDER
            else:
                HOSTNAME_PLACEHOLDER(f"Post operation failed: {response.status_code} - {json_resp})")
                return False, json_resp, response.status_code,HOSTNAME_PLACEHOLDER.total_seconds(),HOSTNAME_PLACEHOLDER
        except Exception as ex:
            HOSTNAME_PLACEHOLDER(f"Exception occurred:{ex} ")
            return False, None, 1000,100,{}
        finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url
    def send_sms(self,url: str,payload, headers: Dict=None,parameters: Dict=None)-> Tuple:
        try:
            default_url = self.SOURCE_NAME_PLACEHOLDER.app_url
            self.SOURCE_NAME_PLACEHOLDER.app_url = url
            default_headers = self.SOURCE_NAME_PLACEHOLDER.headers
            self.SOURCE_NAME_PLACEHOLDER.headers = headers
            start_time = time.perf_counter()
            HOSTNAME_PLACEHOLDER(f'_____________________>>>>{payload}  and type{type(payload)}')
            if HOSTNAME_PLACEHOLDER('missing_request') == 'True':
                HOSTNAME_PLACEHOLDER(f'in side the IF with no data in payload')
                response= self.SOURCE_NAME_PLACEHOLDER.do_post_no_data(self.send_sms_endpoint, parameters)


            else:
                HOSTNAME_PLACEHOLDER(f'in side the ELSE with payload data in payload')
                response = self.SOURCE_NAME_PLACEHOLDER.do_post(self.send_sms_endpoint, \
                                                HOSTNAME_PLACEHOLDER(payload), parameters)




            HOSTNAME_PLACEHOLDER(response)
            HOSTNAME_PLACEHOLDER(f"raw response text is {HOSTNAME_PLACEHOLDER} end {len(HOSTNAME_PLACEHOLDER)}")
            if HOSTNAME_PLACEHOLDER():  # Checks for non-empty response body
                try:
                    json_resp = HOSTNAME_PLACEHOLDER()
                    HOSTNAME_PLACEHOLDER(json_resp)
                except ValueError as e:
                    print("Failed to parse JSON:", e)
                    print("Response content:", HOSTNAME_PLACEHOLDER)
                    json_resp=HOSTNAME_PLACEHOLDER
            else:
                json_resp={}
                print("Empty response body (200 OK)")
            HOSTNAME_PLACEHOLDER(f"Post operation response is {response}", )
            HOSTNAME_PLACEHOLDER(f"The url is: {HOSTNAME_PLACEHOLDER()}")
            HOSTNAME_PLACEHOLDER(f"The header is: {HOSTNAME_PLACEHOLDER}")
            HOSTNAME_PLACEHOLDER(f"The payload is: {payload}")

            self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
            self.SOURCE_NAME_PLACEHOLDER.app_url = default_url
            HOSTNAME_PLACEHOLDER(2)
            if response.status_code == 200:
                HOSTNAME_PLACEHOLDER(f"Post operation is successful: {response.status_code}")
                return True, json_resp, response.status_code,HOSTNAME_PLACEHOLDER.total_seconds(),HOSTNAME_PLACEHOLDER
            else:
                HOSTNAME_PLACEHOLDER(f"Post operation failed: {response.status_code} - {json_resp})")
                return False, json_resp, response.status_code,HOSTNAME_PLACEHOLDER.total_seconds(),HOSTNAME_PLACEHOLDER
        except Exception as ex:
            HOSTNAME_PLACEHOLDER(f"Exception occurred:{ex} ")
            return False, None, 1000,100,{}
        finally:
                self.SOURCE_NAME_PLACEHOLDER.headers = default_headers
                self.SOURCE_NAME_PLACEHOLDER.app_url = default_url
