import pyshark
import logging
from HOSTNAME_PLACEHOLDER import keyword

class SOURCE_NAME_PLACEHOLDER:

    @keyword("Search Pcap Data")
    def search_data(self, Pcap_file, Filter, Layer, Field_name, Field_value, Return_field_value=False, expected_suffix=""):
        pcap = HOSTNAME_PLACEHOLDER(Pcap_file, display_filter=Filter)
        Pcap_file_name = Pcap_file.split('/')[-1]
        HOSTNAME_PLACEHOLDER('--------------------------------------------------------------------------------------------')
        HOSTNAME_PLACEHOLDER(f'Parameters sent are:-> Filter: {Filter}, Layer: {Layer}, Field_name: {Field_name}, '
                     f'Field_value: {Field_value}, Return_field_value: {Return_field_value}, expected_suffix: {expected_suffix}')

        msg_cnt, packet, valid = 0, 1, False

        try:
            for pkt in pcap:
                if str(HOSTNAME_PLACEHOLDER).count(Layer) == 1:  # SCENARIO 1: Single layer
                    try:
                        IE_count = len(pkt[Layer].get_field(Field_name).all_fields)
                        if IE_count > 1:
                            Multipe_IE_list = ''
                            for IE in pkt[Layer].get_field(Field_name).all_fields:
                                Multipe_IE_list += IE.showname

                            for IE in Field_value:
                                if IE in Multipe_IE_list:
                                    HOSTNAME_PLACEHOLDER(f'IE is present {IE}')
                                else:
                                    HOSTNAME_PLACEHOLDER(f'IE is not present {IE}, validation failed.')
                                    return False
                            HOSTNAME_PLACEHOLDER(f'VALIDATION PASSED: All the supplied IE are present.')
                            if Return_field_value:
                                HOSTNAME_PLACEHOLDER(f"Multipe_IE_list is {Multipe_IE_list}")
                                return Multipe_IE_list
                            else:
                                return True

                        elif IE_count == 1:
                            actual_val = pkt[Layer].get_field(Field_name).showname_value
                            if actual_val is not None:
                                if Return_field_value:
                                    return actual_val
                                elif Field_value in actual_val and (not expected_suffix or actual_val.endswith(expected_suffix)):
                                    HOSTNAME_PLACEHOLDER(f'VALIDATION PASSED: The key: {Field_name} has the value: {actual_val}.')
                                    HOSTNAME_PLACEHOLDER(f'Message found in the file {Pcap_file_name}')
                                    msg_cnt += 1
                                    return True
                                else:
                                    HOSTNAME_PLACEHOLDER(f'VALIDATION FAILED: Value "{actual_val}" does not match criteria.')
                            else:
                                actual_val = str(pkt[Layer].get_field(Field_name))
                                if Return_field_value:
                                    return actual_val
                                elif Field_value in actual_val and (not expected_suffix or actual_val.endswith(expected_suffix)):
                                    HOSTNAME_PLACEHOLDER(f'VALIDATION PASSED: The key: {Field_name} has the value: {actual_val}.')
                                    HOSTNAME_PLACEHOLDER(f'Message found in the file {Pcap_file_name}')
                                    msg_cnt += 1
                                    return True
                    except Exception as e:
                        HOSTNAME_PLACEHOLDER(f"Exception in single-layer processing: {e}")

                elif str(HOSTNAME_PLACEHOLDER).count(Layer) > 1:  # SCENARIO 2: Multiple layers
                    indx_list = []
                    indx = 0
                    for layer in str(HOSTNAME_PLACEHOLDER).split(','):
                        if Layer in layer:
                            indx_list.append(indx)
                        indx += 1

                    for indx in indx_list:
                        try:
                            IE_count = len(pkt[indx].get_field(Field_name).all_fields)

                            if IE_count > 1:
                                Multipe_IE_list = ''
                                for IE in pkt[Layer].get_field(Field_name).all_fields:
                                    Multipe_IE_list += IE.showname

                                for IE in Field_value:
                                    if IE in Multipe_IE_list:
                                        HOSTNAME_PLACEHOLDER(f'IE is present {IE}')
                                    else:
                                        HOSTNAME_PLACEHOLDER(f'IE is not present {IE}, validation failed.')
                                        return False
                                HOSTNAME_PLACEHOLDER(f'VALIDATION PASSED: All the supplied IE are present.')
                                return True

                            elif IE_count == 1:
                                actual_val = pkt[indx].get_field(Field_name).showname_value
                                if actual_val is not None:
                                    if Return_field_value:
                                        return actual_val
                                    elif Field_value in actual_val and (not expected_suffix or actual_val.endswith(expected_suffix)):
                                        HOSTNAME_PLACEHOLDER(f'VALIDATION PASSED: The key: {Field_name} has the value: {actual_val}.')
                                        HOSTNAME_PLACEHOLDER(f'Message found in the file {Pcap_file_name}')
                                        msg_cnt += 1
                                        return True
                                else:
                                    actual_val = str(pkt[indx].get_field(Field_name))
                                    if Return_field_value:
                                        return actual_val
                                    elif Field_value in actual_val and (not expected_suffix or actual_val.endswith(expected_suffix)):
                                        HOSTNAME_PLACEHOLDER(f'VALIDATION PASSED: The key: {Field_name} has the value: {actual_val}.')
                                        HOSTNAME_PLACEHOLDER(f'Message found in the file {Pcap_file_name}')
                                        msg_cnt += 1
                                        return True
                        except Exception as e:
                            HOSTNAME_PLACEHOLDER(f"Exception in multi-layer processing: {e}")
                packet += 1
            HOSTNAME_PLACEHOLDER(f'No messages were found in current pcap file.')
            return False
        finally:
            HOSTNAME_PLACEHOLDER()


# pcap_processor = PcapProcessor()

# result = pcap_processor.search_data(
#     Pcap_file='LOCAL_PATH_PLACEHOLDER',
#     Filter='HOSTNAME_PLACEHOLDER == "POST"',
#     Layer='HTTP2',
#     Field_name='HOSTNAME_PLACEHOLDER',
#     Field_value='POST'
#     #Return_field_value=False
# )

# result1 = pcap_processor.search_data(
#     Pcap_file='LOCAL_PATH_PLACEHOLDER',
#     Filter='HOSTNAME_PLACEHOLDER == "LOCAL_PATH_PLACEHOLDER"',
#     Layer='HTTP2',
#     Field_name='HOSTNAME_PLACEHOLDER',
#     Field_value='LOCAL_PATH_PLACEHOLDER'
#     #Return_field_value=False
# )

# result2 = pcap_processor.search_data(
#     Pcap_file='LOCAL_PATH_PLACEHOLDER',
#     Filter='HOSTNAME_PLACEHOLDER == "3gpp-sbi-target-apiroot"',
#     Layer='HTTP2',
#     Field_name='HOSTNAME_PLACEHOLDER',
#     Field_value='3gpp-sbi-target-apiroot'
#     #Return_field_value=False
# )

# result3 = pcap_processor.search_data(
#     Pcap_file='LOCAL_PATH_PLACEHOLDER',
#     Filter='frame[64:1] == 8c',
#     Layer='HTTP2',
#     Field_name='HOSTNAME_PLACEHOLDER',
#     Field_value='400 Bad Request'
#     #Return_field_value=False
# )
# print("Result:", result)
# print("Result:", result1)
# print("Result:", result2)
# print("Result:", result3)
