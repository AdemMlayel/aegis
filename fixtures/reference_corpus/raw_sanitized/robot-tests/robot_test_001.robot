
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
Critical_call_test:International_format_from_Fixed_Residential.|fixed_to_fixed|Munich_to_Munich
    # robot --outputdir "..LOCAL_PATH_PLACEHOLDER:International_format_from_Fixed_Residential.|fixed_to_fixed|Munich_to_Munich" --test "Critical_call_test:International_format_from_Fixed_Residential.|fixed_to_fixed|Munich_to_Munich
    [Documentation]    To verify basic call from Fixed Residential IMS user in International format (004989243xxxx)
    [Tags]     Fixed_CC_26    TMSII00958168    

    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[15] 
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc15_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}     
    ${tc_info}         Call Method    ${ims_tc15_obj}    get_testcase_info
    ${ims_tc15_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]   
    ${tc_info}         Call Method    ${ims_tc15_obj}    get_testcase_info 
    ${devices_info}    Call Method    ${ims_tc15_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc15_obj}    get_call_duration 
    ${trace_inputs}    Call Method    ${ims_tc15_obj}    get_trace_inputs
    ${Pcap_validation_inputs}    Call Method    ${ims_tc15_obj}    get_pcap_vlaidation

Critical_call_test:National_format_from_Fixed_Residential|fixed_to_fixed|Munich_to_Munich
    # robot --outputdir "..LOCAL_PATH_PLACEHOLDER:National_format_from_Fixed_Residential|fixed_to_fixed|Munich_to_Munich" --test "Critical_call_test:National_format_from_Fixed_Residential|fixed_to_fixed|Munich_to_Munich
    [Documentation]    To verify basic call from Fixed Residential IMS user in National format (089243xx)
    [Tags]     Fixed_CC_25    TMSII00958167

    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[16] 
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc16_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}     
    ${tc_info}         Call Method    ${ims_tc16_obj}    get_testcase_info
    ${ims_tc16_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]   
    ${tc_info}         Call Method    ${ims_tc16_obj}    get_testcase_info 
    ${devices_info}    Call Method    ${ims_tc16_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc16_obj}    get_call_duration 
    ${trace_inputs}    Call Method    ${ims_tc16_obj}    get_trace_inputs
    ${Pcap_validation_inputs}    Call Method    ${ims_tc16_obj}    get_pcap_vlaidation

Critical_call_test:Local_format_from_Fixed_Residential|fixed_to_fixed|Munich_to_Munich
    # robot --outputdir "..LOCAL_PATH_PLACEHOLDER:Local_format_from_Fixed_Residential|fixed_to_fixed|Munich_to_Munich" --test "Critical_call_test:Local_format_from_Fixed_Residential|fixed_to_fixed|Munich_to_Munich
    [Documentation]    To verify basic call from Fixed Residential IMS user in Local format (243xxxx) 
    [Tags]     Fixed_CC_24    TMSII00958166

    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[17] 
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc17_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}     
    ${tc_info}         Call Method    ${ims_tc17_obj}    get_testcase_info
    ${ims_tc17_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]   
    ${tc_info}         Call Method    ${ims_tc17_obj}    get_testcase_info 
    ${devices_info}    Call Method    ${ims_tc17_obj}    get_devices_info
    ${call_duration}   Call Method    ${ims_tc17_obj}    get_call_duration 
    ${trace_inputs}    Call Method    ${ims_tc17_obj}    get_trace_inputs
    ${Pcap_validation_inputs}    Call Method    ${ims_tc17_obj}    get_pcap_vlaidation

