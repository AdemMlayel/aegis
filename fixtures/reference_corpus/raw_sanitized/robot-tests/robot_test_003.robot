
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
#Library    ..LOCAL_PATH_PLACEHOLDER

*** Test Cases ***

Export_of_cell_data_from_CRDL
    # robot --outputdir "..LOCAL_PATH_PLACEHOLDER" --test "Export_of_cell_data_from_CRDL" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]    EMER_LBS_154    TMSII01093119  
    [Tags]      SOURCE_NAME_PLACEHOLDER  

    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[29] 
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc36_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}     
    ${tc_info}         Call Method    ${ims_tc36_obj}    get_testcase_info
    ${ims_tc36_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]   
    ${tc_info}         Call Method    ${ims_tc36_obj}    get_testcase_info 
    ${lbs_info}         Call Method    ${ims_tc36_obj}    get_lbs_info 

    # 2. login to nodes and scrap data
    ${nodeobj_lbs}    Create_Object    SOURCE_NAME_PLACEHOLDER    ${lbs} 
    ${network_records}=     Create List    2G_export    3G_export    4G_export    5G_export          
    ${scrap_data_lbs}         Call Method    ${nodeobj_lbs}    fetch_CRDL_export_file    ${lbs_info}[commands][0]    ${tc_info}[tc_dir]     network_record=${network_records}
    Should Not Be Empty    ${scrap_data_lbs}    

5G:Administration_in _BS-Portal_Web_GUI
    # robot --outputdir "..LOCAL_PATH_PLACEHOLDER:Administration_in _BS-Portal_Web_GUI" --test "5G:Administration_in _BS-Portal_Web_GUI" SOURCE_NAME_PLACEHOLDER.robot

    [Documentation]     EMER_LBS_125    TMSII01525132    TMSII01005510 
    [Tags]      SOURCE_NAME_PLACEHOLDER 

    # 1. Retrieve test data from MongoDB
    &{tc_filter}       Create Dictionary    identifier=${ims_testcase_tmsids}[76] 
    ${test_data}       get_document    ${ims_collection}    ${tc_filter}
    ${ims_tc77_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${False}     
    ${tc_info}         Call Method    ${ims_tc77_obj}    get_testcase_info
    ${ims_tc77_obj}     Create Object    SOURCE_NAME_PLACEHOLDER    ${test_data}    ${True}    ${tc_info}[tc_output_dir]   
    ${tc_info}         Call Method    ${ims_tc77_obj}    get_testcase_info 
    ${lbs_info}         Call Method    ${ims_tc77_obj}    get_lbs_info 

    # 2. login to nodes and scrap data
    ${nodeobj_lbs}    Create_Object    SOURCE_NAME_PLACEHOLDER    ${lbs} 

    # 3. modify one record from lbs portal 
    ${nodeobj_lbs}    ${original_values}         Call Method    ${nodeobj_lbs}    modify_data_from_lbsPortal      ${tc_info}[identifier]    ${tc_info}[tc_dir]   ${lbs_info}[5G_record_param]    ${lbs_info}[record_param_to_modify]   record_type=5G    
    Should Be True    ${nodeobj_lbs}
    
    # 4. fetch record  
    ${csv_file_path}         Call Method    ${nodeobj_lbs}    fetch_CRDL_export_file    ${lbs_info}[commands][0]    ${tc_info}[tc_dir]     network_record=5G_export
    should Not Be Empty    ${csv_file_path}

    # 5.
    ${is_record_in_csv}      Call Method    ${nodeobj_lbs}    is_record_in_csv_export_file    ${csv_file_path}    ${lbs_info}[record_param_to_modify]  
    Should Be True    ${is_record_in_csv}

    ${changes_reversed}      Call Method    ${nodeobj_lbs}    reset_data_from_lbsPortal_changes    ${tc_info}[identifier]    ${tc_info}[tc_dir]   ${lbs_info}[5G_record_param]    ${lbs_info}[record_param_to_modify]   record_type=5G  
    Should Be True    ${changes_reversed}