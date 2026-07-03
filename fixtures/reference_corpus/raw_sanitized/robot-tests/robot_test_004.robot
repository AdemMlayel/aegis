
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
Library    ..LOCAL_PATH_PLACEHOLDER    ${CMS}
Library      ..LOCAL_PATH_PLACEHOLDER
Library    ..LOCAL_PATH_PLACEHOLDER

*** Test Cases ***
Validate_alarms_in_CMS
    # robot --outputdir "..LOCAL_PATH_PLACEHOLDER" --test "Validate_alarms_in_CMS" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]   Verify CMS shall receive the alarms from VNF
    [Tags]      CMS-TC02    TMSII00577487

    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[22]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc22_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc22_obj}    get_testcase_info
    ${ims_tc22_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc22_obj}    get_testcase_info
    ${cms_info}         Call Method    ${ims_tc22_obj}    get_cms_info

    # 2 check service status
    ${service_status}     SOURCE_NAME_PLACEHOLDER.check_service_status    ${tc_info}[tc_output_dir]    ${cms_check_service_status}    ${cms_info}[site]     ${cms_info}[service]
    Should Be True    ${service_status}

    # ${service_status}     SOURCE_NAME_PLACEHOLDER.stop_service    ${tc_info}[tc_output_dir]    ${cms_stop_service}    ${cms_info}[site]     ${cms_info}[service]
    # Should Be True    ${service_status}

Validate_event_in_CMS
    # robot --outputdir "..LOCAL_PATH_PLACEHOLDER" --test "Validate_event_in_CMS" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    Verify CMS shall receive  the events from VNF
    [Tags]      CMS-TC03    TMSII00577488

    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[23]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc23_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc23_obj}    get_testcase_info
    ${ims_tc23_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc23_obj}    get_testcase_info
