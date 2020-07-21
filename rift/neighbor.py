import sortedcontainers

import constants
import utils

class Neighbor:
    """
    A node may have multiple parallel interfaces in state 3-way to the same neighbor. In that case
    there is single Neighbor object and there are multiple Interface objects (each having a
    NeighborLIE object to represent the LIE received from the Neighbor).
    """

    def __init__(self, system_id):
        self._system_id = system_id
        self._interfaces = {}             # Interfaces indexed by interface name
        self._ingress_bandwidth = 0       # Neighbor ingress bw = bw from this node to the neighbor
        self._egress_bandwidth = None     # Neighbor egress bw = bw from neighbor further north
        self._traffic_percentage = None

    def add_interface(self, intf):
        assert intf.name not in self._interfaces
        self._interfaces[intf.name] = intf
        self._ingress_bandwidth += intf.bandwidth

    def remove_interface(self, intf):
        assert intf.name in self._interfaces
        self._ingress_bandwidth -= intf.bandwidth
        del self._interfaces[intf.name]
        # Return whether or not the removed interface was the last one
        if self._interfaces:
            return False
        else:
            return True

    def interface_percentage(self, intf_name):
        assert intf_name in self._interfaces
        if self._traffic_percentage is None:
            return None
        intf = self._interfaces[intf_name]
        ingress_fraction = intf.bandwidth / self._ingress_bandwidth
        return ingress_fraction * self._traffic_percentage

    def interface_weight(self, intf_name):
        return round(self.interface_percentage(intf_name) * 10.0)

    def primary_interface(self):
        if not self._interfaces:
            return None
        primary_system_id = next(iter(self._interfaces))
        return self._interfaces[primary_system_id]

    def direction(self):
        return self.primary_interface().neighbor_direction()

    def ingress_bandwidth(self):
        return self._ingress_bandwidth

    def egress_bandwidth(self):
        return self._egress_bandwidth

    def set_egress_bandwidth(self, egress_bandwidth):
        self._egress_bandwidth = egress_bandwidth

    def set_traffic_percentage(self, percentage):
        self._traffic_percentage = percentage

    @staticmethod
    def cli_summary_headers():
        return [
            "System ID",
            "Direction",
            ["Interface", "Name"],
            ["Adjacency", "Name"]]

    def cli_summary_attributes(self):
        adj_names = sortedcontainers.SortedDict()
        for intf_name, intf in self._interfaces.items():
            adj_names[intf_name] = intf.neighbor_lie.name
        return [
            self._system_id,
            constants.direction_str(self.direction()),
            list(adj_names.keys()),
            [adj_name for adj_name in adj_names.values()]]

    @staticmethod
    def cli_bw_summary_headers():
        return [
            "System ID",
            ["Neighbor", "Ingress", "Bandwidth"],
            ["Neighbor", "Egress", "Bandwidth"],
            ["Neighbor", "Traffic", "Percentage"],
            ["Interface", "Name"],
            ["Interface", "Bandwidth"],
            ["Interface", "Traffic", "Percentage"]]

    def cli_bw_summary_attributes(self):
        nbr_percentage = self._traffic_percentage
        if nbr_percentage is None:
            intf_percentage_str = ""
        else:
            nbr_percentage_str = "{:.1f}".format(nbr_percentage) + " %"
        interface_infos = sortedcontainers.SortedDict()
        for intf_name, intf in self._interfaces.items():
            intf_bandwidth_str = utils.value_str(intf.bandwidth, "Mbps", "Mbps")
            intf_percentage = self.interface_percentage(intf_name)
            if intf_percentage is None:
                intf_percentage = ""
            else:
                intf_percentage_str = "{:.1f}".format(intf_percentage) + " %"
            interface_infos[intf_name] = (intf_bandwidth_str, intf_percentage_str)
        return [
            self._system_id,
            utils.value_str(self._ingress_bandwidth, "Mbps", "Mbps"),
            utils.value_str(self._egress_bandwidth, "Mbps", "Mbps"),
            nbr_percentage_str,
            list(interface_infos.keys()),
            [info[0] for info in interface_infos.values()],
            [info[1] for info in interface_infos.values()]]
