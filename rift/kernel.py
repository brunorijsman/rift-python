import socket

import pyroute2

import packet_common
import table

class Kernel:

    def __init__(self):
        # This will throw an exception on platforms where NETLINK is not supported such as macOS
        # (any platform other than Linux)
        try:
            self.ipr = pyroute2.IPRoute()
            self.platform_supported = True
        except OSError:
            self.ipr = None
            self.platform_supported = False

    def unsupported_platform_error(self, cli_session):
        if self.platform_supported:
            return False
        else:
            cli_session.print("Kernel networking not supported on this platform")
            return True

    def command_show_addresses(self, cli_session):
        if self.unsupported_platform_error(cli_session):
            return
        # TODO: Report fields (similar to index and flags in links)
        tab = table.Table()
        tab.add_row([
            ["Interface", "Name"],
            "Address",
            "Local",
            "Broadcast",
            "Anycast",
        ])
        for addr in self.ipr.get_addr():
            tab.add_row([
                addr.get_attr('IFA_LABEL'),
                addr.get_attr('IFA_ADDRESS'),
                addr.get_attr('IFA_LOCAL'),
                addr.get_attr('IFA_BROADCAST'),
                addr.get_attr('IFA_ANYCAST'),
            ])
        cli_session.print("Kernel Addresses:")
        cli_session.print(tab.to_string())

    def command_show_links(self, cli_session):
        if self.unsupported_platform_error(cli_session):
            return
        tab = table.Table()
        tab.add_row([
            ["Interface", "Name"],
            ["Interface", "Index"],
            ["Hardware", "Address"],
            ["Hardware", "Broadcast", "Address"],
            "Link Type",
            "MTU",
            "Flags",
        ])
        for link in self.ipr.get_links():
            tab.add_row([
                link.get_attr('IFLA_IFNAME'),
                link["index"],
                link.get_attr('IFLA_ADDRESS'),
                link.get_attr('IFLA_BROADCAST'),
                link.get_attr('IFLA_LINK'),
                link.get_attr('IFLA_MTU'),
                self.link_flags_to_str(link["flags"]),
            ])
        cli_session.print("Kernel Links:")
        cli_session.print(tab.to_string())

    @staticmethod
    def link_flags_to_str(flags):
        str_list = []
        bit_value = 1
        while flags != 0:
            if flags & 1:
                if bit_value in pyroute2.netlink.rtnl.ifinfmsg.IFF_VALUES:
                    flag_name = pyroute2.netlink.rtnl.ifinfmsg.IFF_VALUES[bit_value]
                    flag_name = flag_name.replace("IFF_", "")
                else:
                    flag_name = hex(bit_value)
                str_list.append(flag_name)
            bit_value *= 2
            flags >>= 1
        return str_list

    @staticmethod
    def route_row_key(row):
        table_nr = int(row[0])
        family_str = row[1]
        prefix_str = row[2]
        prefix = packet_common.make_ip_prefix(prefix_str)
        return (table_nr, family_str, prefix)

    @staticmethod
    def to_str(value):
        if value is None:
            return ""
        else:
            return str(value)

    @staticmethod
    def table_str(table_nr):
        if table_nr == 255:
            return "Local"
        elif table_nr == 254:
            return "Main"
        elif table_nr == 253:
            return "Default"
        else:
            return str(table_nr)

    @staticmethod
    def af_str(address_family):
        if address_family == socket.AF_INET:
            return "IPv4"
        elif address_family == socket.AF_INET6:
            return "IPv6"
        else:
            return str(address_family)

    def command_show_routes(self, cli_session):
        if self.unsupported_platform_error(cli_session):
            return
        # TODO: Report fields (similar to index and flags in links):
        # src_len, tos, table, proto, scope, type, flags
        rows = []
        for route in self.ipr.get_routes():
            family = route["family"]
            dst = route.get_attr('RTA_DST')
            if dst is None:
                if family == socket.AF_INET:
                    dst = "0.0.0.0/0"
                elif family == socket.AF_INET6:
                    dst = "::/0"
                else:
                    dst = "Default"
            else:
                dst_len = route["dst_len"]
                if dst_len is not None:
                    dst += "/" + str(dst_len)
            rows.append([
                route.get_attr('RTA_TABLE'),
                self.af_str(family),
                dst,
                route.get_attr('RTA_OIF'),
                self.to_str(route.get_attr('RTA_GATEWAY')),
                self.to_str(route.get_attr('RTA_PRIORITY')),
                self.to_str(route.get_attr('RTA_PREF')),
                self.to_str(route.get_attr('RTA_PREFSRC')),
            ])
        rows.sort(key=self.route_row_key)
        # Now that the output is sorted, replace number numbers with symbolic names
        for row in rows:
            row[0] = self.table_str(row[0])
        tab = table.Table()
        tab.add_row([
            "Table",
            ["Address", "Family"],
            "Destination",
            ["Outgoing", "Interface"],
            "Gateway",
            "Priority",
            "Preference",
            ["Preferred", "Source", "Address"]
        ])
        tab.add_rows(rows)
        cli_session.print("Kernel Routes:")
        cli_session.print(tab.to_string())

    def command_show_attribs(self, cli_session):
        if self.unsupported_platform_error(cli_session):
            return
        print("Link attributes:")
        self.show_object_attribs(self.ipr.get_links(), cli_session)
        print("Address attributes:")
        self.show_object_attribs(self.ipr.get_addr(), cli_session)
        print("Route attributes:")
        self.show_object_attribs(self.ipr.get_routes(), cli_session)

    @staticmethod
    def show_object_attribs(objects, cli_session):
        attributes = []
        for obj in objects:
            for (key, _) in obj["attrs"]:
                if key not in attributes:
                    attributes.append(key)
        tab = table.Table()
        for attribute in sorted(attributes):
            tab.add_row([attribute])
        cli_session.print(tab.to_string())
