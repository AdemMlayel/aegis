
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
Library      ..LOCAL_PATH_PLACEHOLDER  ${MRF}
Library      ..LOCAL_PATH_PLACEHOLDER
Library    ..LOCAL_PATH_PLACEHOLDER



*** Test Cases ***

TAS_binaries_check
    # robot --outputdir "..LOCAL_PATH_PLACEHOLDER" --test "TAS_binaries_check" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    To verify the version of the binaries running on the system
    [Tags]      APP_CTAS    TMSII00787815

    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[18]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc18_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc18_obj}    get_testcase_info
    ${vnf_info}         Call Method    ${ims_tc18_obj}    get_vnf_info
    ${vnf_val}         Call Method    ${ims_tc18_obj}    get_vnf_val
    ${ims_tc18_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc18_obj}    get_testcase_info

    # 2. login to nodes and scrap data
    ${nodeobj_trm}    Create_Object    SOURCE_NAME_PLACEHOLDER    ${Tastrm01}    Tastrm01
    ${scrap_data_trm}         Call Method    ${nodeobj_trm}    scrape_all_nodes    ${vnf_info}[commands][0]    ${tc_info}[tc_dir]
    ${output_text_dic_trm}    Call Method    ${nodeobj_trm}    load_all_output_texts    ${tc_info}[tc_dir]
    ${nodeobj_trh}    Create_Object    SOURCE_NAME_PLACEHOLDER    ${Tastrh01}    Tastrh01
    ${scrap_data_trh}         Call Method    ${nodeobj_trh}    scrape_all_nodes    ${vnf_info}[commands][0]    ${tc_info}[tc_dir]
    ${output_text_dic_trh}    Call Method    ${nodeobj_trh}    load_all_output_texts    ${tc_info}[tc_dir]
    Should Be True    ${scrap_data_trm} and ${scrap_data_trh}

    ${node_file_map}    Create Dictionary
    Set To Dictionary    ${node_file_map}    &{output_text_dic_trm}
    Set To Dictionary    ${node_file_map}    &{output_text_dic_trh}

    # 3. Validate — pass merged node_file_map to both Create Object and get_validation_results
    ${val_tc18_obj}    Create Object    SOURCE_NAME_PLACEHOLDER    ${node_file_map}    ${vnf_val}[static_test_data]    ${tc_info}[tc_dir]
    Call Method       ${val_tc18_obj}    load_testdata    messages    ${vnf_val}[messages]
    ${df_html}    ${val_result}    Call Method    ${val_tc18_obj}    get_validation_results    ${node_file_map}
    Log               <table>${df_html}</table>    html=True
    Should Be True    ${val_result}



TAS_software_verification
    # robot --outputdir "..LOCAL_PATH_PLACEHOLDER" --test "TAS_software_verification" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    To verify the software version running on each VNF
    [Tags]      APP_CTAS    TMSII00787814

    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[19]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc19_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc19_obj}    get_testcase_info
    ${vnf_info}         Call Method    ${ims_tc19_obj}    get_vnf_info
    ${vnf_val}         Call Method    ${ims_tc19_obj}    get_vnf_val
    ${ims_tc19_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc19_obj}    get_testcase_info

    # 2. login to nodes and scrap data
    ${nodeobj_trm}    Create_Object    SOURCE_NAME_PLACEHOLDER    ${Tastrm01}    Tastrm01
    ${scrap_data_trm}         Call Method    ${nodeobj_trm}    scrape_all_nodes    ${vnf_info}[commands][0]    ${tc_info}[tc_dir]
    ${output_text_dic_trm}    Call Method    ${nodeobj_trm}    load_all_output_texts    ${tc_info}[tc_dir]
    ${nodeobj_trh}    Create_Object    SOURCE_NAME_PLACEHOLDER    ${Tastrh01}    Tastrh01
    ${scrap_data_trh}         Call Method    ${nodeobj_trh}    scrape_all_nodes    ${vnf_info}[commands][0]    ${tc_info}[tc_dir]
    ${output_text_dic_trh}    Call Method    ${nodeobj_trh}    load_all_output_texts    ${tc_info}[tc_dir]
    Should Be True    ${scrap_data_trm} and ${scrap_data_trh}

    ${node_file_map}    Create Dictionary
    Set To Dictionary    ${node_file_map}    &{output_text_dic_trm}
    Set To Dictionary    ${node_file_map}    &{output_text_dic_trh}

    # 3. Validate — pass merged node_file_map to both Create Object and get_validation_results
    ${val_tc19_obj}    Create Object    SOURCE_NAME_PLACEHOLDER    ${node_file_map}    ${vnf_val}[static_test_data]    ${tc_info}[tc_dir]
    Call Method       ${val_tc19_obj}    load_testdata    messages    ${vnf_val}[messages]
    ${df_html}    ${val_result}    ${one_val_result}     Call Method    ${val_tc19_obj}    get_validation_results    ${node_file_map}
    Log               <table>${df_html}</table>    html=True
    Should Be True    ${val_result}



Subscriber_status_in_TAS_VNF
    [Documentation]    APP_CTAS    TMSII00787816
    [Tags]      SOURCE_NAME_PLACEHOLDER

    # robot --variable sites:hamburg --outputdir "..LOCAL_PATH_PLACEHOLDER" --test "Subscriber_status_in_TAS_VNF" SOURCE_NAME_PLACEHOLDER.robot

    ${id}              Set Variable    ${vims_tcs}[Subscriber_status_in_TAS_VNF][${sites}]

    # 0. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[${id}]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc21_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc21_obj}    get_testcase_info
    ${vnf_info}         Call Method    ${ims_tc21_obj}    get_vnf_info
    ${vnf_val}         Call Method    ${ims_tc21_obj}    get_vnf_val
    ${ims_tc21_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc21_obj}    get_testcase_info
    ${devices_info}    Call Method    ${ims_tc21_obj}    get_devices_info

    # 1. Verify Sim card
    ${device1_sim_ok}=     android_verify_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]
    Run Keyword If    '${device1_sim_ok}' == 'False'    android_set_active_sim_slot    ${devices_info}[device_1]    ${devices_info}[device_1][sim][sim_slot]

    # 2. Verify IMS registration for Devices
    android_registration_check    ${devices_info}[device_1]
    ${success_message}=    Set Variable   [✓] Registration Check
    Log To Console    ${success_message}

    # 3. login to nodes and scrap data
    ${nodeobj_trh}    Create_Object    SOURCE_NAME_PLACEHOLDER    ${Tastrh01_app}    Tastrh01_app
    ${scrap_data_trh}         Call Method    ${nodeobj_trh}    scrape_all_nodes    ${vnf_info}[commands][0]    ${tc_info}[tc_dir]
    ${output_text_dic_trh}    Call Method    ${nodeobj_trh}    load_all_output_texts    ${tc_info}[tc_dir]
    Should Be True  ${scrap_data_trh}
    ${node_file_map}    Create Dictionary
    Set To Dictionary    ${node_file_map}    &{output_text_dic_trh}

    # 4. Validate — pass merged node_file_map to both Create Object and get_validation_results
    ${ims_tc21_obj}    Create Object    SOURCE_NAME_PLACEHOLDER    ${node_file_map}    ${vnf_val}[static_test_data]    ${tc_info}[tc_dir]
    Call Method       ${ims_tc21_obj}    load_testdata    messages    ${vnf_val}[messages]
    ${df_html}    ${val_result}     ${val_result_2}     Call Method    ${ims_tc21_obj}    get_validation_results    ${node_file_map}
    Log               <table>${df_html}</table>    html=True
    Should Be True    ${val_result_2}




TAS_system_overload_status
    # robot --outputdir "..LOCAL_PATH_PLACEHOLDER" --test "TAS_system_overload_status" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    To demonstrate that the overload status of each VNF can be queried
    [Tags]      APP_TAS    TMSII00787817

    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[40]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc41_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc41_obj}    get_testcase_info
    ${vnf_info}         Call Method    ${ims_tc41_obj}    get_vnf_info
    ${vnf_val}         Call Method    ${ims_tc41_obj}    get_vnf_val
    ${ims_tc41_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc41_obj}    get_testcase_info

    # 2. login to nodes and scrap data
    ${nodeobj_trm}    Create_Object    SOURCE_NAME_PLACEHOLDER    ${Uagtrm01}    Tastrm01
    ${scrap_data_trm}         Call Method    ${nodeobj_trm}    scrape_all_nodes    ${vnf_info}[commands][0]    ${tc_info}[tc_dir]
    ${output_text_dic_trm}    Call Method    ${nodeobj_trm}    load_all_output_texts    ${tc_info}[tc_dir]
    ${nodeobj_trh}    Create_Object    SOURCE_NAME_PLACEHOLDER    ${Uagtrh01}    Tastrh01
    ${scrap_data_trh}         Call Method    ${nodeobj_trh}    scrape_all_nodes    ${vnf_info}[commands][0]    ${tc_info}[tc_dir]
    ${output_text_dic_trh}    Call Method    ${nodeobj_trh}    load_all_output_texts    ${tc_info}[tc_dir]
    Should Be True    ${scrap_data_trh}    #${scrap_data_trm} and ${scrap_data_trh}

    ${node_file_map}    Create Dictionary
    Set To Dictionary    ${node_file_map}    &{output_text_dic_trm}
    Set To Dictionary    ${node_file_map}    &{output_text_dic_trh}

    # 3. Validate — pass merged node_file_map to both Create Object and get_validation_results
    ${ims_tc41_obj}    Create Object    SOURCE_NAME_PLACEHOLDER    ${node_file_map}    ${vnf_val}[static_test_data]    ${tc_info}[tc_dir]
    Call Method       ${ims_tc41_obj}    load_testdata    messages    ${vnf_val}[messages]
    ${df_html}    ${val_result}    ${one_val_result}    Call Method    ${ims_tc41_obj}    get_validation_results    ${node_file_map}
    Log               <table>${df_html}</table>    html=True
    Should Be True    ${val_result}

System_overload_status
    # robot --outputdir "..LOCAL_PATH_PLACEHOLDER" --test "System_overload_status" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    To demonstrate that the overload status of each VNF can be queried
    [Tags]      APP_FTAS    TMSII00738769

    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[41]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc41_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc41_obj}    get_testcase_info
    ${vnf_info}         Call Method    ${ims_tc41_obj}    get_vnf_info
    ${vnf_val}         Call Method    ${ims_tc41_obj}    get_vnf_val
    ${ims_tc41_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc41_obj}    get_testcase_info

    # 2. login to nodes and scrap data
    ${nodeobj_trm}    Create_Object    SOURCE_NAME_PLACEHOLDER    ${Uagtrm01}    Tastrm02
    ${scrap_data_trm}         Call Method    ${nodeobj_trm}    scrape_all_nodes    ${vnf_info}[commands][0]    ${tc_info}[tc_dir]
    ${output_text_dic_trm}    Call Method    ${nodeobj_trm}    load_all_output_texts    ${tc_info}[tc_dir]
    ${nodeobj_trh}    Create_Object    SOURCE_NAME_PLACEHOLDER    ${Uagtrh01}    Tastrh02
    ${scrap_data_trh}         Call Method    ${nodeobj_trh}    scrape_all_nodes    ${vnf_info}[commands][0]    ${tc_info}[tc_dir]
    ${output_text_dic_trh}    Call Method    ${nodeobj_trh}    load_all_output_texts    ${tc_info}[tc_dir]
    Should Be True    ${scrap_data_trm} and ${scrap_data_trh}

    ${node_file_map}    Create Dictionary
    Set To Dictionary    ${node_file_map}    &{output_text_dic_trm}
    Set To Dictionary    ${node_file_map}    &{output_text_dic_trh}

    # 3. Validate — pass merged node_file_map to both Create Object and get_validation_results
    ${ims_tc41_obj}    Create Object    SOURCE_NAME_PLACEHOLDER    ${node_file_map}    ${vnf_val}[static_test_data]    ${tc_info}[tc_dir]
    Call Method       ${ims_tc41_obj}    load_testdata    messages    ${vnf_val}[messages]
    ${df_html}    ${val_result}    ${val_result}    Call Method    ${ims_tc41_obj}    get_validation_results    ${node_file_map}
    Log               <table>${df_html}</table>    html=True
    Should Be True    ${val_result}
