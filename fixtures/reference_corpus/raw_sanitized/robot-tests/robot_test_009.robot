
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
Library      ..LOCAL_PATH_PLACEHOLDER  ${MRF}
Library      ..LOCAL_PATH_PLACEHOLDER
Library    ..LOCAL_PATH_PLACEHOLDER


*** Test Cases ***
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

    2. login to nodes and scrap data
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
    ${df_html}    ${val_result}    Call Method    ${ims_tc41_obj}    get_validation_results    ${node_file_map}
    Log               <table>${df_html}</table>    html=True
    Should Be True    ${val_result}

Check_binaries
    # robot --outputdir "..LOCAL_PATH_PLACEHOLDER" --test "Check_binaries" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    To verify the version of the binaries running on the system
    [Tags]      APP_FTAS    TMSII00738768

    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[42]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc43_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc43_obj}    get_testcase_info
    ${vnf_info}         Call Method    ${ims_tc43_obj}    get_vnf_info
    ${vnf_val}         Call Method    ${ims_tc43_obj}    get_vnf_val
    ${ims_tc43_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc43_obj}    get_testcase_info

    # 2. login to nodes and scrap data
    ${nodeobj_trm}    Create_Object    SOURCE_NAME_PLACEHOLDER    ${Tastrm01}    Tastrm02
    ${scrap_data_trm}         Call Method    ${nodeobj_trm}    scrape_all_nodes    ${vnf_info}[commands][0]    ${tc_info}[tc_dir]
    ${output_text_dic_trm}    Call Method    ${nodeobj_trm}    load_all_output_texts    ${tc_info}[tc_dir]
    ${nodeobj_trh}    Create_Object    SOURCE_NAME_PLACEHOLDER    ${Tastrh01}    Tastrh02
    ${scrap_data_trh}         Call Method    ${nodeobj_trh}    scrape_all_nodes    ${vnf_info}[commands][0]    ${tc_info}[tc_dir]
    ${output_text_dic_trh}    Call Method    ${nodeobj_trh}    load_all_output_texts    ${tc_info}[tc_dir]
    Should Be True    ${scrap_data_trm} and ${scrap_data_trh}

    ${node_file_map}    Create Dictionary
    Set To Dictionary    ${node_file_map}    &{output_text_dic_trm}
    Set To Dictionary    ${node_file_map}    &{output_text_dic_trh}

    # 3. Validate — pass merged node_file_map to both Create Object and get_validation_results
    ${val_tc43_obj}    Create Object    SOURCE_NAME_PLACEHOLDER    ${node_file_map}    ${vnf_val}[static_test_data]    ${tc_info}[tc_dir]
    Call Method       ${val_tc43_obj}    load_testdata    messages    ${vnf_val}[messages]
    ${df_html}    ${val_result}    ${one_val_result}    Call Method    ${val_tc43_obj}    get_validation_results    ${node_file_map}
    Log               <table>${df_html}</table>    html=True
    Should Be True    ${val_result}


FTAS_software_verification
    # robot --outputdir "..LOCAL_PATH_PLACEHOLDER" --test "FTAS_software_verification" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    To verify the software version running on each VNF
    [Tags]      APP_CTAS    TMSII00738767

    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[43]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc44_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc44_obj}    get_testcase_info
    ${vnf_info}         Call Method    ${ims_tc44_obj}    get_vnf_info
    ${vnf_val}         Call Method    ${ims_tc44_obj}    get_vnf_val
    ${ims_tc44_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc44_obj}    get_testcase_info

    # 2. login to nodes and scrap data
    ${nodeobj_trm}    Create_Object    SOURCE_NAME_PLACEHOLDER    ${Tastrm01}    Tastrm02
    ${scrap_data_trm}         Call Method    ${nodeobj_trm}    scrape_all_nodes    ${vnf_info}[commands][0]    ${tc_info}[tc_dir]
    ${output_text_dic_trm}    Call Method    ${nodeobj_trm}    load_all_output_texts    ${tc_info}[tc_dir]
    ${nodeobj_trh}    Create_Object    SOURCE_NAME_PLACEHOLDER    ${Tastrh01}    Tastrh02
    ${scrap_data_trh}         Call Method    ${nodeobj_trh}    scrape_all_nodes    ${vnf_info}[commands][0]    ${tc_info}[tc_dir]
    ${output_text_dic_trh}    Call Method    ${nodeobj_trh}    load_all_output_texts    ${tc_info}[tc_dir]
    #Should Be True    ${scrap_data_trm} and ${scrap_data_trh}

    ${node_file_map}    Create Dictionary
    Set To Dictionary    ${node_file_map}    &{output_text_dic_trm}
    Set To Dictionary    ${node_file_map}    &{output_text_dic_trh}

    # 3. Validate — pass merged node_file_map to both Create Object and get_validation_results
    ${ims_tc44_obj}    Create Object    SOURCE_NAME_PLACEHOLDER    ${node_file_map}    ${vnf_val}[static_test_data]    ${tc_info}[tc_dir]
    Call Method       ${ims_tc44_obj}    load_testdata    messages    ${vnf_val}[messages]
    ${df_html}    ${val_result}    ${one_val_result}     Call Method    ${ims_tc44_obj}    get_validation_results    ${node_file_map}
    Log               <table>${df_html}</table>    html=True
    Should Be True    ${val_result}
