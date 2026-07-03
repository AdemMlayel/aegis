
*** Settings ***
# Config files
Variables    ..LOCAL_PATH_PLACEHOLDER
Variables    ..LOCAL_PATH_PLACEHOLDER
Variables    ..LOCAL_PATH_PLACEHOLDER

# Resource files
Resource     ..LOCAL_PATH_PLACEHOLDER
Resource     ..LOCAL_PATH_PLACEHOLDER
Resource    SOURCE_NAME_PLACEHOLDER.robot

# Python libraries
Library      Collections
Library      DateTime
Library      ..LOCAL_PATH_PLACEHOLDER
Library      ..LOCAL_PATH_PLACEHOLDER
Library      ..LOCAL_PATH_PLACEHOLDER
Library      ..LOCAL_PATH_PLACEHOLDER    ${nosqldatabase}    ${testdb}
Library      ..LOCAL_PATH_PLACEHOLDER  ${ANRITSU}
Library      ..LOCAL_PATH_PLACEHOLDER
Library    ..LOCAL_PATH_PLACEHOLDER
*** Variables ***
#${pcap_file_path}    ../VoLTE Call From A(Munich) to B(Hamburg)
${pcap_file_path}    ../mVoLTE_Munich_to_mVoLTE_Munich_Android_to_Android.pcapng

*** Test Cases ***
Basic_VoLTE:_A_and_B_VoLTE,_A_releases._A_dials_national_format
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER:_A_and_B_VoLTE,_A_releases._A_dials_national_format" --test "Basic_VoLTE:_A_and_B_VoLTE,_A_releases._A_dials_national_format" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    Validates VoLTE call from Device A to Device B using DB data and Anritsu traces
    [Tags]     SEG_VoLTE004    TMSII01060116

    ${id}              Set Variable    ${vims_tcs}[Basic_VoLTE:_A_and_B_VoLTE,_A_releases._A_dials_national_format][${sites}]
    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_obj}    get_testcase_info
    ${ims_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_obj}    get_trace_inputs

    # # 1. Verify Sim card
    # ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    # ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    # Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    # Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_1]    Notional_format=${True}
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

    # 4. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]    ${devices_info}[device_2]
    Should Be True    ${start_oesearch}
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}


Registration:VoLTE_User_registration_Android_Hamburg
    # robot --outputdir "..LOCAL_PATH_PLACEHOLDER:VoLTE_User_registration_Android_Hamburg" --test "Registration:VoLTE_User_registration_Android_Hamburg" SOURCE_NAME_PLACEHOLDER_Hamburg.robot
    [Documentation]   Demonstrate that it is possible to download an XML representation of the UAG configuration from CMS.
    [Tags]      vUAG_REG_011    TMSII00606289

    # 0. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[79]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc79_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc79_obj}    get_testcase_info
    ${ims_tc79_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc79_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc79_obj}    get_devices_info
    ${trace_inputs}    Call Method    ${ims_tc79_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]

    # 2. perform reg dereg
    ${start_time_stamp}    start_time_margin    60
    execute_android_registration_and_deregistration    ${devices_info}[device_1]     duration=50
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

    # 3. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]

    # 4. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}
    ${success_message}=    Set Variable   [✓] Pcap Downloaded Successful
    Log To Console    ${success_message}
    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]
