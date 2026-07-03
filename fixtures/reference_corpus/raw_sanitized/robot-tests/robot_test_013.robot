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
    [Arguments]    ${DEVICE}    ${NETWORK}
    [Documentation]    Checks if the device is connected to the expected network mode.
    ...    ${DEVICE}: The Android device dictionary.
    ...    ${NETWORK}: The expected network mode to verify.

    ${session_start}=    Evaluate    "\\n\\033[35m[CHECK NETWORK] ${DEVICE}[device_serial] (${DEVICE}[device_brand])\\033[0m"
    Log To Console    ${session_start}
    Log    Starting network mode check for device ${DEVICE}[device_serial]    INFO

    ${network_check}=    check_android_network_mode    ${DEVICE}[device_serial]    ${DEVICE}[device_brand]    ${NETWORK}

    IF    ${network_check}
        ${success_msg}=    Evaluate    "\\033[32m[ SUCCESS] Device ${DEVICE}[device_serial] is connected to network: ${NETWORK}\\033[0m"
        Log To Console    ${success_msg}
        Log    Network mode verified for ${DEVICE}[device_serial]: ${NETWORK}    INFO
    ELSE
        ${failure_msg}=    Evaluate    "\\033[31m[ FAILURE] Device ${DEVICE}[device_serial] is NOT connected to network: ${NETWORK}\\033[0m"
        Log To Console    ${failure_msg}
        Log    Network mode check failed for ${DEVICE}[device_serial]: expected ${NETWORK}    WARN
    END

    Should Be True    ${network_check}


iphone_registration_check
    [Documentation]    Checks IMS registration status on iPhone device.

    ${session_start}=    Evaluate    "\\n\\033[35m[CHECK REGISTRATION] iPhone\\033[0m"
    Log To Console    ${session_start}
    Log    Starting IMS registration check for iPhone    INFO

    ${registered}=    Check Registration Status iphone

    IF    ${registered}
        ${success_msg}=    Evaluate    "\\033[32m[ SUCCESS] iPhone is registered\\033[0m"
        Log To Console    ${success_msg}
        Log    IMS registration verified for iPhone    INFO
    ELSE
        ${failure_msg}=    Evaluate    "\\033[31m[ FAILURE] iPhone is NOT registered\\033[0m"
        Log To Console    ${failure_msg}
        Log    IMS registration check failed for iPhone    WARN
    END

    Should Be True    ${registered}


android_registration_check
    [Arguments]    ${DEVICE}
    [Documentation]    Checks IMS registration status on Android device.
    ...    ${DEVICE}: The Android device dictionary.

    ${session_start}=    Evaluate    "\\n\\033[35m[CHECK REGISTRATION] ${DEVICE}[device_serial] (${DEVICE}[device_brand])\\033[0m"
    Log To Console    ${session_start}
    Log    Starting IMS registration check for device ${DEVICE}[device_serial]    INFO

    ${registered}=    check_android_registration_status    ${DEVICE}[device_serial]    ${DEVICE}[device_brand]

    IF    ${registered}
        ${success_msg}=    Evaluate    "\\033[32m[ SUCCESS] Device ${DEVICE}[device_serial] is registered\\033[0m"
        Log To Console    ${success_msg}
        Log    IMS registration verified for ${DEVICE}[device_serial]    INFO
    ELSE
        ${failure_msg}=    Evaluate    "\\033[31m[ FAILURE] Device ${DEVICE}[device_serial] is NOT registered\\033[0m"
        Log To Console    ${failure_msg}
        Log    IMS registration check failed for ${DEVICE}[device_serial]    WARN
    END

    Should Be True    ${registered}


android_ip_version_check
    [Arguments]    ${DEVICE}    ${EXPECTED_IP_VERSION}
    [Documentation]    Checks if the device is using the expected IP version.
    ...    ${DEVICE}: The Android device dictionary.
    ...    ${EXPECTED_IP_VERSION}: The expected IP version (e.g. IPv4, IPv6).

    ${session_start}=    Evaluate    "\\n\\033[35m[CHECK IP VERSION] ${DEVICE}[device_serial] (${DEVICE}[device_brand])\\033[0m"
    Log To Console    ${session_start}
    Log    Starting IP version check for device ${DEVICE}[device_serial]: expected ${EXPECTED_IP_VERSION}    INFO

    ${ip_version}=    check_android_ip_version    ${DEVICE}[device_serial]    ${DEVICE}[device_brand]    ${EXPECTED_IP_VERSION}

    IF    ${ip_version}
        ${success_msg}=    Evaluate    "\\033[32m[ SUCCESS] Device ${DEVICE}[device_serial] is using IP version: ${EXPECTED_IP_VERSION}\\033[0m"
        Log To Console    ${success_msg}
        Log    IP version verified for ${DEVICE}[device_serial]: ${EXPECTED_IP_VERSION}    INFO
    ELSE
        ${failure_msg}=    Evaluate    "\\033[31m[ FAILURE] Device ${DEVICE}[device_serial] is NOT using IP version: ${EXPECTED_IP_VERSION}\\033[0m"
        Log To Console    ${failure_msg}
        Log    IP version check failed for ${DEVICE}[device_serial]: expected ${EXPECTED_IP_VERSION}    WARN
    END

    Should Be True    ${ip_version}


android_set_ip_version
    [Arguments]    ${DEVICE}    ${EXPECTED_IP_VERSION}
    [Documentation]    Sets the IP version on the Android device.
    ...    ${DEVICE}: The Android device dictionary.
    ...    ${EXPECTED_IP_VERSION}: The IP version to set (e.g. IPv4, IPv6).

    ${session_start}=    Evaluate    "\\n\\033[35m[SET IP VERSION] ${DEVICE}[device_serial] (${DEVICE}[device_brand]) -> ${EXPECTED_IP_VERSION}\\033[0m"
    Log To Console    ${session_start}
    Log    Starting IP version configuration for device ${DEVICE}[device_serial]: target ${EXPECTED_IP_VERSION}    INFO

    ${ip_version}=    set_android_ip_version    ${DEVICE}[device_serial]    ${DEVICE}[device_brand]    ${EXPECTED_IP_VERSION}

    IF    ${ip_version}
        ${success_msg}=    Evaluate    "\\033[32m[ SUCCESS] Device ${DEVICE}[device_serial] IP version set to: ${EXPECTED_IP_VERSION}\\033[0m"
        Log To Console    ${success_msg}
        Log    IP version successfully set for ${DEVICE}[device_serial]: ${EXPECTED_IP_VERSION}    INFO
    ELSE
        ${failure_msg}=    Evaluate    "\\033[31m[ FAILURE] Device ${DEVICE}[device_serial] could NOT set IP version to: ${EXPECTED_IP_VERSION}\\033[0m"
        Log To Console    ${failure_msg}
        Log    IP version configuration failed for ${DEVICE}[device_serial]: target ${EXPECTED_IP_VERSION}    WARN
    END

    Should Be True    ${ip_version}


execute_fixed_android_call_session_ab
    [Arguments]    ${SIP_SERVER}    ${AUT_SERVER}    ${DEVICE_B}    ${call_duration}    ${tc_dir}    ${scenario_path}    ${end_call_side}=${DEVICE_B}    ${Notional_format}=${False}
    [Documentation]    Initiates a call from a Fixed (SIP) endpoint to an Android Device B.
    ...    ${SIP_SERVER}: The SIP server dictionary (ip, port).
    ...    ${AUT_SERVER}: The AUT server dictionary (ip, port).
    ...    ${DEVICE_B}: The Android device dictionary receiving the call.
    ...    ${call_duration}: Duration of the call in seconds.
    ...    ${end_call_side}: Device that ends the call. Defaults to ${DEVICE_B}.

    ${session_start}=    Evaluate    "\\n\\033[35m[CALL SESSION - Fixed -> Android] ${SIP_SERVER}[sip_server_ip] -> ${DEVICE_B}[device_serial] (${DEVICE_B}[device_brand]) | Duration: ${call_duration}s\\033[0m"
    Log To Console    ${session_start}
    Log    Starting call session: ${SIP_SERVER}[sip_server_ip] to ${DEVICE_B}[device_serial]    INFO

    ${step1}=    Evaluate    "\\033[33m[~] [1/2] Initiating call from SIP server ${SIP_SERVER}[sip_server_ip]...\\033[0m"
    Log To Console    ${step1}
    Initiate_sipp_call
    ...    ${SIP_SERVER}[sip_server_ip]
    ...    ${SIP_SERVER}[sip_server_port]
    ...    ${AUT_SERVER}[aut_server_ip]
    ...    ${AUT_SERVER}[aut_server_port]
    ...    ${DEVICE_B}
    ...    ${tc_dir}
    ...    ${scenario_path}

    ${step2}=    Evaluate    "\\033[32m[] [2/2] Call terminated\\033[0m"
    Log To Console    ${step2}
    Log    Call session completed: ${SIP_SERVER}[sip_server_ip] to ${DEVICE_B}[device_serial]    INFO


execute_android_call_session_ab
    [Arguments]    ${DEVICE_A}    ${DEVICE_B}    ${call_duration}    ${end_call_side}=${DEVICE_A}    ${Notional_format}=${False}
    [Documentation]    Initiates a call from Android Device A to Android Device B.
    ...    ${DEVICE_A}: The calling Android device dictionary.
    ...    ${DEVICE_B}: The receiving Android device dictionary.
    ...    ${call_duration}: Duration of the call in seconds.
    ...    ${end_call_side}: Device dictionary that ends the call. Defaults to ${DEVICE_A}.

    ${session_start}=    Evaluate    "\\n\\033[35m[CALL SESSION - Android -> Android] ${DEVICE_A}[device_serial] (${DEVICE_A}[device_brand]) -> ${DEVICE_B}[device_serial] (${DEVICE_B}[device_brand]) | Duration: ${call_duration}s\\033[0m"
    Log To Console    ${session_start}
    Log    Starting call session: ${DEVICE_A}[device_serial] to ${DEVICE_B}[device_serial]    INFO

    ${step1}=    Evaluate    "\\033[33m[~] [1/3] Initiating call from Device A ${DEVICE_A}[device_serial]...\\033[0m"
    Log To Console    ${step1}
    ${call_initiated_result}=    initiate_android_call
    ...    ${DEVICE_A}[device_serial]
    ...    ${DEVICE_A}[device_brand]
    ...    ${DEVICE_B}[sim][msisdn]
    ...    ${Notional_format}
    Should Be Equal As Integers    0    ${call_initiated_result}
    Sleep    5

    ${ender_serial}=    Set Variable    ${end_call_side}[device_serial]
    ${b_hangs_up}=    Evaluate    '${DEVICE_B}[device_serial]' == '${ender_serial}'

    ${step2}=    Evaluate    "\\033[33m[~] [2/3] Answering call on Device B ${DEVICE_B}[device_serial]...\\033[0m"
    Log To Console    ${step2}
    ${call_answered_result}=    answer_android_incoming_call
    ...    ${DEVICE_B}[device_serial]
    ...    ${DEVICE_B}[device_brand]
    ...    ${call_duration}
    ...    ${b_hangs_up}
    Should Be Equal As Integers    0    ${call_answered_result}

    ${step3}=    Evaluate    "\\033[33m[~] [3/3] Terminating call...\\033[0m"
    Log To Console    ${step3}

    IF    '${ender_serial}' == '${DEVICE_A}[device_serial]'
        ${call_terminated_result}=    end_android_active_call
        ...    ${DEVICE_A}[device_serial]
        ...    ${DEVICE_A}[device_brand]
        Should Be Equal As Integers    0    ${call_terminated_result}
    ELSE IF    '${ender_serial}' == '${DEVICE_B}[device_serial]'
        Log    Device B ${DEVICE_B}[device_serial] ended the call during answer phase    INFO
    ELSE
        Fail    end_call_side serial '${ender_serial}' matches neither DEVICE_A (${DEVICE_A}[device_serial]) nor DEVICE_B (${DEVICE_B}[device_serial])
    END

    Log    Call session completed: ${DEVICE_A}[device_serial] to ${DEVICE_B}[device_serial]    INFO


initiate_android_call_session_ab
    [Arguments]    ${DEVICE_A}    ${DEVICE_B}    ${Notional_format}=${False}
    [Documentation]    Initiates a call from Android Device A to Android Device B without answering or terminating.
    ...    ${DEVICE_A}: The calling Android device dictionary.
    ...    ${DEVICE_B}: The receiving Android device dictionary.

    ${session_start}=    Evaluate    "\\n\\033[35m[INITIATE CALL SESSION - Android -> Android] ${DEVICE_A}[device_serial] (${DEVICE_A}[device_brand]) -> ${DEVICE_B}[device_serial] (${DEVICE_B}[device_brand])\\033[0m"
    Log To Console    ${session_start}
    Log    Initiating call: ${DEVICE_A}[device_serial] to ${DEVICE_B}[device_serial]    INFO

    ${step1}=    Evaluate    "\\033[33m[~] [1/1] Initiating call from Device A ${DEVICE_A}[device_serial]...\\033[0m"
    Log To Console    ${step1}
    ${call_initiated_result}=    initiate_android_call
    ...    ${DEVICE_A}[device_serial]
    ...    ${DEVICE_A}[device_brand]
    ...    ${DEVICE_B}[sim][msisdn]
    ...    ${Notional_format}
    Should Be Equal As Integers    0    ${call_initiated_result}


terminate_android_call_session_ab
    [Arguments]    ${DEVICE_A}
    [Documentation]    Terminates the active call on the specified Android device.
    ...    ${DEVICE_A}: The Android device dictionary whose active call will be terminated.

    ${session_start}=    Evaluate    "\\n\\033[35m[TERMINATE CALL SESSION - Android] ${DEVICE_A}[device_serial] (${DEVICE_A}[device_brand])\\033[0m"
    Log To Console    ${session_start}
    Log    Terminating active call on device ${DEVICE_A}[device_serial]    INFO

    ${step1}=    Evaluate    "\\033[33m[~] [1/1] Declining/terminating call on Device A ${DEVICE_A}[device_serial]...\\033[0m"
    Log To Console    ${step1}
    ${call_result}=    decline_android_incoming_call
    ...    ${DEVICE_A}[device_serial]
    ...    ${DEVICE_A}[device_brand]
    Should Be Equal As Integers    0    ${call_result}

    Log    Call terminated on ${DEVICE_A}[device_serial]    INFO


accept_android_call_session_ab
    [Arguments]    ${DEVICE_A}    ${Call_duration}
    [Documentation]    Answers an incoming call on the specified Android device.
    ...    ${DEVICE_A}: The Android device dictionary that will answer the call.
    ...    ${Call_duration}: Duration to hold the call before hanging up.

    ${session_start}=    Evaluate    "\\n\\033[35m[ACCEPT CALL SESSION - Android] ${DEVICE_A}[device_serial] (${DEVICE_A}[device_brand])\\033[0m"
    Log To Console    ${session_start}
    Log    Answering incoming call on device ${DEVICE_A}[device_serial]    INFO

    ${step1}=    Evaluate    "\\033[33m[~] [1/1] Answering call on Device A ${DEVICE_A}[device_serial]...\\033[0m"
    Log To Console    ${step1}
    ${call_answered_result}=    answer_android_incoming_call
    ...    ${DEVICE_A}[device_serial]
    ...    ${DEVICE_A}[device_brand]
    ...    ${Call_duration}
    ...    ${False}
    Should Be Equal As Integers    0    ${call_answered_result}

    Log    Call answered on ${DEVICE_A}[device_serial]    INFO


execute_android_call_session_ab_a_rel_before_b_answer
    [Arguments]    ${DEVICE_A}    ${DEVICE_B}    ${call_duration}    ${end_call_side}=A    ${SOURCE_SIM_SLOT}=1    ${Notional_format}=${False}    ${b_party_msisdn}=${None}
    [Documentation]    Initiates a call from Android Device A to Android Device B, then cancels from A before B answers.
    ...    ${DEVICE_A}: The calling Android device dictionary.
    ...    ${DEVICE_B}: The receiving Android device dictionary.
    ...    ${call_duration}: Duration to wait before cancelling.
    ...    ${end_call_side}: Which side ends the call - 'A' (caller) or 'B' (receiver). Defaults to 'A'.
    ...    ${b_party_msisdn}: Override B party number. Defaults to ${DEVICE_B}[sim][msisdn].

    ${session_start}=    Evaluate    "\\n\\033[35m[CALL SESSION - Android -> Android, A releases before B answers] ${DEVICE_A}[device_serial] (${DEVICE_A}[device_brand]) -> ${DEVICE_B}[device_serial] (${DEVICE_B}[device_brand]) | Duration: ${call_duration}s\\033[0m"
    Log To Console    ${session_start}
    Log    Starting early-release call session: ${DEVICE_A}[device_serial] to ${DEVICE_B}[device_serial]    INFO

    ${step1}=    Evaluate    "\\033[33m[~] [1/2] Initiating call from Device A ${DEVICE_A}[device_serial]...\\033[0m"
    Log To Console    ${step1}

    IF    ${b_party_msisdn}==${None}
        ${dial_number}=    Set Variable    ${DEVICE_B}[sim][msisdn]
    ELSE
        ${dial_number}=    Set Variable    ${b_party_msisdn}
    END

    ${call_initiated_result}=    initiate_android_call
    ...    ${DEVICE_A}[device_serial]
    ...    ${DEVICE_A}[device_brand]
    ...    ${dial_number}
    ...    ${Notional_format}
    Should Be Equal As Integers    0    ${call_initiated_result}
    Sleep    5

    ${step2}=    Evaluate    "\\033[33m[~] [2/2] Cancelling call from Device A ${DEVICE_A}[device_serial] before B answers...\\033[0m"
    Log To Console    ${step2}

    IF    '${end_call_side}'.upper() == 'A'
        ${call_terminated_result}=    end_android_active_call
        ...    ${DEVICE_A}[device_serial]
        ...    ${DEVICE_A}[device_brand]
        Should Be Equal As Integers    0    ${call_terminated_result}
        Log    Call cancelled by Device A ${DEVICE_A}[device_serial] before Device B answered    INFO
    END


android_verify_active_sim_slot
    [Arguments]    ${DEVICE}    ${SIM_SLOT}
    [Documentation]    Verifies that the active SIM card on the device is in the specified SIM slot.
    ...    Returns True if the active SIM matches the expected slot, otherwise False.
    ...    ${DEVICE}: The Android device dictionary.
    ...    ${SIM_SLOT}: The expected active SIM slot number.

    ${session_start}=    Evaluate    "\\n\\033[35m[CHECK SIM SLOT] ${DEVICE}[device_serial] (${DEVICE}[device_brand])\\033[0m"
    Log To Console    ${session_start}
    Log    Starting SIM slot check for device ${DEVICE}[device_serial]: expected slot ${SIM_SLOT}    INFO

    ${sim_card_ok}=    android_verify_sim_slot    ${DEVICE}[device_serial]    ${DEVICE}[device_brand]    ${SIM_SLOT}

    IF    ${sim_card_ok}
        ${success_msg}=    Evaluate    "\\033[32m[ SUCCESS] Device ${DEVICE}[device_serial] is using expected SIM slot: ${SIM_SLOT}\\033[0m"
        Log To Console    ${success_msg}
        Log    SIM slot verification passed for ${DEVICE}[device_serial]: slot ${SIM_SLOT}    INFO
        RETURN    ${True}
    ELSE
        ${failure_msg}=    Evaluate    "\\033[31m[ FAILURE] Device ${DEVICE}[device_serial] is NOT using expected SIM slot: ${SIM_SLOT}\\033[0m"
        Log To Console    ${failure_msg}
        Log    SIM slot verification failed for ${DEVICE}[device_serial]: expected slot ${SIM_SLOT}    WARN
        RETURN    ${False}
    END


android_set_active_sim_slot
    [Arguments]    ${DEVICE}    ${SIM_SLOT}
    [Documentation]    Sets the active SIM slot on the Android device.
    ...    Returns True if the device successfully switches to the specified slot, otherwise False.
    ...    ${DEVICE}: The Android device dictionary.
    ...    ${SIM_SLOT}: The SIM slot number to activate.

    ${session_start}=    Evaluate    "\\n\\033[35m[SET ACTIVE SIM SLOT] ${DEVICE}[device_serial] (${DEVICE}[device_brand])\\033[0m"
    Log To Console    ${session_start}
    Log    Starting SIM slot configuration for device ${DEVICE}[device_serial]: target slot ${SIM_SLOT}    INFO

    ${sim_card_ok}=    android_set_sim_slot    ${DEVICE}[device_serial]    ${DEVICE}[device_brand]    ${SIM_SLOT}

    IF    ${sim_card_ok}
        ${success_msg}=    Evaluate    "\\033[32m[ SUCCESS] Device ${DEVICE}[device_serial] active SIM slot set to: ${SIM_SLOT}\\033[0m"
        Log To Console    ${success_msg}
        Log    SIM slot successfully set for ${DEVICE}[device_serial]: slot ${SIM_SLOT}    INFO
    ELSE
        ${failure_msg}=    Evaluate    "\\033[31m[ FAILURE] Device ${DEVICE}[device_serial] could NOT switch to SIM slot: ${SIM_SLOT}\\033[0m"
        Log To Console    ${failure_msg}
        Log    SIM slot configuration failed for ${DEVICE}[device_serial]: target slot ${SIM_SLOT}    WARN
    END


execute_iphone_android_call_session_ab
    [Arguments]    ${DEVICE_A}    ${DEVICE_B}    ${call_duration}
    [Documentation]    Initiates a call from an iPhone (Device A) to an Android device (Device B).
    ...    ${DEVICE_A}: The iPhone device dictionary (caller).
    ...    ${DEVICE_B}: The Android device dictionary (receiver).
    ...    ${call_duration}: Duration of the call in seconds.

    ${session_start}=    Evaluate    "\\n\\033[35m[CALL SESSION - iPhone -> Android] ${DEVICE_A}[device_serial] (${DEVICE_A}[device_brand]) -> ${DEVICE_B}[device_serial] (${DEVICE_B}[device_brand]) | Duration: ${call_duration}s\\033[0m"
    Log To Console    ${session_start}
    Log    Starting call session: ${DEVICE_A}[device_serial] (iPhone) to ${DEVICE_B}[device_serial] (Android)    INFO

    ${step1}=    Evaluate    "\\033[33m[~] [1/3] Initiating call from iPhone ${DEVICE_A}[device_serial]...\\033[0m"
    Log To Console    ${step1}
    Initiate Call from Real Device Iphone
    ...    ${DEVICE_B}[sims][sim_slot_1][msisdn]
    ...    ${DEVICE_A}[device_serial]
    ...    ${DEVICE_A}[device_brand]
    Sleep    5

    ${step2}=    Evaluate    "\\033[33m[~] [2/3] Answering call on Android Device B ${DEVICE_B}[device_serial]...\\033[0m"
    Log To Console    ${step2}
    answer_android_incoming_call
    ...    ${DEVICE_B}[device_serial]
    ...    ${DEVICE_B}[device_brand]
    ...    ${call_duration}
    ...    ${False}

    ${step3}=    Evaluate    "\\033[33m[~] [3/3] Terminating call from iPhone ${DEVICE_A}[device_serial]...\\033[0m"
    Log To Console    ${step3}
    Terminate Active Call Iphone
    ...    ${DEVICE_A}[device_serial]
    ...    ${DEVICE_A}[device_brand]

    Log    Call session completed: ${DEVICE_A}[device_serial] (iPhone) to ${DEVICE_B}[device_serial] (Android)    INFO


fixedIms_registration
    [Arguments]    ${SIP_SERVER}    ${tc_dir}    ${scenario_path}
    [Documentation]    Performs IMS registration for a Fixed (SIP) endpoint.
    ...    ${SIP_SERVER}: The SIP server dictionary (ip, port).
    ...    ${tc_dir}: Test case directory for SIP scenario files.
    ...    ${scenario_path}: Path to the SIP registration scenario file.

    ${session_start}=    Evaluate    "\\n\\033[35m[FIXED IMS REGISTRATION] ${SIP_SERVER}[sip_server_ip]:${SIP_SERVER}[sip_server_port]\\033[0m"
    Log To Console    ${session_start}
    Log    Starting Fixed IMS registration for SIP server ${SIP_SERVER}[sip_server_ip]:${SIP_SERVER}[sip_server_port]    INFO

    ${registered}=    sip_registration    ${SIP_SERVER}[sip_server_ip]    ${SIP_SERVER}[sip_server_port]    ${tc_dir}    ${scenario_path}

    IF    ${registered}
        ${success_msg}=    Evaluate    "\\033[32m[ SUCCESS] SIP server ${SIP_SERVER}[sip_server_ip]:${SIP_SERVER}[sip_server_port] registered successfully\\033[0m"
        Log To Console    ${success_msg}
        Log    Fixed IMS registration successful for ${SIP_SERVER}[sip_server_ip]:${SIP_SERVER}[sip_server_port]    INFO
    ELSE
        ${failure_msg}=    Evaluate    "\\033[31m[ FAILURE] SIP server ${SIP_SERVER}[sip_server_ip]:${SIP_SERVER}[sip_server_port] registration FAILED\\033[0m"
        Log To Console    ${failure_msg}
        Log    Fixed IMS registration failed for ${SIP_SERVER}[sip_server_ip]:${SIP_SERVER}[sip_server_port]    WARN
    END

    Should Be True    ${registered}


android_hide_number
    [Arguments]    ${DEVICE_A}
    [Documentation]    Hides the A-party number to make outgoing calls anonymous.
    ...    ${DEVICE_A}: The Android device dictionary.

    ${session_start}=    Evaluate    "\\n\\033[35m[HIDE NUMBER - Android] ${DEVICE_A}[device_serial] (${DEVICE_A}[device_brand])\\033[0m"
    Log To Console    ${session_start}
    Log    Configuring caller ID hide for device ${DEVICE_A}[device_serial]    INFO

    ${hide_num_result}=    hide_number_android
    ...    ${DEVICE_A}[device_serial]
    ...    ${DEVICE_A}[device_brand]
    ...    ${DEVICE_A}[sim][sim_slot]

    Should Be True    ${hide_num_result}
    Log    Caller ID successfully hidden for ${DEVICE_A}[device_serial]    INFO


android_display_number
    [Arguments]    ${DEVICE_A}
    [Documentation]    Restores A-party number display for outgoing calls.
    ...    ${DEVICE_A}: The Android device dictionary.

    ${session_start}=    Evaluate    "\\n\\033[35m[DISPLAY NUMBER - Android] ${DEVICE_A}[device_serial] (${DEVICE_A}[device_brand])\\033[0m"
    Log To Console    ${session_start}
    Log    Configuring caller ID display for device ${DEVICE_A}[device_serial]    INFO

    ${display_num_result}=    display_number_android
    ...    ${DEVICE_A}[device_serial]
    ...    ${DEVICE_A}[device_brand]
    ...    ${DEVICE_A}[sim][sim_slot]

    Should Be True    ${display_num_result}
    Log    Caller ID display successfully restored for ${DEVICE_A}[device_serial]    INFO


android_set_call_forwarding
    [Arguments]    ${DEVICE_A}    ${DEVICE_B}    ${condition}
    [Documentation]    Configures call forwarding on an Android device using GSM MMI codes.
    ...    Forwards calls from Device A to Device B's number under the given condition.
    ...    ${DEVICE_A}: The Android device dictionary to configure forwarding on.
    ...    ${DEVICE_B}: The Android device dictionary whose number receives forwarded calls.
    ...    ${condition}: Forwarding condition (unconditional, no_reply, busy, not_reachable).

    ${session_start}=    Evaluate    "\\n\\033[35m[SET CALL FORWARDING - Android -> Android] ${DEVICE_A}[device_serial] (${DEVICE_A}[device_brand]) -> ${DEVICE_B}[device_serial] (${DEVICE_B}[device_brand]) | Condition: ${condition}\\033[0m"
    Log To Console    ${session_start}
    Log    Configuring call forwarding: ${DEVICE_A}[device_serial] -> ${DEVICE_B}[device_serial] (${condition})    INFO

    ${step1}=    Evaluate    "\\033[33m[~] [1/1] Applying call forwarding (${condition}) on ${DEVICE_A}[device_serial] -> ${DEVICE_B}[sim][msisdn]...\\033[0m"
    Log To Console    ${step1}
    ${cf_set_result}=    set_android_call_forwarding
    ...    ${DEVICE_A}[device_serial]
    ...    ${DEVICE_B}[sim][msisdn]
    ...    ${condition}
    Should Be Equal As Integers    0    ${cf_set_result}

    Log    Call forwarding (${condition}) successfully configured on ${DEVICE_A}[device_serial]    INFO


android_disable_call_forwarding
    [Arguments]    ${DEVICE}    ${condition}
    [Documentation]    Disables call forwarding on an Android device using GSM MMI codes.
    ...    ${DEVICE}: The Android device dictionary to disable forwarding on.
    ...    ${condition}: Forwarding condition to disable (unconditional, no_reply, busy, not_reachable).

    ${session_start}=    Evaluate    "\\n\\033[35m[DISABLE CALL FORWARDING - Android] ${DEVICE}[device_serial] (${DEVICE}[device_brand]) | Condition: ${condition}\\033[0m"
    Log To Console    ${session_start}
    Log    Disabling call forwarding on ${DEVICE}[device_serial]: condition ${condition}    INFO

    ${cf_set_result}=    disable_android_call_forwarding
    ...    ${DEVICE}[device_serial]
    ...    ${condition}
    Should Be Equal As Integers    0    ${cf_set_result}

    Log    Call forwarding (${condition}) successfully disabled on ${DEVICE}[device_serial]    INFO


android_query_call_log
    [Arguments]    ${DEVICE_A}    ${DEVICE_B}    ${call_duration}
    [Documentation]    Queries the call log on Device A to verify a past call from/to Device B.
    ...    ${DEVICE_A}: The Android device dictionary whose call log is queried.
    ...    ${DEVICE_B}: The Android device dictionary whose number is looked up in the log.
    ...    ${call_duration}: Expected call duration to match in the call log.

    ${session_start}=    Evaluate    "\\n\\033[35m[QUERY CALL LOG - Android] ${DEVICE_A}[device_serial] (${DEVICE_A}[device_brand])\\033[0m"
    Log To Console    ${session_start}
    Log    Starting call log query on ${DEVICE_A}[device_serial] for number ${DEVICE_B}[sim][msisdn]    INFO

    ${step1}=    Evaluate    "\\033[33m[~] [1/1] Querying call log on ${DEVICE_A}[device_serial] for ${DEVICE_B}[sim][msisdn]...\\033[0m"
    Log To Console    ${step1}
    ${is_call_done}=    query_call_log_android
    ...    ${DEVICE_A}[device_serial]
    ...    ${DEVICE_B}[sim][msisdn]
    ...    ${call_duration}

    IF    ${is_call_done}
        ${success_msg}=    Evaluate    "\\033[32m[ SUCCESS] Call log verified on ${DEVICE_A}[device_serial] for ${DEVICE_B}[sim][msisdn]\\033[0m"
        Log To Console    ${success_msg}
        Log    Call log verification passed on ${DEVICE_A}[device_serial]    INFO
    ELSE
        ${failure_msg}=    Evaluate    "\\033[31m[ FAILURE] Call log NOT verified on ${DEVICE_A}[device_serial] for ${DEVICE_B}[sim][msisdn]\\033[0m"
        Log To Console    ${failure_msg}
        Log    Call log verification failed on ${DEVICE_A}[device_serial]    WARN
    END

    Should Be True    ${is_call_done}


execute_android_registration_and_deregistration
    [Arguments]    ${DEVICE_A}    ${call_duration}
    [Documentation]    Toggles airplane mode on Device A for the given duration to simulate deregistration then re-registration.
    ...    ${DEVICE_A}: The Android device dictionary.
    ...    ${call_duration}: Duration airplane mode stays ON before auto-disabling (in seconds).

    ${session_start}=    Evaluate    "\\n\\033[35m[ANDROID REGISTRATION/DEREGISTRATION SESSION] ${DEVICE_A}[device_serial] (${DEVICE_A}[device_brand]) | Duration: ${call_duration}s\\033[0m"
    Log To Console    ${session_start}
    Log    Starting registration/deregistration cycle for ${DEVICE_A}[device_serial]: duration ${call_duration}s    INFO

    ${step1}=    Evaluate    "\\033[33m[~] [1/1] Toggling airplane mode on ${DEVICE_A}[device_serial] for ${call_duration}s...\\033[0m"
    Log To Console    ${step1}
    ${airplane_result}=    set_airplane_mode_android
    ...    ${DEVICE_A}[device_serial]
    ...    ${call_duration}


execute_android_call_forwarding_chain_CFU
    [Arguments]    ${DEVICE_A}    ${DEVICE_B}    ${DEVICE_C}    ${call_duration}    ${end_call_side}    ${Notional_format}=${False}
    [Documentation]    Executes a Call Forwarding Unconditional (CFU) chain: A calls B, B forwards immediately to C.
    ...    ${DEVICE_A}: The calling device dictionary.
    ...    ${DEVICE_B}: The device with CFU active (will not ring -- forwards immediately).
    ...    ${DEVICE_C}: The forwarding target device dictionary.
    ...    ${call_duration}: Duration of the call in seconds.
    ...    ${end_call_side}: Device dictionary that ends the call (DEVICE_A or DEVICE_C).

    ${session_start}=    Evaluate    "\\n\\033[35m[CFU SESSION - Call Forwarding Unconditional] ${DEVICE_A}[device_serial] (${DEVICE_A}[device_brand]) -> ${DEVICE_B}[device_serial] (${DEVICE_B}[device_brand]) -> ${DEVICE_C}[device_serial] (${DEVICE_C}[device_brand]) | Duration: ${call_duration}s\\033[0m"
    Log To Console    ${session_start}
    Log    Starting CFU session: ${DEVICE_A}[device_serial] -> ${DEVICE_B}[device_serial] (CFU) -> ${DEVICE_C}[device_serial]    INFO

    ${step1}=    Evaluate    "\\033[33m[~] [1/3] Initiating call from Device A ${DEVICE_A}[device_serial] to Device B ${DEVICE_B}[device_serial] (CFU active -- forwards immediately to Device C)...\\033[0m"
    Log To Console    ${step1}
    ${call_initiated_result}=    initiate_android_call
    ...    ${DEVICE_A}[device_serial]
    ...    ${DEVICE_A}[device_brand]
    ...    ${DEVICE_B}[sim][msisdn]
    ...    ${Notional_format}
    Should Be Equal As Integers    0    ${call_initiated_result}
    Sleep    5

    ${ender_serial}=    Set Variable    ${end_call_side}[device_serial]
    ${c_hangs_up}=    Evaluate    '${DEVICE_C}[device_serial]' == '${ender_serial}'

    ${step2}=    Evaluate    "\\033[33m[~] [2/3] Answering forwarded call on Device C ${DEVICE_C}[device_serial] (forwarded from Device B via CFU)...\\033[0m"
    Log To Console    ${step2}
    ${call_answered_result}=    answer_android_incoming_call
    ...    ${DEVICE_C}[device_serial]
    ...    ${DEVICE_C}[device_brand]
    ...    ${call_duration}
    ...    ${c_hangs_up}
    Should Be Equal As Integers    0    ${call_answered_result}

    ${step3}=    Evaluate    "\\033[33m[~] [3/3] Terminating CFU call session...\\033[0m"
    Log To Console    ${step3}

    IF    '${ender_serial}' == '${DEVICE_A}[device_serial]'
        ${call_terminated_result}=    end_android_active_call
        ...    ${DEVICE_A}[device_serial]
        ...    ${DEVICE_A}[device_brand]
        Should Be Equal As Integers    0    ${call_terminated_result}
    ELSE IF    '${ender_serial}' == '${DEVICE_C}[device_serial]'
        Log    Device C ${DEVICE_C}[device_serial] ended the call during answer phase    INFO
    ELSE
        Fail    end_call_side serial '${ender_serial}' matches neither DEVICE_A (${DEVICE_A}[device_serial]) nor DEVICE_C (${DEVICE_C}[device_serial])
    END

    Log    CFU session completed: call forwarded unconditionally from ${DEVICE_B}[device_serial] to ${DEVICE_C}[device_serial]    INFO


execute_android_call_forwarding_chain_CFNRc
    [Arguments]    ${DEVICE_A}    ${DEVICE_B}    ${DEVICE_C}    ${call_duration}    ${end_call_side}    ${Notional_format}=${False}
    [Documentation]    Executes a Call Forwarding Not Reachable (CFNRc) chain: A calls B (unreachable), B forwards to C.
    ...    ${DEVICE_A}: The calling device dictionary.
    ...    ${DEVICE_B}: The device with CFNRc active, put in airplane mode to simulate unreachability.
    ...    ${DEVICE_C}: The forwarding target device dictionary.
    ...    ${call_duration}: Duration of the call in seconds.
    ...    ${end_call_side}: Device dictionary that ends the call (DEVICE_A or DEVICE_C).

    ${session_start}=    Evaluate    "\\n\\033[35m[CFNRc SESSION - Call Forwarding Not Reachable] ${DEVICE_A}[device_serial] (${DEVICE_A}[device_brand]) -> ${DEVICE_B}[device_serial] (${DEVICE_B}[device_brand]) -> [not reachable] -> ${DEVICE_C}[device_serial] (${DEVICE_C}[device_brand]) | Duration: ${call_duration}s\\033[0m"
    Log To Console    ${session_start}
    Log    Starting CFNRc session: ${DEVICE_A}[device_serial] -> ${DEVICE_B}[device_serial] (unreachable) -> ${DEVICE_C}[device_serial]    INFO

    ${step1}=    Evaluate    "\\033[33m[~] [1/4] Setting Device B ${DEVICE_B}[device_serial] as unreachable (enabling airplane mode)...\\033[0m"
    Log To Console    ${step1}
    ${airplane_result}=    set_airplane_mode_android
    ...    ${DEVICE_B}[device_serial]
    Should Be True    ${airplane_result}

    ${step2}=    Evaluate    "\\033[33m[~] [2/4] Initiating call from Device A ${DEVICE_A}[device_serial] to Device B ${DEVICE_B}[device_serial] (CFNRc active -- Device B unreachable, will forward to Device C)...\\033[0m"
    Log To Console    ${step2}
    ${call_initiated_result}=    initiate_android_call
    ...    ${DEVICE_A}[device_serial]
    ...    ${DEVICE_A}[device_brand]
    ...    ${DEVICE_B}[sim][msisdn]
    ...    ${Notional_format}
execute_android_deregistration
    [Arguments]    ${DEVICE_A}
    [Documentation]    Executes Android deregistration flow for the specified device.
    ...    Performs Android network/service deregistration validation steps.
    ...    ${DEVICE_A}: The Android device dictionary used for the deregistration process.

    ${session_start}=    Evaluate    "\\n\\033[35m[ANDROID DEREGISTRATION SESSION] ─── ${DEVICE_A}[device_serial] (${DEVICE_A}[device_brand]) ───\\033[0m"
    Log To Console    ${session_start}
    Log    Starting Android deregistration session    INFO

    ${step1}=    Evaluate    "\\033[33m[~] Enabling airplane mode on ${DEVICE_A}[device_serial] (${DEVICE_A}[device_brand])...\\033[0m"
    Log To Console    ${step1}
    ${airplane_result}=    set_airplane_mode_android
    ...    ${DEVICE_A}[device_serial]

execute_android_registration
    [Arguments]    ${DEVICE_A}
    [Documentation]    Executes Android registration flow for the specified device.
    ...    Performs Android network/service registration steps.
    ...    ${DEVICE_A}: The Android device dictionary used for the registration process.

    ${session_start}=    Evaluate    "\\n\\033[35m[ANDROID REGISTRATION SESSION] ─── ${DEVICE_A}[device_serial] (${DEVICE_A}[device_brand]) ───\\033[0m"
    Log To Console    ${session_start}
    Log    Starting Android registration session    INFO

    ${step1}=    Evaluate    "\\033[33m[~] Disabling airplane mode on ${DEVICE_A}[device_serial] (${DEVICE_A}[device_brand])...\\033[0m"
    Log To Console    ${step1}
    ${airplane_result}=    disable_airplane_mode_android
    ...    ${DEVICE_A}[device_serial]
