
*** Settings ***

Variables    ..LOCAL_PATH_PLACEHOLDER
Variables    ..LOCAL_PATH_PLACEHOLDER
Variables    ..LOCAL_PATH_PLACEHOLDER


Resource     ..LOCAL_PATH_PLACEHOLDER
Resource     ..LOCAL_PATH_PLACEHOLDER
Resource    SOURCE_NAME_PLACEHOLDER.robot
Variables    ..LOCAL_PATH_PLACEHOLDER

Library      Collections
Library      DateTime
Library      ..LOCAL_PATH_PLACEHOLDER
Library      ..LOCAL_PATH_PLACEHOLDER
Library      ..LOCAL_PATH_PLACEHOLDER
Library      ..LOCAL_PATH_PLACEHOLDER    ${nosqldatabase}    ${testdb}
Library      ..LOCAL_PATH_PLACEHOLDER  ${ANRITSU}
Library      ..LOCAL_PATH_PLACEHOLDER
Library    ..LOCAL_PATH_PLACEHOLDER
Library    ..LOCAL_PATH_PLACEHOLDER    ${CMS}
Library    Call_Flow.quick_validator
*** Test Cases ***
Basic_call_VoLTE_long_duration_call
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER" --test "Basic_call_VoLTE_long_duration_call" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    CTAS_LONG_CALL    TMSII00613035
    [Tags]    SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[Basic_call_VoLTE_long_duration_call][${sites}]
    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc75_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc75_obj}    get_testcase_info
    ${ims_tc75_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc75_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc75_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc75_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc75_obj}    get_trace_inputs

    # # 1. Verify Sim card
    # ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    # ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    # Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    # Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # # 2. Verify IMS registration for Devices
    # android_registration_check    ${devices_info}[device_1]
    # android_registration_check    ${devices_info}[device_2]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    initiate_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    Notional_format=${True}
    accept_android_call_session_ab    ${devices_info}[device_2]    ${call_duration}
    Sleep    1 minutes

    # 4. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]    ${devices_info}[device_2]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}
    ${success_message}=    Set Variable   [✓] Pcap Downloaded Successful
    Log To Console    ${success_message}
