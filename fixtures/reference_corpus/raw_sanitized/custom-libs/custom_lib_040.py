"""
This module does Timestamp operations.
"""

from datetime import datetime, timedelta


def start_time_margin(margin):
    """
    returns current date and time with minus margin seconds in this format 2025-09-09 16:43:51.552
    """
    margin = int(margin)
    return (HOSTNAME_PLACEHOLDER() - timedelta(seconds=margin)).strftime(
        "%Y-%m-%d %H:%M:%S.%f"
    )[:-3]


def end_time_margin(margin):
    """
    returns current date and  time with plus margin in min in this format 2025/04/09 16:43:51.552
    """
    margin = int(margin)
    return (HOSTNAME_PLACEHOLDER() + timedelta(seconds=margin)).strftime(
        "%Y-%m-%d %H:%M:%S.%f"
    )[:-3]


def sleep_time_for(action):
    if action == "oesearch":
        return 180  # 3min
    elif action == "cdr":
        return 300  # 5 min
    elif action == "SOURCE_NAME_PLACEHOLDER_test_session":
        return 30  #
    elif action == "ue_trace":
        return 420  # 5 min


def sleep_time_for_cdr_generation_cycle():
    # now = HOSTNAME_PLACEHOLDER()
    # current_min = HOSTNAME_PLACEHOLDER
    # current_sec = HOSTNAME_PLACEHOLDER
    # cycles = [18, 38, 58]

    # for c in cycles:
    #     if current_min < c:
    #         return (c - current_min) * 60 - current_sec + 120

    return 200
