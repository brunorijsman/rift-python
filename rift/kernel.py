import errno
import socket

import pyroute2

import packet_common
import table

RTPROT_RIFT = 99

class Kernel:

    def __init__(self, table_name, log, log_id):
        self._table_name = table_name
        if isinstance(table_name, int):
            self._table_nr = table_name
        else:
            self._table_nr = self.table_name_to_nr(table_name)
        self._log = log
        self._log_id = log_id
        self.debug("Create kernel using route table %s" % table_name)
        try:
            self.ipr = pyroute2.IPRoute()
            self.platform_supported = True
            self.debug("Kernel networking is supported on this platform")
        except OSError:
            self.ipr = None
            self.platform_supported = False
            self.warning("Kernel networking is not supported on this platform")

    def debug(self, msg, *args):
        if self._log:
            self._log.debug("[%s] %s" % (self._log_id, msg), *args)

    def warning(self, msg, *args):
        if self._log:
            self._log.warning("[%s] %s" % (self._log_id, msg), *args)

    def error(self, msg, *args):
        if self._log:
            self._log.error("[%s] %s" % (self._log_id, msg), *args)

    def unsupported_platform_error(self, cli_session):
        if self.platform_supported:
            return False
        else:
            cli_session.print("Kernel networking not supported on this platform")
            return True

    def put_route(self, rte):
        if not self.platform_supported:
            return
        if self._table_nr == -1:
            return
        dst = str(rte.prefix)
        if rte.next_hops == []:
            kernel_args = {}
        elif len(rte.next_hops) == 1:
            nhop = rte.next_hops[0]
            kernel_args = self.nhop_to_kernel_args(nhop, dst)
            if kernel_args == {}:
                self.del_route(rte.prefix)
                return
        else:
            kernel_args = {"multipath": []}
            for nhop in rte.next_hops:
                nhop_args = self.nhop_to_kernel_args(nhop, dst)
                if nhop_args:
                    kernel_args["multipath"].append(nhop_args)
            if kernel_args["multipath"] == []:
                self.del_route(rte.prefix)
                return
        try:
            self.ipr.route('replace',
                           table=self._table_nr,
                           dst=dst,
                           proto=RTPROT_RIFT,
                           **kernel_args)
        except pyroute2.netlink.exceptions.NetlinkError as err:
            self.error("Netlink error %s replacing route to %s: %s", err, dst, kernel_args)
        except OSError as err:
            self.error("OS error \"%s\" replacing route to %s: %s", err, dst, kernel_args)
        else:
            self.debug("Replace route to \"%s\": %s", dst, kernel_args)

    def del_route(self, prefix):
        if not self.platform_supported:
            return
        if self._table_nr == -1:
            return
        dst = str(prefix)
        try:
            self.ipr.route('del', table=self._table_nr, dst=dst, proto=RTPROT_RIFT)
        except pyroute2.netlink.exceptions.NetlinkError as err:
            if err.code != errno.ESRCH:  # It is not an error to delete a non-existing route
                self.error("Netlink error \"%s\" deleting route to %s", err, dst)
        except OSError as err:
            self.error("OS error \"%s\" deleting route to %s", err, dst)
        else:
            self.debug("Delete route to %s", prefix)

    def nhop_to_kernel_args(self, nhop, dst):
        link = self.ipr.link_lookup(ifname=nhop.interface)
        if link == []:
            self.error("Unknown interface \"%s\" replacing route to %s", nhop.interface, dst)
            return {}
        oif = link[0]
        if nhop.address is None:
            kernel_args = {"oif": oif, "hops": 1}
        else:
            gateway = str(nhop.address)
            kernel_args = {"oif": oif, "gateway": gateway, "hops": 1}
        return kernel_args

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
                self.to_str(addr.get_attr('IFA_LABEL')),
                self.to_str(addr.get_attr('IFA_ADDRESS')),
                self.to_str(addr.get_attr('IFA_LOCAL')),
                self.to_str(addr.get_attr('IFA_BROADCAST')),
                self.to_str(addr.get_attr('IFA_ANYCAST')),
            ])
        cli_session.print("Kernel Addresses:")
        cli_session.print(tab.to_string())

    def cli_links_table(self):
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
                self.to_str(link.get_attr('IFLA_IFNAME')),
                self.to_str(link["index"]),
                self.to_str(link.get_attr('IFLA_ADDRESS')),
                self.to_str(link.get_attr('IFLA_BROADCAST')),
                self.to_str(link.get_attr('IFLA_LINK')),
                self.to_str(link.get_attr('IFLA_MTU')),
                self.link_flags_to_str(link["flags"]),
            ])
        return tab

    def command_show_links(self, cli_session):
        if self.unsupported_platform_error(cli_session):
            return
        tab = self.cli_links_table()
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
    def table_nr_to_name(table_nr):
        if table_nr == 255:
            return "Local"
        elif table_nr == 254:
            return "Main"
        elif table_nr == 253:
            return "Default"
        elif table_nr == 0:
            return "Unspecified"
        elif table_nr == -1:
            return "None"
        else:
            return str(table_nr)

    @staticmethod
    def table_name_to_nr(table_name):
        lower_name = table_name.lower()
        if lower_name == "local":
            return 255
        elif lower_name == "main":
            return 254
        elif lower_name == "default":
            return 253
        elif lower_name == "unspecified":
            return 0
        elif lower_name == "none":
            return -1
        else:
            return int(table_name)

    @staticmethod
    def first_letter_uppercase(string):
        if string == "":
            return string
        first_letter = string[0]
        rest = string[1:]
        return first_letter.upper() + rest

    @staticmethod
    def route_type_str(route_type):
        if route_type in pyroute2.netlink.rtnl.rt_type:
            route_type_str = pyroute2.netlink.rtnl.rt_type[route_type]
            route_type_str = Kernel.first_letter_uppercase(route_type_str)
        else:
            route_type_str = str(route_type)
        return route_type_str

    @staticmethod
    def proto_str(proto):
        if proto in pyroute2.netlink.rtnl.rt_proto:
            proto_str = pyroute2.netlink.rtnl.rt_proto[proto]
            proto_str = Kernel.first_letter_uppercase(proto_str)
        elif proto == RTPROT_RIFT:
            proto_str = "RIFT"
        else:
            proto_str = str(proto)
        return proto_str

    @staticmethod
    def af_str(address_family):
        if address_family == socket.AF_INET:
            return "IPv4"
        elif address_family == socket.AF_INET6:
            return "IPv6"
        else:
            return str(address_family)

    @staticmethod
    def interface_index_to_name(interface_index, links):
        for link in links:
            if link["index"] == interface_index:
                return link.get_attr('IFLA_IFNAME')
        return str(interface_index)

    @staticmethod
    def kernel_route_dst_prefix_str(route):
        dst = route.get_attr('RTA_DST')
        if dst is None:
            family = route["family"]
            if family == socket.AF_INET:
                prefix_str = "0.0.0.0/0"
            elif family == socket.AF_INET6:
                prefix_str = "::/0"
            else:
                prefix_str = "Default"
        else:
            prefix_str = dst
            dst_len = route["dst_len"]
            if dst_len is not None:
                prefix_str += "/" + str(dst_len)
        return prefix_str

    @staticmethod
    def kernel_route_src_prefix_str(route):
        src = route.get_attr('RTA_SRC')
        if src is None:
            return ""
        else:
            prefix_str = src
            src_len = route["src_len"]
            if src_len is not None:
                prefix_str += "/" + str(src_len)
        return prefix_str

    @staticmethod
    def kernel_route_multipath_nhops(route, links):
        # Returns a list of three-tuples: [(oif_str, gateway_str, weight_str)]
        multipath_list = route.get_attr('RTA_MULTIPATH')
        if multipath_list is None:
            return []
        next_hops_list = []
        for path in multipath_list:
            # TODO: Add support for path["flags"].
            if "oif" in path:
                oif_index = path["oif"]
                oif_str = Kernel.interface_index_to_name(oif_index, links)
            else:
                oif_str = ""
            if "attrs" in path:
                attr_list = path["attrs"]
            else:
                attr_list = []
            gateway_str = ""
            for (attr_name, attr_value) in attr_list:
                if attr_name == "RTA_GATEWAY":
                    gateway_str = attr_value
                    break
            if "hops" in path:
                weight_str = path["hops"]
            else:
                weight_str = ""
            nhop = (oif_str, gateway_str, weight_str)
            next_hops_list.append(nhop)
        return next_hops_list

    @staticmethod
    def kernel_route_nhops(route, links):
        oif = route.get_attr('RTA_OIF')
        multipath = route.get_attr('RTA_MULTIPATH')
        assert (oif is None) or (multipath is None)  # Can't have OIF and MULTIPATH
        if oif is not None:
            oif_str = Kernel.interface_index_to_name(oif, links)
            gateway_str = Kernel.to_str(route.get_attr('RTA_GATEWAY'))
            weight_str = ""
            next_hops = [(oif_str, gateway_str, weight_str)]
        elif multipath is not None:
            next_hops = Kernel.kernel_route_multipath_nhops(route, links)
        else:
            next_hops = []
        return next_hops

    def command_show_routes(self, cli_session, table_nr):
        # pylint:disable=too-many-locals
        if self.unsupported_platform_error(cli_session):
            return
        links = self.ipr.get_links()
        rows = []
        for route in self.ipr.get_routes():
            family = route["family"]
            dst_prefix_str = self.kernel_route_dst_prefix_str(route)
            route_table_nr = route.get_attr('RTA_TABLE')
            if (table_nr is not None) and (table_nr != route_table_nr):
                continue
            next_hops = self.kernel_route_nhops(route, links)
            oif_cell = []
            gateway_cell = []
            weight_cell = []
            for nhop in next_hops:
                oif_cell.append(nhop[0])
                gateway_cell.append(nhop[1])
                weight_cell.append(nhop[2])
            rows.append([route_table_nr,
                         self.af_str(family),
                         dst_prefix_str,
                         self.route_type_str(route["type"]),
                         self.proto_str(route["proto"]),
                         oif_cell,
                         gateway_cell,
                         weight_cell])
        rows.sort(key=self.route_row_key)
        # Now that the output is sorted, replace number numbers with symbolic names
        for row in rows:
            row[0] = self.table_nr_to_name(row[0])
        tab = table.Table()
        tab.add_row(["Table",
                     ["Address", "Family"],
                     "Destination",
                     "Type",
                     "Protocol",
                     ["Outgoing", "Interface"],
                     "Gateway",
                     "Weight"])
        tab.add_rows(rows)
        cli_session.print("Kernel Routes:")
        cli_session.print(tab.to_string())

    def command_show_route_prefix(self, cli_session, table_nr, prefix):
        # TODO: Add support for:
        # - Attribute RTA_FLOW
        # - Attribute RTA_ENCAP_TYPE
        # - Attribute RTA_ENCAP
        # - Attribute RTA_METRICS
        # - Field tos
        # - Field flags
        # - Field scope
        if self.unsupported_platform_error(cli_session):
            return
        route = None
        for rte in self.ipr.get_routes():
            route_table_nr = rte.get_attr('RTA_TABLE')
            dst_prefix_str = self.kernel_route_dst_prefix_str(rte)
            if (table_nr == route_table_nr) and (dst_prefix_str == str(prefix)):
                route = rte
                break
        if route is None:
            cli_session.print('Prefix "{}" in table "{}" not present in kernel route table'
                              .format(prefix, self.table_nr_to_name(table_nr)))
            return
        links = self.ipr.get_links()
        tab = table.Table(separators=False)
        next_hops = self.kernel_route_nhops(route, links)
        next_hops_cell = []
        for nhop in next_hops:
            next_hop_str = str(nhop[0]) + " " + str(nhop[1]) + " " + str(nhop[2])
            next_hops_cell.append(next_hop_str)
        tab.add_row(["Table", self.table_nr_to_name(table_nr)])
        tab.add_row(["Address Family", self.af_str(self.af_str(route["family"]))])
        tab.add_row(["Destination", str(prefix)])
        tab.add_row(["Type", self.route_type_str(route["type"])])
        tab.add_row(["Protocol", self.proto_str(route["proto"])])
        tab.add_row(["Next-hops", next_hops_cell])
        tab.add_row(["Priority", self.to_str(route.get_attr('RTA_PRIORITY'))])
        tab.add_row(["Preference", self.to_str(route.get_attr('RTA_PREF'))])
        tab.add_row(["Preferred Source Address", self.to_str(route.get_attr('RTA_PREFSRC'))])
        tab.add_row(["Source", self.kernel_route_src_prefix_str(route)])
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
