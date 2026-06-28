
*** Settings ***
# Config files
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

*** Test Cases ***
Basic_VoLTE:_A_and_B_VoLTE,_B_releases._A_dials_international_format.|Android_to_Android|Munich_to_Munich
    # robot --outputdir "..LOCAL_PATH_PLACEHOLDER:_A_and_B_VoLTE,_B_releases._A_dials_international_format.|Android_to_Android|Munich_to_Munich" --test "Basic_VoLTE:_A_and_B_VoLTE,_B_releases._A_dials_international_format.|Android_to_Android|Munich_to_Munich" SOURCE_NAME_PLACEHOLDER.robot
    [Documentation]    IMS Call between Munich <-> Munich  to verify the call with International format dialing
    [Tags]     mVoLTE CC_TC10    TMSII00532817    

    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[6] 
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc6_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}     
    ${tc_info}         Call Method    ${ims_tc6_obj}    get_testcase_info
    ${ims_tc6_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]   
    ${tc_info}         Call Method    ${ims_tc6_obj}    get_testcase_info 
    ${devices_info}    Call Method    ${ims_tc6_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc6_obj}    get_call_duration 
    ${trace_inputs}    Call Method    ${ims_tc6_obj}    get_trace_inputs
    ${Pcap_validation_inputs}    Call Method    ${ims_tc6_obj}    get_pcap_vlaidation

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1] 
    android_registration_check    ${devices_info}[device_2]
    ${success_message}=    Set Variable   [✓] Registration Check : Successful 
    Log To Console    ${success_message}

    # 3. Execute VoLTE call scenario
    ${start_time_stamp}    start_time_margin    60
    execute_android_call_session_ab   ${devices_info}[device_1]    ${devices_info}[device_2]    ${call_duration} 
    ${end_time_stamp}      end_time_margin    60  
    Sleep    1 minutes
    ${success_message}=    Set Variable   [✓] Test Execution : Successful 
    Log To Console    ${success_message}

    # 4. Collect Anritsu trace    
    ${initialize_anritsu_driver}    initialize_anritsu_driver    ${tc_info}[identifier]    ${tc_info}[tc_dir]    
    Should Be True    ${initialize_anritsu_driver}
    ${start_oesearch}    start_oesearch_NewUi    ${Oesearch_NewUi}    ${start_time_stamp}    ${end_time_stamp}    ${devices_info}[device_1][sims][sim_slot_1]     ${devices_info}[device_2][sims][sim_slot_1]     ${trace_inputs}[Template]      
    Should Be True    ${start_oesearch} 
    log    Anritsu Trace Initiated: Successful  
    ${sleep_time}    sleep_time_for    oesearch 
    Sleep    ${sleep_time} 
    ${download_oesearch_pcap}    download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${Oesearch_pcap_download} 
    ${success_message}=    Set Variable   [✓] Pcap Downloaded Successful 
    Log To Console    ${success_message}

    # 5. Validate PCAP file
    ${pcap_file_path}    get_pcap_path    ${trace_inputs}[Template] 
    ${volte_tc1_obj}    Create Object    SOURCE_NAME_PLACEHOLDER    ${pcap_file_path}    ${Pcap_validation_inputs}[filter]    ${Pcap_validation_inputs}[static_test_data]    ${tc_info}[tc_dir]           
    ${df_html}=       Call Method    ${volte_tc1_obj}   get_dynamic_ips_results_ab    ${Pcap_validation_inputs}[static_test_data]      
    Log               <table>${df_html}</table>        html=True 
    Call Method       ${volte_tc1_obj}   load_testdata     messages    ${Pcap_validation_inputs}[messages]  
    ${df_html}   ${val_result}           Call Method    ${volte_tc1_obj}   get_validation_results
    Log               <table>${df_html}</table>        html=True
    Call Method       ${volte_tc1_obj}   load_testdata        seq_messages    ${Pcap_validation_inputs}[a_sequence_messages]     
    ${a_seq_val_result}     ${message}        ${df_html}=        Call Method    ${volte_tc1_obj}   get_validate_seq_results    ${Pcap_validation_inputs}[a_sequence_criteria]
    Log               <table>${df_html}</table>        html=True 
    Call Method       ${volte_tc1_obj}   load_testdata        seq_messages    ${Pcap_validation_inputs}[b_sequence_messages]     
    ${b_seq_val_result}    ${message}    ${df_html} =        Call Method    ${volte_tc1_obj}   get_validate_seq_results    ${Pcap_validation_inputs}[b_sequence_criteria]        
    Log               <table>${df_html}</table>        html=True  
    @{result_list}=    Create List    ${val_result}    ${a_seq_val_result}     ${b_seq_val_result}
    ${result_list_val}    Evaluate    all(${result_list})
    Should Be True    ${result_list_val}     
    ${success_message}=    Set Variable     [✓]  Pcap Validation: Successful
    Log To Console    ${success_message}