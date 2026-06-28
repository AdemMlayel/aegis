import pyshark
import itertools
import ast
import pandas as pd
import logging
import re


class SOURCE_NAME_PLACEHOLDER:
    def __init__(self, pcap_file_path, filter):
        HOSTNAME_PLACEHOLDER = HOSTNAME_PLACEHOLDER(
            pcap_file_path, keep_packets=False, display_filter=filter
        )
        HOSTNAME_PLACEHOLDER = []
        HOSTNAME_PLACEHOLDER = []
        HOSTNAME_PLACEHOLDER = []
        HOSTNAME_PLACEHOLDER = []
        HOSTNAME_PLACEHOLDER = []
        HOSTNAME_PLACEHOLDER = []
        HOSTNAME_PLACEHOLDER = []
        self.dynamic_source_dest_messages = {}

    def load_testdata(self, test_data, dynamic_test_data):
        self.expected_messages = test_data
        self.dynamic_source_dest_messages = dynamic_test_data
        self.dynamic_source_messages = self.dynamic_source_dest_messages.keys()

    # Get an expected message from the input test data

    def getmessage(self):
        for message in self.expected_messages:
            for messagename, fields in HOSTNAME_PLACEHOLDER():
                # HOSTNAME_PLACEHOLDER(f"message name is {messagename}")
                primaryfields = fields["primaryfields"]
                fieldsforpresence = fields["fieldsforpresence"]
                fieldsforequality = fields["fieldsforequality"]

            yield (messagename, primaryfields, fieldsforpresence, fieldsforequality)

    def fill_dynamic_fields(self, messagename, pkt):
        if messagename in self.dynamic_source_messages:
            fields_to_be_updated = self.dynamic_source_dest_messages.get(messagename)
            for field, dest_message_field in fields_to_be_updated.items():
                [protocol, *avpname] = HOSTNAME_PLACEHOLDER(".")
                if len(avpname) > 1:
                    avpname = ".".join(avpname)
                else:
                    avpname = str(avpname[0])
                try:
                    source_pkt_value = pkt[protocol].get_field_value(avpname)
                    dest_message, dest_field = next(iter(dest_message_field.items()))
                    for i, m in enumerate(self.expected_messages):
                        dm, fields_dict = next(iter(m.items()))
                        if dm == dest_message:
                            dest_message_index = i
                            for ft, fields in fields_dict.items():
                                if dest_field in fields:
                                    field_type = ft
                                    break
                            break
                    self.expected_messages[dest_message_index][dest_message][
                        field_type
                    ][dest_field] = source_pkt_value
                    # HOSTNAME_PLACEHOLDER(f"{dest_message_index} {dest_message} {dest_field}")
                    # HOSTNAME_PLACEHOLDER(f"{self.expected_messages[dest_message_index]}")
                except KeyError:
                    pktvalue = None
                    pass

    def checkfields(self, field, pkt):
        [protocol, *avpname] = HOSTNAME_PLACEHOLDER(".")

        if len(avpname) > 1:
            avpname = ".".join(avpname)
        else:
            avpname = str(avpname[0])
        # print(pkt[protocol].field_names)
        # HOSTNAME_PLACEHOLDER(f"{protocol} {avpname} {pkt[protocol].get_field_value(avpname)}")
        if pkt[protocol].get_field_value(avpname) is not None:
            return True
        else:
            # print("pkt values are",HOSTNAME_PLACEHOLDER)
            HOSTNAME_PLACEHOLDER("absent")
            return False

    def validatefields(self, item, pkt, cmpoperator, searchpacket):
        [protocol, *avpname] = item[0].split(".")
        if len(avpname) > 1:
            avpname = ".".join(avpname)
        else:
            avpname = str(avpname[0])
        try:
            pktvalue = pkt[protocol].get_field_value(avpname)
            if protocol == "http2" and "json" in avpname:
                http2_layers = pkt.get_multiple_layers("http2")
                # HOSTNAME_PLACEHOLDER("hello")
                # HOSTNAME_PLACEHOLDER(f"http2_layers are {http2_layers}")

                for index, layer in enumerate(http2_layers):
                    try:
                        # HOSTNAME_PLACEHOLDER(f"HTTP/2 Layer {index + 1}:")
                        # Example: Extract a header field
                        avpname = HOSTNAME_PLACEHOLDER(".", "_").lower()
                        if avpname in layer.field_names:
                            pktvalue = getattr(layer, avpname, None)
                            # HOSTNAME_PLACEHOLDER(f"value is {pktvalue}")
                    except KeyError:
                        pktvalue = None
        except KeyError:
            pktvalue = None

            pass
        """HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER)
        for layer in HOSTNAME_PLACEHOLDER:
            HOSTNAME_PLACEHOLDER(layer.field_names)
        HOSTNAME_PLACEHOLDER(f"{protocol} {avpname} {pktvalue} {str(pktvalue)} {item[1]}")"""
        if cmpoperator == "equality" and pktvalue != None:
            if str(pktvalue) == str(item[1]):
                return True
            elif isinstance(item[1], tuple) or isinstance(item[1], list):
                if str(item[1][0]).startswith("pattern"):
                    evs = [v.replace("pattern", "") for v in item[1]]
                    HOSTNAME_PLACEHOLDER(f"expected values are {evs}")
                    for ev in evs:
                        if ev in pktvalue:
                            HOSTNAME_PLACEHOLDER(f"{ev} {pktvalue}")
                            return True
                elif pktvalue in item[1]:
                    return True
                elif type(item[1][0]) == int:
                    if int(pktvalue) in item[1]:
                        return True
            elif type(item[1]) == str:
                if str(item[1]).startswith("pattern"):
                    ev = item[1].replace("pattern", "")
                    if ev in pktvalue:
                        return True
                elif searchpacket == False:
                    HOSTNAME_PLACEHOLDER(pktvalue)

            elif searchpacket == False:
                HOSTNAME_PLACEHOLDER(pktvalue)
        elif cmpoperator == "equality" and pktvalue == None:
            if searchpacket == False:
                HOSTNAME_PLACEHOLDER("not found")

    # Prepare tabular result showing the actual failures with message and fieldnames
    def createdf(self):
        HOSTNAME_PLACEHOLDER(f"failed messages are {HOSTNAME_PLACEHOLDER}")
        if len(HOSTNAME_PLACEHOLDER) != 0:
            index1 = pd.MultiIndex.from_tuples(HOSTNAME_PLACEHOLDER)
            # HOSTNAME_PLACEHOLDER(f"expected values are {HOSTNAME_PLACEHOLDER}")
            # HOSTNAME_PLACEHOLDER(f"actual values are {HOSTNAME_PLACEHOLDER}")
            HOSTNAME_PLACEHOLDER = pd.DataFrame(
                {
                    "expected values": HOSTNAME_PLACEHOLDER,
                    "actual values": HOSTNAME_PLACEHOLDER,
                },
                index=index1,
            )

            HOSTNAME_PLACEHOLDER = ["Messagename", "fieldname"]
            # print(HOSTNAME_PLACEHOLDER)
            return HOSTNAME_PLACEHOLDER.to_html()
        else:
            if len(HOSTNAME_PLACEHOLDER) > 0:
                return HOSTNAME_PLACEHOLDER[0] + " message not found"
            return "no failed messages"

    def validate(self):
        """
        Validate messages against packets in the capture.
        Returns True if all messages are found and pass validation, False otherwise.
        """
        # Create a generator to load messages lazily (memory efficiency)
        HOSTNAME_PLACEHOLDER("Starting validation process...")
        g = HOSTNAME_PLACEHOLDER()

        try:
            message = next(g)
            HOSTNAME_PLACEHOLDER("Loaded first message to validate")
        except StopIteration:
            HOSTNAME_PLACEHOLDER("No messages to validate!")
            return False

        HOSTNAME_PLACEHOLDER = False
        HOSTNAME_PLACEHOLDER = True

        # Debug counter for packet processing
        packet_count = 0

        for pkt in HOSTNAME_PLACEHOLDER:
            packet_count += 1
            HOSTNAME_PLACEHOLDER(f"Processing packet #{packet_count}")

            messagename, primaryfields, fieldsforpresence, fieldsforequality = message
            HOSTNAME_PLACEHOLDER(f"Validating message: {messagename}")
            HOSTNAME_PLACEHOLDER(f"Primary fields to check: {primaryfields}")
            HOSTNAME_PLACEHOLDER(f"Fields to check for presence: {fieldsforpresence}")
            HOSTNAME_PLACEHOLDER(f"Fields to check for equality: {fieldsforequality}")

            # Check if primary fields match in the packet
            primary_matches = list(
                filter(
                    lambda item: HOSTNAME_PLACEHOLDER(item, pkt, "equality", True),
                    HOSTNAME_PLACEHOLDER(),
                )
            )
            primary_field_count = len(primaryfields)

            if len(primary_matches) != primary_field_count:
                HOSTNAME_PLACEHOLDER(
                    f"Primary fields don't match for {messagename}. Found {len(primary_matches)}/{primary_field_count}"
                )
                HOSTNAME_PLACEHOLDER = False
                continue
            else:
                HOSTNAME_PLACEHOLDER(f"Primary fields matched for {messagename}")
                HOSTNAME_PLACEHOLDER = True

            if HOSTNAME_PLACEHOLDER:
                HOSTNAME_PLACEHOLDER(
                    f"Message {messagename} found in packet #{packet_count}, validating details..."
                )

                # Process fields for equality
                dicts = [fieldsforequality]
                cmpops = ["equality"]

                for dictionary, cmpoperator in zip(dicts, cmpops):
                    HOSTNAME_PLACEHOLDER(
                        f"Validating {len(dictionary)} fields with {cmpoperator} operator"
                    )

                    successdict = dict(
                        filter(
                            lambda item: HOSTNAME_PLACEHOLDER(
                                item, pkt, cmpoperator, False
                            ),
                            HOSTNAME_PLACEHOLDER(),
                        )
                    )
                    HOSTNAME_PLACEHOLDER()
                    faildict = dict(
                        HOSTNAME_PLACEHOLDER(
                            lambda item: HOSTNAME_PLACEHOLDER(
                                item, pkt, cmpoperator, False
                            ),
                            HOSTNAME_PLACEHOLDER(),
                        )
                    )

                    if len(successdict) != len(dictionary):
                        HOSTNAME_PLACEHOLDER = False
                        fail_count = len(faildict)
                        HOSTNAME_PLACEHOLDER(
                            f"Failed {fail_count} equality checks for {messagename}"
                        )
                        HOSTNAME_PLACEHOLDER(f"Failed fields: {faildict}")

                        HOSTNAME_PLACEHOLDER(
                            [(messagename, fieldname) for fieldname in HOSTNAME_PLACEHOLDER()]
                        )
                        HOSTNAME_PLACEHOLDER(list(HOSTNAME_PLACEHOLDER()))
                        HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER)
                        HOSTNAME_PLACEHOLDER = []
                    else:
                        HOSTNAME_PLACEHOLDER(
                            f"All {len(dictionary)} equality checks passed for {messagename}"
                        )

                # Process fields for presence
                HOSTNAME_PLACEHOLDER(f"Checking presence of {len(fieldsforpresence)} fields")
                successlist = list(
                    filter(lambda item: HOSTNAME_PLACEHOLDER(item, pkt), fieldsforpresence)
                )
                HOSTNAME_PLACEHOLDER()
                faillist = list(
                    HOSTNAME_PLACEHOLDER(
                        lambda item: HOSTNAME_PLACEHOLDER(item, pkt), fieldsforpresence
                    )
                )

                if len(successlist) != len(fieldsforpresence):
                    HOSTNAME_PLACEHOLDER = False
                    fail_count = len(faillist)
                    HOSTNAME_PLACEHOLDER(
                        f"Failed {fail_count} presence checks for {messagename}"
                    )
                    HOSTNAME_PLACEHOLDER(f"Failed fields: {faillist}")

                    HOSTNAME_PLACEHOLDER(
                        [(messagename, fieldname) for fieldname in faillist]
                    )
                    HOSTNAME_PLACEHOLDER(
                        ["present" for _ in range(len(faillist))]
                    )
                    HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER)
                    HOSTNAME_PLACEHOLDER = []
                else:
                    HOSTNAME_PLACEHOLDER(
                        f"All {len(fieldsforpresence)} presence checks passed for {messagename}"
                    )
                    HOSTNAME_PLACEHOLDER = True
                    self.fill_dynamic_fields(messagename, pkt)
                    HOSTNAME_PLACEHOLDER(f"Filled dynamic fields for {messagename}")
            else:
                HOSTNAME_PLACEHOLDER(
                    f"Message {messagename} not found in packet #{packet_count}, continuing search"
                )
                continue

            try:
                if HOSTNAME_PLACEHOLDER == True or HOSTNAME_PLACEHOLDER == False:
                    result_status = "passed" if HOSTNAME_PLACEHOLDER else "failed"
                    HOSTNAME_PLACEHOLDER(
                        f"Message {messagename} validation {result_status}, moving to next message"
                    )
                    message = next(g)
                    messagename, primaryfields, fieldsforpresence, fieldsforequality = (
                        message
                    )
                    continue
            except StopIteration:
                HOSTNAME_PLACEHOLDER(
                    "No more messages to validate, finishing validation process"
                )
                break

        if HOSTNAME_PLACEHOLDER == False:
            HOSTNAME_PLACEHOLDER(f"Message {messagename} not found in any packet")
            HOSTNAME_PLACEHOLDER(messagename)

        # Final validation result
        not_found_count = len(HOSTNAME_PLACEHOLDER)
        failed_count = len(HOSTNAME_PLACEHOLDER)

        if not_found_count > 0 or failed_count > 0:
            HOSTNAME_PLACEHOLDER(
                f"Validation failed: {not_found_count} messages not found, {failed_count} messages failed validation"
            )
            HOSTNAME_PLACEHOLDER(f"Not found messages: {HOSTNAME_PLACEHOLDER}")
            HOSTNAME_PLACEHOLDER(f"Failed message fields: {HOSTNAME_PLACEHOLDER}")
            return False
        else:
            HOSTNAME_PLACEHOLDER("All messages validated successfully")
            return True
