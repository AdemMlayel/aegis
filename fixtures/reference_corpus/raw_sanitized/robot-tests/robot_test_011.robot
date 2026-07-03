
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
IMS_v6_->_IMS_v6_clear_from_MO_side
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v6_clear_from_MO_side" --test "IMS_v6_->_IMS_v6_clear_from_MO_side" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    vUAG_CAL_063    TMSII00606341
    [Tags]     SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v6_->_IMS_v6_clear_from_MO_side][${sites}]

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

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_1]    Notional_format=${False}
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


IMS_v6_->_IMS_v6_clear_from_MT_side
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v6_clear_from_MT_side" --test "IMS_v6_->_IMS_v6_clear_from_MT_side" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    TMSII00606341    vUAG_CAL_063
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v6_->_IMS_v6_clear_from_MT_side][${sites}]
    log to console    ${id}
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

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_2]    Notional_format=${False}
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes



IMS_v6_->_IMS_v4_clear_from_Mo_side
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v4_clear_from_Mo_side" --test "IMS_v6_->_IMS_v4_clear_from_Mo_side" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    TMSII00606362    vUAG_CAL_084
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v6_->_IMS_v4_clear_from_Mo_side][${sites}]

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

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_1]    Notional_format=${False}
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

IMS_v6_->_IMS_v4_clear_from_MT_side
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v4_clear_from_MT_side" --test "IMS_v6_->_IMS_v4_clear_from_MT_side" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    TMSII00606341    vUAG_CAL_063
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v6_->_IMS_v4_clear_from_MT_side][${sites}]

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

    # # 3. Execute VoLTE call scenario
    # ${start_time_stamp}    start_time_margin    60
    # execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_1]    Notional_format=${False}
    # ${end_time_stamp}      end_time_margin    60
    # Sleep    1 minutes

    # # 4. Collect Anritsu trace
    # ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    # Should Be True    ${initialize_anritsu_driver}
    # ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]    ${devices_info}[device_2]
    # Should Be True    ${start_oesearch}
    # ${sleep_time}    sleep_time_for    oesearch
    # Sleep    ${sleep_time}
    # ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    # Should Be True    ${Oesearch_pcap_download}

    # 5. PCAP Validation
    #${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]
    ${pcap_file_path}=    Set Variable     LOCAL_PATH_PLACEHOLDER
    ${val_result}    Validate Volte Call    IPV6_TO_IPV4_CALL    a_msisdn=+${devices_info}[device_1][sim][msisdn]    b_msisdn=+${devices_info}[device_2][sim][msisdn]    a_imsi=${devices_info}[device_1][sim][imsi]    b_imsi=${devices_info}[device_2][sim][imsi]    clear_party=clear_B    pcap_file_path=${pcap_file_path}
    Log               <table>${val_result}[0]</table>        html=True
    Log               <table>${val_result}[1]</table>        html=True
    Should Be True     ${val_result}[2]




IMS_v4_->_IMS_v4_clear_from_MT_side
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v4_clear_from_MT_side" --test "IMS_v4_->_IMS_v4_clear_from_MT_side" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    vUAG_CAL_023        TMSII00606301
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v4_->_IMS_v4_clear_from_MT_side][${sites}]

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

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_2]    Notional_format=${False}
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes


IMS_v4_->_IMS_v4_clear_from_MO_side
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v4_clear_from_MO_side" --test "IMS_v4_->_IMS_v4_clear_from_MO_side" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    vUAG_CAL_022        TMSII00606300
    [Tags]    SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v4_->_IMS_v4_clear_from_MO_side][${sites}]

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

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_2]    Notional_format=${False}
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

IMS_v4_->_IMS_v6_clear_from_MO_side
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v6_clear_from_MO_side" --test "IMS_v4_->_IMS_v6_clear_from_MO_side" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]   vUAG_CAL_043        TMSII00606321
    [Tags]       SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v4_->_IMS_v6_clear_from_MO_side][${sites}]

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

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_1]    Notional_format=${False}
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

IMS_v4_->_IMS_v6_clear_from_MT_side
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v6_clear_from_MT_side" --test "IMS_v4_->_IMS_v6_clear_from_MT_side" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]   vUAG_CAL_043        TMSII01060217
    [Tags]       SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v4_->_IMS_v6_clear_from_MT_side][${sites}]

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

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_2]    Notional_format=${False}
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

IMS_v6->VoWifi_release_before_answer
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>VoWifi_release_before_answer" --test "IMS_v6->VoWifi_release_before_answer" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    vUAG_CAL_304        TMSII00606582
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v6->VoWifi_release_before_answer][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc35_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc35_obj}    get_testcase_info
    ${ims_tc35_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc35_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc35_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc35_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc35_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    initiate_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    Notional_format=${True}
    Sleep    5
    terminate_android_call_session_ab    ${devices_info}[device_1]
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

    # 4. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}

    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]
    #${pcap_file_path}=    Set Variable     LOCAL_PATH_PLACEHOLDER
    ${val_result}    Validate Volte Call    IPV6_TO_VOWIFI_CALL_REL_BEF_ANS    a_msisdn=+${devices_info}[device_1][sim][msisdn]    b_msisdn=+${devices_info}[device_2][sim][msisdn]    a_imsi=${devices_info}[device_1][sim][imsi]    b_imsi=${devices_info}[device_1][sim][imsi]    pcap_file_path=${pcap_file_path}
    Log               <table>${val_result}[0]</table>        html=True
    Log               <table>${val_result}[1]</table>        html=True
    Should Be True     ${val_result}[2]

VoWifi->IMS_v6_clear_from_MO_side
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>IMS_v6_clear_from_MO_side" --test "VoWifi->IMS_v6_clear_from_MO_side" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    vUAG_CAL_279        TMSII00606557
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[VoWifi->IMS_v6_clear_from_MO_side][${sites}]
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc35_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc35_obj}    get_testcase_info
    ${ims_tc35_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc35_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc35_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc35_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc35_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_1]    Notional_format=${False}
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes


    # 4. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}

    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]
    #${pcap_file_path}=    Set Variable     LOCAL_PATH_PLACEHOLDER
    ${val_result}    Validate Volte Call    IPV6_TO_VOWIFI_CALL_REL_BEF_ANS    a_msisdn=+${devices_info}[device_1][sim][msisdn]    b_msisdn=+${devices_info}[device_2][sim][msisdn]    a_imsi=${devices_info}[device_1][sim][imsi]    b_imsi=${devices_info}[device_1][sim][imsi]    pcap_file_path=${pcap_file_path}
    Log               <table>${val_result}[0]</table>        html=True
    Log               <table>${val_result}[1]</table>        html=True
    Should Be True     ${val_result}[2]

VoWifi->IMS_v6_clear_from_MT_side
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>IMS_v6_clear_from_MT_side" --test "VoWifi->IMS_v6_clear_from_MT_side" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    vUAG_CAL_280        TMSII00606558
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[VoWifi->IMS_v6_clear_from_MT_side][${sites}]
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc35_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc35_obj}    get_testcase_info
    ${ims_tc35_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc35_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc35_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc35_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc35_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_2]    Notional_format=${False}
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

    # 4. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}

    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]
    #${pcap_file_path}=    Set Variable     LOCAL_PATH_PLACEHOLDER
    ${val_result}    Validate Volte Call    IPV6_TO_VOWIFI_CALL_REL_BEF_ANS    a_msisdn=+${devices_info}[device_1][sim][msisdn]    b_msisdn=+${devices_info}[device_2][sim][msisdn]    a_imsi=${devices_info}[device_1][sim][imsi]    b_imsi=${devices_info}[device_1][sim][imsi]    pcap_file_path=${pcap_file_path}
    Log               <table>${val_result}[0]</table>        html=True
    Log               <table>${val_result}[1]</table>        html=True
    Should Be True     ${val_result}[2]
IMS_v6->VoWifi_clear_from_MO_side
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>VoWifi_clear_from_MO_side" --test "IMS_v6->VoWifi_clear_from_MO_side" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    vUAG_CAL_299        TMSII00606577
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v6->VoWifi_clear_from_MO_side][${sites}]
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc35_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc35_obj}    get_testcase_info
    ${ims_tc35_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc35_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc35_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc35_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc35_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_2]    Notional_format=${False}
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes


    # 4. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}

    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]
    #${pcap_file_path}=    Set Variable     LOCAL_PATH_PLACEHOLDER
    ${val_result}    Validate Volte Call    IPV6_TO_VOWIFI_CALL_REL_BEF_ANS    a_msisdn=+${devices_info}[device_1][sim][msisdn]    b_msisdn=+${devices_info}[device_2][sim][msisdn]    a_imsi=${devices_info}[device_1][sim][imsi]    b_imsi=${devices_info}[device_1][sim][imsi]    pcap_file_path=${pcap_file_path}
    Log               <table>${val_result}[0]</table>        html=True
    Log               <table>${val_result}[1]</table>        html=True
    Should Be True     ${val_result}[2]

IMS_v6->VoWifi_clear_from_MT_side
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>VoWifi_clear_from_MT_side" --test "IMS_v6->VoWifi_clear_from_MT_side" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    vUAG_CAL_300       TMSII00606578
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v6->VoWifi_clear_from_MT_side][${sites}]
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc35_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc35_obj}    get_testcase_info
    ${ims_tc35_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc35_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc35_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc35_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc35_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_2]    Notional_format=${False}
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes


    # 4. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}

    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]
    #${pcap_file_path}=    Set Variable     LOCAL_PATH_PLACEHOLDER
    ${val_result}    Validate Volte Call    IPV6_TO_VOWIFI_CALL_REL_BEF_ANS    a_msisdn=+${devices_info}[device_1][sim][msisdn]    b_msisdn=+${devices_info}[device_2][sim][msisdn]    a_imsi=${devices_info}[device_1][sim][imsi]    b_imsi=${devices_info}[device_1][sim][imsi]    pcap_file_path=${pcap_file_path}
    Log               <table>${val_result}[0]</table>        html=True
    Log               <table>${val_result}[1]</table>        html=True
    Should Be True     ${val_result}[2]
IMS_v6->IMS_v6_release_before_answer
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>IMS_v6_release_before_answer" --test "IMS_v6->IMS_v6_release_before_answer" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    vUAG_CAL_068       TMSII00606346
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v6->IMS_v6_release_before_answer][${sites}]
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc35_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc35_obj}    get_testcase_info
    ${ims_tc35_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc35_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc35_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc35_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc35_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    initiate_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    Notional_format=${True}
    Sleep    5
    terminate_android_call_session_ab    ${devices_info}[device_1]
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

    # 4. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}

    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]
    #${pcap_file_path}=    Set Variable     LOCAL_PATH_PLACEHOLDER
    ${val_result}    Validate Volte Call    IPV6_TO_VOWIFI_CALL_REL_BEF_ANS    a_msisdn=+${devices_info}[device_1][sim][msisdn]    b_msisdn=+${devices_info}[device_2][sim][msisdn]    a_imsi=${devices_info}[device_1][sim][imsi]    b_imsi=${devices_info}[device_1][sim][imsi]    pcap_file_path=${pcap_file_path}
    Log               <table>${val_result}[0]</table>        html=True
    Log               <table>${val_result}[1]</table>        html=True
    Should Be True     ${val_result}[2]
IMS_v6->IMS_v4_release_before_answer
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>IMS_v4_release_before_answer" --test "IMS_v6->IMS_v4_release_before_answer" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    vUAG_CAL_088       TMSII00606366
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v6->IMS_v4_release_before_answer][${sites}]
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc35_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc35_obj}    get_testcase_info
    ${ims_tc35_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc35_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc35_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc35_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc35_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    initiate_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    Notional_format=${True}
    Sleep    5
    terminate_android_call_session_ab    ${devices_info}[device_1]
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

    # 4. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}

    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]
    #${pcap_file_path}=    Set Variable     LOCAL_PATH_PLACEHOLDER
    ${val_result}    Validate Volte Call    IPV6_TO_VOWIFI_CALL_REL_BEF_ANS    a_msisdn=+${devices_info}[device_1][sim][msisdn]    b_msisdn=+${devices_info}[device_2][sim][msisdn]    a_imsi=${devices_info}[device_1][sim][imsi]    b_imsi=${devices_info}[device_1][sim][imsi]    pcap_file_path=${pcap_file_path}
    Log               <table>${val_result}[0]</table>        html=True
    Log               <table>${val_result}[1]</table>        html=True
    Should Be True     ${val_result}[2]
IMS_v4->IMS_v6_release_before_answer
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>IMS_v6_release_before_answer" --test "IMS_v4->IMS_v6_release_before_answer" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    vUAG_CAL_088       TMSII00606366
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v4->IMS_v6_release_before_answer][${sites}]
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc35_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc35_obj}    get_testcase_info
    ${ims_tc35_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc35_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc35_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc35_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc35_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    initiate_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    Notional_format=${True}
    Sleep    5
    terminate_android_call_session_ab    ${devices_info}[device_1]
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

    # 4. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}

    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]
    #${pcap_file_path}=    Set Variable     LOCAL_PATH_PLACEHOLDER
    ${val_result}    Validate Volte Call    IPV6_TO_VOWIFI_CALL_REL_BEF_ANS    a_msisdn=+${devices_info}[device_1][sim][msisdn]    b_msisdn=+${devices_info}[device_2][sim][msisdn]    a_imsi=${devices_info}[device_1][sim][imsi]    b_imsi=${devices_info}[device_1][sim][imsi]    pcap_file_path=${pcap_file_path}
    Log               <table>${val_result}[0]</table>        html=True
    Log               <table>${val_result}[1]</table>        html=True
    Should Be True     ${val_result}[2]

IMS_v4->IMS_v4_release_before_answer
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>IMS_v4_release_before_answer" --test "IMS_v4->IMS_v4_release_before_answer" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    vUAG_CAL_027       TMSII00606305
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v4->IMS_v4_release_before_answer][${sites}]
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc35_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc35_obj}    get_testcase_info
    ${ims_tc35_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc35_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc35_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc35_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc35_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    initiate_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    Notional_format=${True}
    Sleep    5
    terminate_android_call_session_ab    ${devices_info}[device_1]
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

    # 4. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}

    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]
    #${pcap_file_path}=    Set Variable     LOCAL_PATH_PLACEHOLDER
    ${val_result}    Validate Volte Call    IPV6_TO_VOWIFI_CALL_REL_BEF_ANS    a_msisdn=+${devices_info}[device_1][sim][msisdn]    b_msisdn=+${devices_info}[device_2][sim][msisdn]    a_imsi=${devices_info}[device_1][sim][imsi]    b_imsi=${devices_info}[device_1][sim][imsi]    pcap_file_path=${pcap_file_path}
    Log               <table>${val_result}[0]</table>        html=True
    Log               <table>${val_result}[1]</table>        html=True
    Should Be True     ${val_result}[2]

Software Verification
    # robot --variable sites:hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER Verification" --test "Software Verification" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    Verify the software version running on each VNF
    [Tags]      vUAG_OAM_319    TMSII00606597

    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[24]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}

    ${ims_tc24_obj}    Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc24_obj}    get_testcase_info
    ${vnf_info}        Call Method    ${ims_tc24_obj}    get_vnf_info
    ${vnf_val}         Call Method    ${ims_tc24_obj}    get_vnf_val

    ${ims_tc24_obj}    Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc24_obj}    get_testcase_info

    # 2. Select node based on site
    IF    '${sites}' == 'munich'
        ${selected_node}=     Set Variable    ${Uagtrm01}
        ${selected_name}=     Set Variable    Uagtrm01
    ELSE IF    '${sites}' == 'hamburg'
        ${selected_node}=     Set Variable    ${Uagtrh01}
        ${selected_name}=     Set Variable    Uagtrh01
    ELSE
        Fail    Unsupported site: ${sites}
    END

    # 3. Login and scrape data
    ${nodeobj}         Create_Object    SOURCE_NAME_PLACEHOLDER    ${selected_node}    ${selected_name}

    ${scrap_data}      Call Method
    ...    ${nodeobj}
    ...    scrape_all_nodes
    ...    ${vnf_info}[commands][0]
    ...    ${tc_info}[tc_dir]

    ${output_text_dic}    Call Method
    ...    ${nodeobj}
    ...    load_all_output_texts
    ...    ${tc_info}[tc_dir]

    Should Be True    ${scrap_data}

    # 4. Validation
    ${val_tc124_obj}    Create Object
    ...    SOURCE_NAME_PLACEHOLDER
    ...    ${output_text_dic}
    ...    ${vnf_val}[static_test_data]
    ...    ${tc_info}[tc_dir]

    Call Method
    ...    ${val_tc124_obj}
    ...    load_testdata
    ...    messages
    ...    ${vnf_val}[messages]

    ${df_html}    ${val_result}    Call Method
    ...    ${val_tc124_obj}
    ...    get_validation_results
    ...    ${output_text_dic}

    Log    <table>${df_html}</table>    html=True

    Should Be True    ${val_result}

New_registration_IPv6_Android
    # robot --variable sites:hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER" --test "New_registration_IPv6_Android" SOURCE_NAME_PLACEHOLDER.robot
    [Tags]      SOURCE_NAME_PLACEHOLDER
    [Documentation]   vUAG_REG_005    TMSII00606283

    ${id}              Set Variable    ${vims_tcs}[New_registration_IPv6_Android][${sites}]
    # 0. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc77_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc77_obj}    get_testcase_info
    ${ims_tc77_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc77_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc77_obj}    get_devices_info
    ${trace_inputs}    Call Method    ${ims_tc77_obj}    get_trace_inputs

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


New_registration_IPv4_Android
    # robot --variable sites:hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER" --test "New_registration_IPv4_Android" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]   vUAG_REG_011    TMSII00606289
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[New_registration_IPv4_Android][${sites}]

    # 0. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc78_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc78_obj}    get_testcase_info
    ${ims_tc78_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc78_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc78_obj}    get_devices_info
    ${trace_inputs}    Call Method    ${ims_tc78_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    #Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sims][sim_slot_2][slot_number]
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


Registration:VoLTE_User_registration
    # robot --variable sites:hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER:VoLTE_User_registration_" --test "Registration:VoLTE_User_registration" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]   vUAG_REG_011    TMSII00606289
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[Registration:VoLTE_User_registration][${sites}]

    # 0. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]

    # 0. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[27]
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



Download_UAG_configuration
    # robot --outputdir "..LOCAL_PATH_PLACEHOLDER" --test "Download_UAG_configuration" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]   vUAG_OAM_320   TMSII00606598
    [Tags]      SOURCE_NAME_PLACEHOLDER

    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[28]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc26_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc26_obj}    get_testcase_info
    ${ims_tc26_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc26_obj}    get_testcase_info
    ${cms_info}         Call Method    ${ims_tc26_obj}    get_cms_info

    # 2 check service status
    ${config_downloaded}     SOURCE_NAME_PLACEHOLDER.download_config    ${tc_info}[tc_dir]     ${cms_config_download}    ${cms_info}[site]
    Should Be True    ${config_downloaded}

IMS_v6_->_IMS_v6_Call_forwarding_unconditional
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v6_Call_forwarding_unconditional" --test "IMS_v6_->_IMS_v6_Call_forwarding_unconditional" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    vUAG_CAL_078    TMSII00606356
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v6_->_IMS_v6_Call_forwarding_unconditional][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc70_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc70_obj}    get_testcase_info
    ${ims_tc70_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc70_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc70_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc70_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc70_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    ${device3_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device3_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]
    android_registration_check    ${devices_info}[device_3]

    # 3. Set CFNRc for B to C
    android_set_call_forwarding    ${devices_info}[device_2]    ${devices_info}[device_3]    condition=CFU

    # 4. Execute VoLTE call scenario
    log    Executing forwarding chain : CFU Unconditional forwarding
    ${start_time_stamp}    start_time_margin    60
    initiate_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    Notional_format=${True}
    accept_android_call_session_ab    ${devices_info}[device_3]    ${call_duration}
    terminate_android_call_session_ab    ${devices_info}[device_1]
    ${end_time_stamp}      end_time_margin    60

    # 5. Disable forwarding chain
    android_disable_call_forwarding    ${devices_info}[device_2]     condition=CFU
    Sleep    1 minutes

    # 6. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]    ${devices_info}[device_3]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}
    ${success_message}=    Set Variable   [✓] Pcap Downloaded Successful
    Log To Console    ${success_message}
    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]


IMS_v6_->_IMS_v4_Call_forwarding_unconditional
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v4_Call_forwarding_unconditional" --test "IMS_v6_->_IMS_v4_Call_forwarding_unconditional" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    vUAG_CAL_058    TMSII00606336
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v6_->_IMS_v4_Call_forwarding_unconditional][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc70_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc70_obj}    get_testcase_info
    ${ims_tc70_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc70_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc70_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc70_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc70_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    ${device3_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device3_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]
    android_registration_check    ${devices_info}[device_3]

    # 3. Set CFNRc for B to C
    android_set_call_forwarding    ${devices_info}[device_2]    ${devices_info}[device_3]    condition=CFU

    # 4. Execute VoLTE call scenario
    log    Executing forwarding chain : CFU Unconditional forwarding
    ${start_time_stamp}    start_time_margin    60
    initiate_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    Notional_format=${True}
    accept_android_call_session_ab    ${devices_info}[device_3]    ${call_duration}
    terminate_android_call_session_ab    ${devices_info}[device_1]
    ${end_time_stamp}      end_time_margin    60

    # 5. Disable forwarding chain
    android_disable_call_forwarding    ${devices_info}[device_2]     condition=CFU
    Sleep    1 minutes

    # 6. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]    ${devices_info}[device_3]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}
    ${success_message}=    Set Variable   [✓] Pcap Downloaded Successful
    Log To Console    ${success_message}
    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]

IMS_v4_->_IMS_v4_Call_forwarding_unconditional
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v4_Call_forwarding_unconditional" --test "IMS_v4_->_IMS_v4_Call_forwarding_unconditional" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    vUAG_CAL_037    TMSII00606315
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v4_->_IMS_v4_Call_forwarding_unconditional][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc70_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc70_obj}    get_testcase_info
    ${ims_tc70_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc70_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc70_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc70_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc70_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    ${device3_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device3_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]
    android_registration_check    ${devices_info}[device_3]

    # 3. Set CFNRc for B to C
    android_set_call_forwarding    ${devices_info}[device_2]    ${devices_info}[device_3]    condition=CFU

    # 4. Execute VoLTE call scenario
    log    Executing forwarding chain : CFU Unconditional forwarding
    ${start_time_stamp}    start_time_margin    60
    initiate_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    Notional_format=${True}
    accept_android_call_session_ab    ${devices_info}[device_3]    ${call_duration}
    terminate_android_call_session_ab    ${devices_info}[device_1]
    ${end_time_stamp}      end_time_margin    60

    # 5. Disable forwarding chain
    android_disable_call_forwarding    ${devices_info}[device_2]     condition=CFU
    Sleep    1 minutes

    # 6. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]    ${devices_info}[device_3]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}
    ${success_message}=    Set Variable   [✓] Pcap Downloaded Successful
    Log To Console    ${success_message}
    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]


IMS_v4_->_IMS_v6_Call_forwarding_unconditional
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v4_Call_forwarding_unconditional" --test "IMS_v6_->_IMS_v4_Call_forwarding_unconditional" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    vUAG_CAL_078    TMSII00606356
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v6_->_IMS_v4_Call_forwarding_unconditional][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc70_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc70_obj}    get_testcase_info
    ${ims_tc70_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc70_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc70_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc70_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc70_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    ${device3_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device3_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]
    android_registration_check    ${devices_info}[device_3]

    # 3. Set CFNRc for B to C
    android_set_call_forwarding    ${devices_info}[device_2]    ${devices_info}[device_3]    condition=CFU

    # 4. Execute VoLTE call scenario
    log    Executing forwarding chain : CFU Unconditional forwarding
    ${start_time_stamp}    start_time_margin    60
    initiate_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    Notional_format=${True}
    accept_android_call_session_ab    ${devices_info}[device_3]    ${call_duration}
    terminate_android_call_session_ab    ${devices_info}[device_1]
    ${end_time_stamp}      end_time_margin    60

    # 5. Disable forwarding chain
    android_disable_call_forwarding    ${devices_info}[device_2]     condition=CFU
    Sleep    1 minutes

    # 6. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]    ${devices_info}[device_3]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}
    ${success_message}=    Set Variable   [✓] Pcap Downloaded Successful
    Log To Console    ${success_message}
    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]


IMS_v6_->_IMS_v6_Call_forwarding_not_Reachable
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v6_Call_forwarding_not_Reachable" --test "IMS_v6_->_IMS_v6_Call_forwarding_not_Reachable" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    vUAG_CAL_076        TMSII00606354
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v6_->_IMS_v6_Call_forwarding_not_Reachable][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc86_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc86_obj}    get_testcase_info
    ${ims_tc86_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc86_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc86_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc86_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc86_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    ${device3_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device3_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]
    android_registration_check    ${devices_info}[device_3]

    # 3. Set CFNRc for B to C
    android_set_call_forwarding    ${devices_info}[device_2]    ${devices_info}[device_3]    CFNRc

    # 4. Execute VoLTE call scenario
    log    Executing forwarding chain : CFU Not Reachable forwarding
    ${start_time_stamp}    start_time_margin    60
    execute_android_deregistration    ${devices_info}[device_2]
    initiate_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    Notional_format=${True}
    accept_android_call_session_ab    ${devices_info}[device_3]     ${call_duration}
    terminate_android_call_session_ab    ${devices_info}[device_1]
    execute_android_registration    ${devices_info}[device_2]
    android_registration_check    ${devices_info}[device_2]
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

    # 5. Disable CFNRC call forwarding
    android_disable_call_forwarding    ${devices_info}[device_2]    CFNRc

    # # 6. Collect Anritsu trace
    # ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    # Should Be True    ${initialize_anritsu_driver}
    # ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]    ${devices_info}[device_3]
    # Should Be True    ${start_oesearch}
    # log    Anritsu Trace Initiated: Successful
    # ${sleep_time}    sleep_time_for    oesearch
    # Sleep    ${sleep_time}
    # ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    # Should Be True    ${Oesearch_pcap_download}
    # ${success_message}=    Set Variable   [✓] Pcap Downloaded Successful
    # Log To Console    ${success_message}
    # ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]


    # [Teardown]    android_disable_call_forwarding    ${devices_info}[device_2]    CFNRc
IMS_v4_->_IMS_v6_Call_forwarding_not_Reachable
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v6_Call_forwarding_not_Reachable" --test "IMS_v4_->_IMS_v6_Call_forwarding_not_Reachable" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    vUAG_CAL_076        TMSII00606354
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v4_->_IMS_v6_Call_forwarding_not_Reachable][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc86_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc86_obj}    get_testcase_info
    ${ims_tc86_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc86_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc86_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc86_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc86_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    ${device3_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device3_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]
    android_registration_check    ${devices_info}[device_3]

    # 3. Set CFNRc for B to C
    android_set_call_forwarding    ${devices_info}[device_2]    ${devices_info}[device_3]    CFNRc

    # 4. Execute VoLTE call scenario
    log    Executing forwarding chain : CFU Not Reachable forwarding
    ${start_time_stamp}    start_time_margin    60
    execute_android_deregistration    ${devices_info}[device_2]
    initiate_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    Notional_format=${True}
    accept_android_call_session_ab    ${devices_info}[device_3]     ${call_duration}
    terminate_android_call_session_ab    ${devices_info}[device_1]
    execute_android_registration    ${devices_info}[device_2]
    android_registration_check    ${devices_info}[device_2]
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

    # 5. Disable CFNRC call forwarding
    android_disable_call_forwarding    ${devices_info}[device_2]    CFNRc

    # # 6. Collect Anritsu trace
    # ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    # Should Be True    ${initialize_anritsu_driver}
    # ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]    ${devices_info}[device_3]
    # Should Be True    ${start_oesearch}
    # log    Anritsu Trace Initiated: Successful
    # ${sleep_time}    sleep_time_for    oesearch
    # Sleep    ${sleep_time}
    # ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    # Should Be True    ${Oesearch_pcap_download}
    # ${success_message}=    Set Variable   [✓] Pcap Downloaded Successful
    # Log To Console    ${success_message}
    # ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]


    # [Teardown]    android_disable_call_forwarding    ${devices_info}[device_2]    CFNRc
IMS_v4_->_IMS_v4_Call_forwarding_not_Reachable
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v4_Call_forwarding_not_Reachable" --test "IMS_v4_->_IMS_v4_Call_forwarding_not_Reachable" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    vUAG_CAL_035       TMSII00606313
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v4_->_IMS_v4_Call_forwarding_not_Reachable][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc86_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc86_obj}    get_testcase_info
    ${ims_tc86_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc86_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc86_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc86_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc86_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    ${device3_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device3_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]
    android_registration_check    ${devices_info}[device_3]

    # 3. Set CFNRc for B to C
    android_set_call_forwarding    ${devices_info}[device_2]    ${devices_info}[device_3]    CFNRc

    # 4. Execute VoLTE call scenario
    log    Executing forwarding chain : CFU Not Reachable forwarding
    ${start_time_stamp}    start_time_margin    60
    execute_android_deregistration    ${devices_info}[device_2]
    initiate_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    Notional_format=${True}
    accept_android_call_session_ab    ${devices_info}[device_3]     ${call_duration}
    terminate_android_call_session_ab    ${devices_info}[device_1]
    execute_android_registration    ${devices_info}[device_2]
    android_registration_check    ${devices_info}[device_2]
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

    # 5. Disable CFNRC call forwarding
    android_disable_call_forwarding    ${devices_info}[device_2]    CFNRc

    # # 6. Collect Anritsu trace
    # ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    # Should Be True    ${initialize_anritsu_driver}
    # ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]    ${devices_info}[device_3]
    # Should Be True    ${start_oesearch}
    # log    Anritsu Trace Initiated: Successful
    # ${sleep_time}    sleep_time_for    oesearch
    # Sleep    ${sleep_time}
    # ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    # Should Be True    ${Oesearch_pcap_download}
    # ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]


    # [Teardown]    android_disable_call_forwarding    ${devices_info}[device_2]    CFNRc
IMS_v6_->_IMS_v4_Call_forwarding_not_Reachable
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v4_Call_forwarding_not_Reachable" --test "IMS_v6_->_IMS_v4_Call_forwarding_not_Reachable" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    vUAG_CAL_096        TMSII00606374
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v6_->_IMS_v4_Call_forwarding_not_Reachable][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc86_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc86_obj}    get_testcase_info
    ${ims_tc86_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc86_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc86_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc86_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc86_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    ${device3_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device3_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]
    android_registration_check    ${devices_info}[device_3]

    # 3. Set CFNRc for B to C
    android_set_call_forwarding    ${devices_info}[device_2]    ${devices_info}[device_3]    CFNRc

    # 4. Execute VoLTE call scenario
    log    Executing forwarding chain : CFU Not Reachable forwarding
    ${start_time_stamp}    start_time_margin    60
    execute_android_deregistration    ${devices_info}[device_2]
    initiate_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    Notional_format=${True}
    accept_android_call_session_ab    ${devices_info}[device_3]     ${call_duration}
    terminate_android_call_session_ab    ${devices_info}[device_1]
    execute_android_registration    ${devices_info}[device_2]
    android_registration_check    ${devices_info}[device_2]
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

    # 5. Disable CFNRC call forwarding
    android_disable_call_forwarding    ${devices_info}[device_2]    CFNRc

    # # 6. Collect Anritsu trace
    # ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    # Should Be True    ${initialize_anritsu_driver}
    # ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]    ${devices_info}[device_3]
    # Should Be True    ${start_oesearch}
    # log    Anritsu Trace Initiated: Successful
    # ${sleep_time}    sleep_time_for    oesearch
    # Sleep    ${sleep_time}
    # ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    # Should Be True    ${Oesearch_pcap_download}
    # ${success_message}=    Set Variable   [✓] Pcap Downloaded Successful
    # Log To Console    ${success_message}
    # ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]


    # [Teardown]    android_disable_call_forwarding    ${devices_info}[device_2]    CFNRc

IMS_v6_->_IMS_v4_Call_forwarding_Busy
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v4_Call_forwarding_Busy" --test "IMS_v6_->_IMS_v4_Call_forwarding_Busy" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    vUAG_CAL_098        TMSII00606374
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v6_->_IMS_v4_Call_forwarding_Busy][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[84]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc85_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc85_obj}    get_testcase_info
    ${ims_tc85_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc85_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc85_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc85_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc85_obj}    get_trace_inputs

    # 1. Verify Sim card
    # ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    # ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    # ${device3_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]
    # ${device3_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]
    # Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    # Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    # #Run Keyword If    '${device3_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]
    # #Run Keyword If    '${device4_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    #android_registration_check    ${devices_info}[device_1]
    #android_registration_check    ${devices_info}[device_2]
    #android_registration_check    ${devices_info}[device_3]
    #android_registration_check    ${devices_info}[device_4]

    # 3. Set CFB for B to C
    # android_set_call_forwarding    ${devices_info}[device_2]    ${devices_info}[device_3]    CFB

    # 4. Execute VoLTE call scenario
    log    Executing forwarding chain : CFB Reject forwarding
    ${start_time_stamp}    start_time_margin    60
    initiate_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    Notional_format=${True}
    terminate_android_call_session_ab    ${devices_info}[device_2]
    accept_android_call_session_ab    ${devices_info}[device_3]    ${call_duration}
    terminate_android_call_session_ab    ${devices_info}[device_1]
    ${end_time_stamp}      end_time_margin    60
    #Sleep    1 minutes

    # # 5. Disable CFNRC call forwarding
    # android_disable_call forwarding    ${devices_info}[device_2]    CFB

    # # 6. Collect Anritsu trace
    # ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    # Should Be True    ${initialize_anritsu_driver}
    # ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]    ${devices_info}[device_3]
    # Should Be True    ${start_oesearch}
    # log    Anritsu Trace Initiated: Successful
    # ${sleep_time}    sleep_time_for    oesearch
    # Sleep    ${sleep_time}
    # ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    # Should Be True    ${Oesearch_pcap_download}
    # ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]

IMS_v6_->_IMS_v6_Call_forwarding_Busy
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v6_Call_forwarding_Busy" --test "IMS_v6_->_IMS_v6_Call_forwarding_Busy" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    vUAG_CAL_078        TMSII00606356
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v6_->_IMS_v6_Call_forwarding_Busy][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[84]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc85_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc85_obj}    get_testcase_info
    ${ims_tc85_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc85_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc85_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc85_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc85_obj}    get_trace_inputs

    # 1. Verify Sim card
    # ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    # ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    # ${device3_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]
    # ${device3_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]
    # Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    # Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    # #Run Keyword If    '${device3_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]
    # #Run Keyword If    '${device4_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    #android_registration_check    ${devices_info}[device_1]
    #android_registration_check    ${devices_info}[device_2]
    #android_registration_check    ${devices_info}[device_3]
    #android_registration_check    ${devices_info}[device_4]

    # 3. Set CFB for B to C
    # android_set_call_forwarding    ${devices_info}[device_2]    ${devices_info}[device_3]    CFB

    # 4. Execute VoLTE call scenario
    log    Executing forwarding chain : CFB Reject forwarding
    ${start_time_stamp}    start_time_margin    60
    initiate_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    Notional_format=${True}
    terminate_android_call_session_ab    ${devices_info}[device_2]
    accept_android_call_session_ab    ${devices_info}[device_3]    ${call_duration}
    terminate_android_call_session_ab    ${devices_info}[device_1]
    ${end_time_stamp}      end_time_margin    60
    #Sleep    1 minutes

    # # 5. Disable CFNRC call forwarding
    # android_disable_call forwarding    ${devices_info}[device_2]    CFB

    # # 6. Collect Anritsu trace
    # ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    # Should Be True    ${initialize_anritsu_driver}
    # ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]    ${devices_info}[device_3]
    # Should Be True    ${start_oesearch}
    # log    Anritsu Trace Initiated: Successful
    # ${sleep_time}    sleep_time_for    oesearch
    # Sleep    ${sleep_time}
    # ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    # Should Be True    ${Oesearch_pcap_download}
    # ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]

IMS_v4_->_IMS_v6_Call_forwarding_Busy
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v6_Call_forwarding_Busy" --test "IMS_v4_->_IMS_v6_Call_forwarding_Busy" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    vUAG_CAL_058        TMSII00606336
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v4_->_IMS_v6_Call_forwarding_Busy][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[84]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc85_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc85_obj}    get_testcase_info
    ${ims_tc85_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc85_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc85_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc85_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc85_obj}    get_trace_inputs

    # 1. Verify Sim card
    # ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    # ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    # ${device3_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]
    # ${device3_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]
    # Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    # Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    # #Run Keyword If    '${device3_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]
    # #Run Keyword If    '${device4_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    #android_registration_check    ${devices_info}[device_1]
    #android_registration_check    ${devices_info}[device_2]
    #android_registration_check    ${devices_info}[device_3]
    #android_registration_check    ${devices_info}[device_4]

    # 3. Set CFB for B to C
    # android_set_call_forwarding    ${devices_info}[device_2]    ${devices_info}[device_3]    CFB

    # 4. Execute VoLTE call scenario
    log    Executing forwarding chain : CFB Reject forwarding
    ${start_time_stamp}    start_time_margin    60
    initiate_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    Notional_format=${True}
    terminate_android_call_session_ab    ${devices_info}[device_2]
    accept_android_call_session_ab    ${devices_info}[device_3]    ${call_duration}
    terminate_android_call_session_ab    ${devices_info}[device_1]
    ${end_time_stamp}      end_time_margin    60
    #Sleep    1 minutes

    # # 5. Disable CFNRC call forwarding
    # android_disable_call forwarding    ${devices_info}[device_2]    CFB

    # # 6. Collect Anritsu trace
    # ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    # Should Be True    ${initialize_anritsu_driver}
    # ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]    ${devices_info}[device_3]
    # Should Be True    ${start_oesearch}
    # log    Anritsu Trace Initiated: Successful
    # ${sleep_time}    sleep_time_for    oesearch
    # Sleep    ${sleep_time}
    # ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    # Should Be True    ${Oesearch_pcap_download}
    # ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]


IMS_v4_->_IMS_v4_Call_forwarding_Busy
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v4_Call_forwarding_Busy" --test "IMS_v4_->_IMS_v4_Call_forwarding_Busy" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    vUAG_CAL_037       TMSII00606315
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v4_->_IMS_v4_Call_forwarding_Busy][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[84]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc85_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc85_obj}    get_testcase_info
    ${ims_tc85_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc85_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc85_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc85_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc85_obj}    get_trace_inputs

    # 1. Verify Sim card
    # ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    # ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    # ${device3_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]
    # ${device3_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]
    # Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    # Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    # #Run Keyword If    '${device3_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]
    # #Run Keyword If    '${device4_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_3]    ${devices_info}[device_3][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    #android_registration_check    ${devices_info}[device_1]
    #android_registration_check    ${devices_info}[device_2]
    #android_registration_check    ${devices_info}[device_3]
    #android_registration_check    ${devices_info}[device_4]

    # 3. Set CFB for B to C
    # android_set_call_forwarding    ${devices_info}[device_2]    ${devices_info}[device_3]    CFB

    # 4. Execute VoLTE call scenario
    log    Executing forwarding chain : CFB Reject forwarding
    ${start_time_stamp}    start_time_margin    60
    initiate_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    Notional_format=${True}
    terminate_android_call_session_ab    ${devices_info}[device_2]
    accept_android_call_session_ab    ${devices_info}[device_3]    ${call_duration}
    terminate_android_call_session_ab    ${devices_info}[device_1]
    ${end_time_stamp}      end_time_margin    60
    #Sleep    1 minutes

    # # 5. Disable CFNRC call forwarding
    # android_disable_call forwarding    ${devices_info}[device_2]    CFB

    # # 6. Collect Anritsu trace
    # ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    # Should Be True    ${initialize_anritsu_driver}
    # ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]    ${devices_info}[device_3]
    # Should Be True    ${start_oesearch}
    # log    Anritsu Trace Initiated: Successful
    # ${sleep_time}    sleep_time_for    oesearch
    # Sleep    ${sleep_time}
    # ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    # Should Be True    ${Oesearch_pcap_download}
    # ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]


IMS_v4_->_IMS_v6_MO_OIR_enabled
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v6_MO_OIR_enabled" --test "IMS_v4_->_IMS_v6_MO_OIR_enabled" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    vUAG_CAL_060        TMSII00606338
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v4_->_IMS_v6_MO_OIR_enabled][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc56_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc56_obj}    get_testcase_info
    ${ims_tc56_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc56_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc56_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc56_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc56_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]

    android_hide_number    ${devices_info}[device_1]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_1]    Notional_format=${False}
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

    android_display_number   ${devices_info}[device_1]

    # 4. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}

    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]
    #${pcap_file_path}=    Set Variable     LOCAL_PATH_PLACEHOLDER
    ${val_result}    Validate Volte Call    IPV4_TO_IPV6_MO_OIR    a_msisdn=anonymous    b_msisdn=+${devices_info}[device_2][sim][msisdn]    a_imsi=${devices_info}[device_1][sim][imsi]    b_imsi=${devices_info}[device_1][sim][imsi]    clear_party=clear_B    pcap_file_path=${pcap_file_path}    a_msisdn_oir=+${devices_info}[device_1][sim][msisdn]
    Log               <table>${val_result}[0]</table>        html=True
    Log               <table>${val_result}[1]</table>        html=True
    Should Be True     ${val_result}[2]


IMS_v4_->_IMS_v6_MO_OIR_disabled
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v6_MO_OIR_disabled" --test "IMS_v4_->_IMS_v6_MO_OIR_disabled" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    vUAG_CAL_061        TMSII00606339
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v4_->_IMS_v6_MO_OIR_disabled][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc56_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc56_obj}    get_testcase_info
    ${ims_tc56_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc56_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc56_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc56_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc56_obj}    get_trace_inputs

    # # 1. Verify Sim card
    # ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    # ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    # Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    # Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # # 2. Verify IMS registration for Devices
    # android_registration_check    ${devices_info}[device_1]
    # android_registration_check    ${devices_info}[device_2]

    android_display_number   ${devices_info}[device_1]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_1]    Notional_format=${False}
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes


    # 4. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}

    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]
    #${pcap_file_path}=    Set Variable     LOCAL_PATH_PLACEHOLDER
    ${val_result}    Validate Volte Call    IPV4_TO_IPV6_MO_OIR    a_msisdn=anonymous    b_msisdn=+${devices_info}[device_2][sim][msisdn]    a_imsi=${devices_info}[device_1][sim][imsi]    b_imsi=${devices_info}[device_1][sim][imsi]    clear_party=clear_B    pcap_file_path=${pcap_file_path}    a_msisdn_oir=+${devices_info}[device_1][sim][msisdn]
    Log               <table>${val_result}[0]</table>        html=True
    Log               <table>${val_result}[1]</table>        html=True
    Should Be True     ${val_result}[2]
IMS_v4_->_IMS_v4_MO_OIR_enabled
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v4_MO_OIR_enabled" --test "IMS_v4_->_IMS_v4_MO_OIR_enabled" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    vUAG_CAL_040        TMSII00606318
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v4_->_IMS_v4_MO_OIR_enabled][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc56_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc56_obj}    get_testcase_info
    ${ims_tc56_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc56_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc56_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc56_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc56_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]

    android_hide_number    ${devices_info}[device_1]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_1]    Notional_format=${False}
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

    android_display_number   ${devices_info}[device_1]

    # 4. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}

    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]
    #${pcap_file_path}=    Set Variable     LOCAL_PATH_PLACEHOLDER
    ${val_result}    Validate Volte Call    IPV4_TO_IPV6_MO_OIR    a_msisdn=anonymous    b_msisdn=+${devices_info}[device_2][sim][msisdn]    a_imsi=${devices_info}[device_1][sim][imsi]    b_imsi=${devices_info}[device_1][sim][imsi]    clear_party=clear_B    pcap_file_path=${pcap_file_path}    a_msisdn_oir=+${devices_info}[device_1][sim][msisdn]
    Log               <table>${val_result}[0]</table>        html=True
    Log               <table>${val_result}[1]</table>        html=True
    Should Be True     ${val_result}[2]


IMS_v4_->_IMS_v4_MO_OIR_disabled
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v4_MO_OIR_disabled" --test "IMS_v4_->_IMS_v4_MO_OIR_disabled" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    vUAG_CAL_041        TMSII00606319
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v4_->_IMS_v4_MO_OIR_disabled][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc56_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc56_obj}    get_testcase_info
    ${ims_tc56_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc56_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc56_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc56_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc56_obj}    get_trace_inputs

    # # 1. Verify Sim card
    # ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    # ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    # Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    # Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # # 2. Verify IMS registration for Devices
    # android_registration_check    ${devices_info}[device_1]
    # android_registration_check    ${devices_info}[device_2]

    android_display_number   ${devices_info}[device_1]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_1]    Notional_format=${False}
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

    # 4. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}

    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]
    #${pcap_file_path}=    Set Variable     LOCAL_PATH_PLACEHOLDER
    ${val_result}    Validate Volte Call    IPV4_TO_IPV6_MO_OIR    a_msisdn=anonymous    b_msisdn=+${devices_info}[device_2][sim][msisdn]    a_imsi=${devices_info}[device_1][sim][imsi]    b_imsi=${devices_info}[device_1][sim][imsi]    clear_party=clear_B    pcap_file_path=${pcap_file_path}    a_msisdn_oir=+${devices_info}[device_1][sim][msisdn]
    Log               <table>${val_result}[0]</table>        html=True
    Log               <table>${val_result}[1]</table>        html=True
    Should Be True     ${val_result}[2]

IMS_v6_->_IMS_v4_MO_OIR_enabled
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v4_MO_OIR_enabled" --test "IMS_v6_->_IMS_v4_MO_OIR_enabled" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    vUAG_CAL_100       TMSII00606378
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v6_->_IMS_v4_MO_OIR_enabled][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc56_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc56_obj}    get_testcase_info
    ${ims_tc56_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc56_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc56_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc56_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc56_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]

    android_hide_number    ${devices_info}[device_1]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_1]    Notional_format=${False}
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

    android_display_number   ${devices_info}[device_1]

    # 4. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}

    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]
    #${pcap_file_path}=    Set Variable     LOCAL_PATH_PLACEHOLDER
    ${val_result}    Validate Volte Call    IPV4_TO_IPV6_MO_OIR    a_msisdn=anonymous    b_msisdn=+${devices_info}[device_2][sim][msisdn]    a_imsi=${devices_info}[device_1][sim][imsi]    b_imsi=${devices_info}[device_1][sim][imsi]    clear_party=clear_B    pcap_file_path=${pcap_file_path}    a_msisdn_oir=+${devices_info}[device_1][sim][msisdn]
    Log               <table>${val_result}[0]</table>        html=True
    Log               <table>${val_result}[1]</table>        html=True
    Should Be True     ${val_result}[2]


IMS_v6_->_IMS_v4_MO_OIR_disabled
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v4_MO_OIR_disabled" --test "IMS_v6_->_IMS_v4_MO_OIR_disabled" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    vUAG_CAL_041        TMSII00606319
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v6_->_IMS_v4_MO_OIR_disabled][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc56_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc56_obj}    get_testcase_info
    ${ims_tc56_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc56_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc56_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc56_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc56_obj}    get_trace_inputs

    # # 1. Verify Sim card
    # ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    # ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    # Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    # Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # # 2. Verify IMS registration for Devices
    # android_registration_check    ${devices_info}[device_1]
    # android_registration_check    ${devices_info}[device_2]

    android_display_number   ${devices_info}[device_1]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_1]    Notional_format=${False}
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

    # 4. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}

    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]
    #${pcap_file_path}=    Set Variable     LOCAL_PATH_PLACEHOLDER
    ${val_result}    Validate Volte Call    IPV4_TO_IPV6_MO_OIR    a_msisdn=anonymous    b_msisdn=+${devices_info}[device_2][sim][msisdn]    a_imsi=${devices_info}[device_1][sim][imsi]    b_imsi=${devices_info}[device_1][sim][imsi]    clear_party=clear_B    pcap_file_path=${pcap_file_path}    a_msisdn_oir=+${devices_info}[device_1][sim][msisdn]
    Log               <table>${val_result}[0]</table>        html=True
    Log               <table>${val_result}[1]</table>        html=True
    Should Be True     ${val_result}[2]


IMS_v6_->_IMS_v6_MO_OIR_enabled
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v6_MO_OIR_enabled" --test "IMS_v6_->_IMS_v6_MO_OIR_enabled" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    vUAG_CAL_80       TMSII00606358
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v6_->_IMS_v6_MO_OIR_enabled][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc56_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc56_obj}    get_testcase_info
    ${ims_tc56_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc56_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc56_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc56_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc56_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]

    android_hide_number    ${devices_info}[device_1]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_1]    Notional_format=${False}
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

    android_display_number   ${devices_info}[device_1]

    # 4. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}

    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]
    #${pcap_file_path}=    Set Variable     LOCAL_PATH_PLACEHOLDER
    ${val_result}    Validate Volte Call    IPV4_TO_IPV6_MO_OIR    a_msisdn=anonymous    b_msisdn=+${devices_info}[device_2][sim][msisdn]    a_imsi=${devices_info}[device_1][sim][imsi]    b_imsi=${devices_info}[device_1][sim][imsi]    clear_party=clear_B    pcap_file_path=${pcap_file_path}    a_msisdn_oir=+${devices_info}[device_1][sim][msisdn]
    Log               <table>${val_result}[0]</table>        html=True
    Log               <table>${val_result}[1]</table>        html=True
    Should Be True     ${val_result}[2]


IMS_v6_->_IMS_v6_MO_OIR_disabled
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v6_MO_OIR_disabled" --test "IMS_v6_->_IMS_v6_MO_OIR_disabled" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    vUAG_CAL_081        TMSII00606359
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v6_->_IMS_v6_MO_OIR_disabled][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc56_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc56_obj}    get_testcase_info
    ${ims_tc56_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc56_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc56_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc56_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc56_obj}    get_trace_inputs

    # # 1. Verify Sim card
    # ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    # ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    # Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    # Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # # 2. Verify IMS registration for Devices
    # android_registration_check    ${devices_info}[device_1]
    # android_registration_check    ${devices_info}[device_2]

    android_display_number   ${devices_info}[device_1]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_1]    Notional_format=${False}
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

    # 4. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}

    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]
    #${pcap_file_path}=    Set Variable     LOCAL_PATH_PLACEHOLDER
    ${val_result}    Validate Volte Call    IPV4_TO_IPV6_MO_OIR    a_msisdn=anonymous    b_msisdn=+${devices_info}[device_2][sim][msisdn]    a_imsi=${devices_info}[device_1][sim][imsi]    b_imsi=${devices_info}[device_1][sim][imsi]    clear_party=clear_B    pcap_file_path=${pcap_file_path}    a_msisdn_oir=+${devices_info}[device_1][sim][msisdn]
    Log               <table>${val_result}[0]</table>        html=True
    Log               <table>${val_result}[1]</table>        html=True
    Should Be True     ${val_result}[2]

IMS_v4_->_IMS_v6_MO_OIR_enabled
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v6_MO_OIR_enabled" --test "IMS_v4_->_IMS_v6_MO_OIR_enabled" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    vUAG_CAL_060       TMSII00606338
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v4_->_IMS_v6_MO_OIR_enabled][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc56_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc56_obj}    get_testcase_info
    ${ims_tc56_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc56_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc56_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc56_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc56_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]

    android_hide_number    ${devices_info}[device_1]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_1]    Notional_format=${False}
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

    android_display_number   ${devices_info}[device_1]

    # 4. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}

    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]
    #${pcap_file_path}=    Set Variable     LOCAL_PATH_PLACEHOLDER
    ${val_result}    Validate Volte Call    IPV4_TO_IPV6_MO_OIR    a_msisdn=anonymous    b_msisdn=+${devices_info}[device_2][sim][msisdn]    a_imsi=${devices_info}[device_1][sim][imsi]    b_imsi=${devices_info}[device_1][sim][imsi]    clear_party=clear_B    pcap_file_path=${pcap_file_path}    a_msisdn_oir=+${devices_info}[device_1][sim][msisdn]
    Log               <table>${val_result}[0]</table>        html=True
    Log               <table>${val_result}[1]</table>        html=True
    Should Be True     ${val_result}[2]


IMS_v4_->_IMS_v6_MO_OIR_disabled
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v6_MO_OIR_disabled" --test "IMS_v4_->_IMS_v6_MO_OIR_disabled" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    vUAG_CAL_061       TMSII00606339
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[IMS_v6_->_IMS_v6_MO_OIR_disabled][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc56_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc56_obj}    get_testcase_info
    ${ims_tc56_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc56_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc56_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc56_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc56_obj}    get_trace_inputs

    # # 1. Verify Sim card
    # ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    # ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    # Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    # Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # # 2. Verify IMS registration for Devices
    # android_registration_check    ${devices_info}[device_1]
    # android_registration_check    ${devices_info}[device_2]

    android_display_number   ${devices_info}[device_1]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_1]    Notional_format=${False}
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

    # 4. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}

    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]
    #${pcap_file_path}=    Set Variable     LOCAL_PATH_PLACEHOLDER
    ${val_result}    Validate Volte Call    IPV4_TO_IPV6_MO_OIR    a_msisdn=anonymous    b_msisdn=+${devices_info}[device_2][sim][msisdn]    a_imsi=${devices_info}[device_1][sim][imsi]    b_imsi=${devices_info}[device_1][sim][imsi]    clear_party=clear_B    pcap_file_path=${pcap_file_path}    a_msisdn_oir=+${devices_info}[device_1][sim][msisdn]
    Log               <table>${val_result}[0]</table>        html=True
    Log               <table>${val_result}[1]</table>        html=True
    Should Be True     ${val_result}[2]

VoWifi_->_IMS_v6_MO_OIR_enabled
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_v6_MO_OIR_enabled" --test "VoWifi_->_IMS_v6_MO_OIR_enabled" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    vUAG_CAL_060       TMSII00606338
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[VoWifi_->_IMS_v6_MO_OIR_enabled][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc56_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc56_obj}    get_testcase_info
    ${ims_tc56_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc56_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc56_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc56_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc56_obj}    get_trace_inputs

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    android_registration_check    ${devices_info}[device_2]

    android_hide_number    ${devices_info}[device_1]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_1]    Notional_format=${False}
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

    android_display_number   ${devices_info}[device_1]

    # 4. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}

    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]
    #${pcap_file_path}=    Set Variable     LOCAL_PATH_PLACEHOLDER
    ${val_result}    Validate Volte Call    IPV4_TO_IPV6_MO_OIR    a_msisdn=anonymous    b_msisdn=+${devices_info}[device_2][sim][msisdn]    a_imsi=${devices_info}[device_1][sim][imsi]    b_imsi=${devices_info}[device_1][sim][imsi]    clear_party=clear_B    pcap_file_path=${pcap_file_path}    a_msisdn_oir=+${devices_info}[device_1][sim][msisdn]
    Log               <table>${val_result}[0]</table>        html=True
    Log               <table>${val_result}[1]</table>        html=True
    Should Be True     ${val_result}[2]


VoWifi_->_IMS_ v6_MT_OIP_disabled
    # robot --variable sites:hamburg-hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER>_IMS_ v6_MT_OIP_disabled" --test "VoWifi_->_IMS_ v6_MT_OIP_disabled" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    vUAG_CAL_297       TMSII00606575
    [Tags]      SOURCE_NAME_PLACEHOLDER

    ${id}              Set Variable    ${vims_tcs}[VoWifi_->_IMS_ v6_MT_OIP_disabled][${sites}]

    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc56_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc56_obj}    get_testcase_info
    ${ims_tc56_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc56_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc56_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc56_obj}    get_call_duration
    ${trace_inputs}    Call Method    ${ims_tc56_obj}    get_trace_inputs

    # # 1. Verify Sim card
    # ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    # ${device2_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]
    # Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    # Run Keyword If    '${device2_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_2]    ${devices_info}[device_2][sim][sim_slot]

    # # 2. Verify IMS registration for Devices
    # android_registration_check    ${devices_info}[device_1]
    # android_registration_check    ${devices_info}[device_2]

    android_display_number   ${devices_info}[device_1]

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration}   end_call_side=${devices_info}[device_1]    Notional_format=${False}
    ${end_time_stamp}      end_time_margin    60
    Sleep    1 minutes

    # 4. Collect Anritsu trace
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${trace_inputs}[Template]    ${devices_info}[device_1]     ${devices_info}[device_2]
    Should Be True    ${start_oesearch}
    log    Anritsu Trace Initiated: Successful
    ${sleep_time}    sleep_time_for    oesearch
    Sleep    ${sleep_time}
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download}

    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template]
    #${pcap_file_path}=    Set Variable     LOCAL_PATH_PLACEHOLDER
    ${val_result}    Validate Volte Call    IPV4_TO_IPV6_MO_OIR    a_msisdn=anonymous    b_msisdn=+${devices_info}[device_2][sim][msisdn]    a_imsi=${devices_info}[device_1][sim][imsi]    b_imsi=${devices_info}[device_1][sim][imsi]    clear_party=clear_B    pcap_file_path=${pcap_file_path}    a_msisdn_oir=+${devices_info}[device_1][sim][msisdn]
    Log               <table>${val_result}[0]</table>        html=True
    Log               <table>${val_result}[1]</table>        html=True
    Should Be True     ${val_result}[2]
