
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

Performance_management_Statistics_retrieval
    # robot --outputdir "..LOCAL_PATH_PLACEHOLDER" --test "Performance_management_Statistics_retrieval" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    Verify Performance Statistics retrieval in MRF
    [Tags]      vIMS_MRF_014    TMSII00596730

    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[12]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc9_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc9_obj}    get_testcase_info
    ${ims_tc9_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc9_obj}    get_testcase_info

    # 2. Retrive statistics file from MRF GUI
    ${retrieved_statistics}    SOURCE_NAME_PLACEHOLDER.retrieve_statistics        ${tc_info}[tc_dir]     ${retrieve_statistics_path}
    Should Be True    ${retrieved_statistics}

Performance_management_Statistics_configuration
    # robot --outputdir "..LOCAL_PATH_PLACEHOLDER" --test "Performance_management_Statistics_configuration" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    Verify Performance Statistics retrieval in MRF
    [Tags]      vIMS_MRF_015    TMSII00596731

    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[13]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc10_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc10_obj}    get_testcase_info
    ${ims_tc10_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc10_obj}    get_testcase_info

    # 2. Retrive statistics file from MRF GUI
    ${configurate_statistics}    SOURCE_NAME_PLACEHOLDER.configurate_statistics        ${tc_info}[tc_dir]     ${configurate_statistics_path}
    Should Be True    ${configurate_statistics}

MRF_Software_Level
    # robot --outputdir "..LOCAL_PATH_PLACEHOLDER" --test "MRF_Software_Level" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    Verify Performance Statistics retrieval in MRF
    [Tags]      vIMS_MRF_023    TMSII00596739

    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[14]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc11_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc11_obj}    get_testcase_info
    ${ims_tc11_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc11_obj}    get_testcase_info
    ${mrf_validation}         Call Method    ${ims_tc11_obj}    get_mrf_validation


    # 2. Retrive statistics file from MRF GUI
    ${show_software_version}    SOURCE_NAME_PLACEHOLDER.show_software_version       ${tc_info}[tc_dir]     ${show_software_version_path}    ${mrf_validation}[fieldsforpresence]
    Should Be True    ${show_software_version}

MRF_Licensing
    # robot --outputdir "..LOCAL_PATH_PLACEHOLDER" --test "MRF_Licensing" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    Verify Performance Statistics retrieval in MRF
    [Tags]      vIMS_MRF_023    TMSII00596740

    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[15]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc12_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc12_obj}    get_testcase_info
    ${ims_tc12_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc12_obj}    get_testcase_info
    ${mrf_validation}         Call Method    ${ims_tc12_obj}    get_mrf_validation


    # 2. Retrive statistics file from MRF GUI
    ${show_mrf_licensing}    SOURCE_NAME_PLACEHOLDER.show_mrf_licensing      ${tc_info}[tc_dir]     ${show_mrf_licensing_path}    ${mrf_validation}[fieldsforpresence]
    Should Be True    ${show_mrf_licensing}

MRF_Node_Configuration
    # robot --outputdir "..LOCAL_PATH_PLACEHOLDER" --test "MRF_Node_Configuration" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    Verify Performance Statistics retrieval in MRF
    [Tags]      vIMS_MRF_027    TMSII00596743

    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[16]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc13_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc13_obj}    get_testcase_info
    ${ims_tc13_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc13_obj}    get_testcase_info
    ${mrf_validation}         Call Method    ${ims_tc13_obj}    get_mrf_validation

    # 2. Retrive statistics file from MRF GUI
    ${show_mrf_node_Configuration}    SOURCE_NAME_PLACEHOLDER.show_mrf_node_configuration      ${tc_info}[tc_dir]     ${show_mrf_node_Configuration_path}    ${mrf_validation}[fieldsforpresence]
    Should Be True    ${show_mrf_node_Configuration}

MRF_Node_Service_Mode
    # robot --outputdir "..LOCAL_PATH_PLACEHOLDER" --test "MRF_Node_Service_Mode" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    Verify Performance Statistics retrieval in MRF
    [Tags]      vIMS_MRF_028    TMSII00596744

    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[17]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc14_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc14_obj}    get_testcase_info
    ${ims_tc14_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc14_obj}    get_testcase_info
    ${mrf_validation}         Call Method    ${ims_tc14_obj}    get_mrf_validation

    # 2. Retrive statistics file from MRF GUI
    ${mrf_node_service_node}    SOURCE_NAME_PLACEHOLDER.mrf_node_service_node     ${tc_info}[tc_dir]     ${mrf_node_service_node_path}    ${mrf_validation}[service_mode]
    Should Be True    ${mrf_node_service_node}
