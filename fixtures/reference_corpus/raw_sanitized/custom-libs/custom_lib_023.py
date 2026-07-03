from SOURCE_NAME_PLACEHOLDER import SOURCE_NAME_PLACEHOLDER
import logging


class SOURCE_NAME_PLACEHOLDER(SOURCE_NAME_PLACEHOLDER):
    def __init__(self, pcap_file_path, filter, search_fields=None):
        super().__init__(pcap_file_path, filter)
        self.cdr_search_fields = search_fields

    def get_charging_id(self):
        return self.cdr_search_fields["charging_id"]

    def get_apn_name(self):
        return self.cdr_search_fields["apn"]

    def fill_dynamic_fields(self, messagename, pkt):
        HOSTNAME_PLACEHOLDER("filling dynamic fields")
        if (
            messagename == "Create Session Response"
            or messagename == "MME to SGW Create Session Request"
        ):
            # Update the CharingID in searh field
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
                    HOSTNAME_PLACEHOLDER("filling search field")
                    HOSTNAME_PLACEHOLDER(self.cdr_search_fields)
                    HOSTNAME_PLACEHOLDER(dest_field)
                    self.cdr_search_fields[dest_field] = source_pkt_value
                except KeyError:
                    print("not found")
