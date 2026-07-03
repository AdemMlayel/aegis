
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
Library    ..LOCAL_PATH_PLACEHOLDER    ${CMS}
Library      ..LOCAL_PATH_PLACEHOLDER
Library    ..LOCAL_PATH_PLACEHOLDER

*** Test Cases ***

Validating_GUI_access_to_CMS
    # robot --outputdir "..LOCAL_PATH_PLACEHOLDER" --test "Validating_GUI_access_to_CMS" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    Verify CMS GUI can be accessed via web browser
    [Tags]      mCMS_AWS_TC01    TMSII01356383

    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[21]
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc21_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}
    ${tc_info}         Call Method    ${ims_tc21_obj}    get_testcase_info
    ${ims_tc21_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]
    ${tc_info}         Call Method    ${ims_tc21_obj}    get_testcase_info

    # 2. login to cms Server
    ${cms_access}    SOURCE_NAME_PLACEHOLDER.initialize_cms_driver      ${tc_info}[tc_dir]
    Should Be True    ${cms_access}
