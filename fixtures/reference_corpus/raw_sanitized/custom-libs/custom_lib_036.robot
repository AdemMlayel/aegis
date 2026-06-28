*** Settings ***
# Config files
Variables    ..LOCAL_PATH_PLACEHOLDER
Variables    ..LOCAL_PATH_PLACEHOLDER

# Resource files
Resource     ..LOCAL_PATH_PLACEHOLDER
Resource     ..LOCAL_PATH_PLACEHOLDER

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

*** Keywords ***
android_network_mode_check
    [Arguments]    ${DEVICE}    ${NETOWRK} 
    [Documentation]    Checks if used notwork is correct     

    log    ${DEVICE} 
    ${session_start}=    Evaluate    "\\n\\033[32m[CHECK NETOWRK] ${DEVICE}[device_serial] (${DEVICE}[device_brand])\\033[0m"
    Log To Console    ${session_start}
    Log    Starting Network check for device ${DEVICE}[device_serial]    INFO

    ${network_check}=    check_android_network_mode    ${DEVICE}[device_serial]    ${DEVICE}[device_brand]    ${NETOWRK}        

    IF    ${network_check}
        ${success_msg}=    Evaluate    "\\033[32m[✓ SUCCESS] Device ${DEVICE}[device_serial] is connected to network : ${NETOWRK}\\033[0m"
        Log To Console    ${success_msg}
        Log    IMS registration verified for ${DEVICE}[device_serial]    INFO
    ELSE
        ${failure_msg}=    Evaluate    "\\033[31m[✗ FAILURE] Device ${DEVICE}[device_serial] is not connected to network : ${NETOWRK}\\033[0m"
        Log To Console    ${failure_msg}
        Log    IMS registration check failed for ${DEVICE}[device_serial]    WARN
    END

    Should Be True    ${network_check}    

iphone_registration_check

    [Documentation]    Checks IMS Registration status on Android device

    ${registered}=    Check Registration Status iphone

    IF    ${registered}
        ${success_msg}=    Evaluate    "\\033[32m[✓ SUCCESS] Device  is registered\\033[0m"
        Log To Console    ${success_msg}
    ELSE
        ${failure_msg}=    Evaluate    "\\033[31m[✗ FAILURE] Device $is NOT registered\\033[0m"
        Log To Console    ${failure_msg}
    END

    Should Be True    ${registered}

android_registration_check
    [Arguments]    ${DEVICE}
    [Documentation]    Checks IMS Registration status on Android device

    ${session_start}=    Evaluate    "\\n\\033[32m[CHECK REGISTRATION] ${DEVICE}[device_serial] (${DEVICE}[device_brand])\\033[0m"
    Log To Console    ${session_start}
    Log    Starting IMS registration check for device ${DEVICE}[device_serial]    INFO

    ${registered}=    check_android_registration_status    ${DEVICE}[device_serial]    ${DEVICE}[device_brand]

    IF    ${registered}
        ${success_msg}=    Evaluate    "\\033[32m[✓ SUCCESS] Device ${DEVICE}[device_serial] is registered\\033[0m"
        Log To Console    ${success_msg}
        Log    IMS registration verified for ${DEVICE}[device_serial]    INFO
    ELSE
        ${failure_msg}=    Evaluate    "\\033[31m[✗ FAILURE] Device ${DEVICE}[device_serial] is NOT registered\\033[0m"
        Log To Console    ${failure_msg}
        Log    IMS registration check failed for ${DEVICE}[device_serial]    WARN
    END

    Should Be True    ${registered}
android_ip_version_check
    [Arguments]    ${DEVICE}    ${EXPECTED_IP_VERSION}
    [Documentation]

    ${session_start}=    Evaluate    "\\n\\033[32m[CHECK IP VERSION] ${DEVICE}[device_serial] (${DEVICE}[device_brand])\\033[0m"
    Log To Console    ${session_start}
    Log    Starting IP version check for device ${DEVICE}[device_serial]    INFO

    ${ip_version}=    check_android_ip_version    ${DEVICE}[device_serial]    ${DEVICE}[device_brand]    ${EXPECTED_IP_VERSION}
    IF    ${ip_version}
        ${pass_message}=    Evaluate    "\\033[32m[✓ SUCCESS] Device ${DEVICE}[device_serial] is using IP version ${EXPECTED_IP_VERSION}\\033[0m"    
        Log To Console    ${pass_message} 
    ELSE     
        ${fail_message}=    Evaluate     "\\033[31m[✗ FAILURE] Device ${DEVICE}[device_serial] is NOT using IP version ${EXPECTED_IP_VERSION}\\033[0m"
        Log To Console    ${fail_message}    
    END

    Should Be True    ${ip_version}
         

execute_fixed_android_call_session_ab
    [Arguments]    ${SIP_SERVER}     ${AUT_SERVER}   ${DEVICE_B}    ${call_duration}    ${tc_dir}    ${scenario_path}         
    [Documentation]    Initiates a call from FIXED A to android Device B
     
    ${session_start}=    Evaluate    "\\n\\033[32m[CALL SESSION - Fixed to Android] ${SIP_SERVER}[sip_server_ip] -> ${DEVICE_B}[device_serial] (${DEVICE_B}[device_brand]) | Duration: ${call_duration}s\\033[0m"
    Log To Console    ${session_start}
    Log Many    Starting call session:  ${SIP_SERVER}[sip_server_ip] to ${DEVICE_B}[device_serial]    INFO
    
    # Place call from Fixed A to Device B and handel the call
    ${step1}=    Evaluate    "\\033[32m[1/3] Initiating call from sipp...\\033[0m"
    Log To Console    ${step1}
    Initiate_sipp_call    ${SIP_SERVER}[sip_server_ip]    ${SIP_SERVER}[sip_server_port]    ${AUT_SERVER}[aut_server_ip]    ${AUT_SERVER}[aut_server_port]    ${DEVICE_B}     ${tc_dir}    ${scenario_path}            
    
    ${step3}=    Evaluate    "\\033[32m[3/3] Call Terminated...\\033[0m"
    Log To Console    ${step3}

execute_android_call_session_ab   
    [Arguments]    ${DEVICE_A}    ${DEVICE_B}    ${call_duration}     
    [Documentation]    Initiates a call from android Device A to android Device B
     
    ${session_start}=    Evaluate    "\\n\\033[32m[CALL SESSION - Android to Android] ${DEVICE_A}[device_serial] (${DEVICE_A}[device_brand]) -> ${DEVICE_B}[device_serial] (${DEVICE_B}[device_brand]) | Duration: ${call_duration}s\\033[0m"
    Log To Console    ${session_start}
    Log    Starting call session: ${DEVICE_A}[device_serial] to ${DEVICE_B}[device_serial]    INFO
    

    ${step1}=    Evaluate    "\\033[32m[1/3] Initiating call from Device A...\\033[0m"
    Log To Console    ${step1}
    ${call_initiated_result}=    initiate_android_call    
    ...    ${DEVICE_A}[device_serial]    
    ...    ${DEVICE_A}[device_brand]    
    ...    ${DEVICE_B}[sims][sim_slot_1][msisdn]
    Should Be Equal As Integers    0    ${call_initiated_result}
    Sleep    5


    ${step2}=    Evaluate    "\\033[32m[2/3] Answering call on Device B...\\033[0m"
    Log To Console    ${step2}
    ${call_answered_result}=    answer_android_incoming_call    
    ...    ${DEVICE_B}[device_serial]    
    ...    ${DEVICE_B}[device_brand]    
    ...    ${call_duration}
    ...    ${False}
    Should Be Equal As Integers    0    ${call_answered_result}


    ${step3}=    Evaluate    "\\033[32m[3/3] Terminating call...\\033[0m"
    Log To Console    ${step3}
    ${call_terminated_result}=    end_android_active_call 
    ...    ${DEVICE_A}[device_serial]        
    ...    ${DEVICE_A}[device_brand]
    Should Be Equal As Integers    0    ${call_terminated_result}
    Log    Call session completed successfully    INFO

execute_iphone_android_call_session_ab
    [Arguments]    ${DEVICE_A}    ${DEVICE_B}    ${call_duration}     
    [Documentation]    Initiates a call from android Device A to android Device B
    
    ${session_start}=    Evaluate    "\\n\\033[32m[CALL SESSION - IPhone to Android] ${DEVICE_A}[device_serial] (${DEVICE_A}[device_brand]) -> ${DEVICE_B}[device_serial] (${DEVICE_B}[device_brand]) | Duration: ${call_duration}s\\033[0m"
    Log To Console    ${session_start}
    Log    Starting call session: ${DEVICE_A}[device_serial] to ${DEVICE_B}[device_serial]    INFO

    # Place call from Device A to Device B
    ${step1}=    Evaluate    "\\033[32m[1/3] Initiating call from Device A...\\033[0m"
    Log To Console    ${step1}
    Initiate Call from Real Device Iphone 
    ...    ${DEVICE_B}[sims][sim_slot_1][msisdn] 
    ...    ${DEVICE_A}[device_serial]  
    ...    ${DEVICE_A}[device_brand]         
    
    Sleep    5
    ${step2}=    Evaluate    "\\033[32m[2/3] Answering call on Device B...\\033[0m"
    Log To Console    ${step2}
    answer_android_incoming_call    
    ...    ${DEVICE_B}[device_serial]    
    ...    ${DEVICE_B}[device_brand]    
    ...    ${call_duration}
    ...    ${False}     
    
    ${step3}=    Evaluate    "\\033[32m[3/3] Terminating call...\\033[0m"
    Log To Console    ${step3}
    Terminate Active Call Iphone 
    ...    ${DEVICE_A}[device_serial]        
    ...    ${DEVICE_A}[device_brand]
    
    Log    Call session completed successfully    INFO


android_set_ip_version
    [Arguments]    ${DEVICE}    ${EXPECTED_IP_VERSION}
    [Documentation]

    ${session_start}=    Evaluate    "\\n\\033[32m[set_ip_version] ${DEVICE}[device_serial] (${DEVICE}[device_brand]) -> ${EXPECTED_IP_VERSION} \\033[0m"
    Log To Console    ${session_start}


    ${ip_version}=    set_android_ip_version     ${DEVICE}[device_serial]    ${DEVICE}[device_brand]    ${EXPECTED_IP_VERSION}
    IF    ${ip_version}
        ${success_msg}=    Evaluate    "\\n\\033[32m[✓ SUCCESS] Device ${DEVICE}[device_serial] is on ${EXPECTED_IP_VERSION}\\033[0m"
        Log To Console    ${success_msg}
        Log    IMS registration verified for ${DEVICE}[device_serial]    INFO
    ELSE
        ${failure_msg}=    Evaluate    "\\n\\033[31m[✗ FAILURE] Device ${DEVICE}[device_serial] is NOT on ${EXPECTED_IP_VERSION}\\033[0m"
        Log To Console    ${failure_msg}
        Log    IMS registration check failed for ${DEVICE}[device_serial]    WARN
    END
    
    
fixedIms_registration
    [Arguments]    ${SIP_SERVER}    ${tc_dir}    ${scenario_path}
    [Documentation]

    ${session_start}=    Evaluate    "\\n\\033[32m[Fixed IMS-registration ${SIP_SERVER}[sip_server_ip]\\033[0m"
    Log To Console    ${session_start}
    
    ${registered}=    sip_registration    ${SIP_SERVER}[sip_server_ip]    ${SIP_SERVER}[sip_server_port]    ${tc_dir}    ${scenario_path} 

    IF    ${registered}
        ${pass_message}=    Evaluate    "\\033[32m[✓ SUCCESS] Registration : Sipp Server (${SIP_SERVER}[sip_server_ip]:${SIP_SERVER}[sip_server_port]) \\033[0m"    
        Log To Console    ${pass_message} 
    ELSE     
        ${fail_message}=    Evaluate     "\\033[31m[✗ FAILURE] Registration Failed : Sipp Server (${SIP_SERVER}[sip_server_ip]:${SIP_SERVER}[sip_server_port]) \\033[0m"
        Log To Console    ${fail_message}    
    END          
    


