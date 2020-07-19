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
        self._interfaces = {}            # Interfaces indexed by interface name
        self._ingress_bandwidth = 0      # Neighbor ingress bw = bw from this node to the neighbor
        self._egress_bandwidth = None     # Neighbor egress bw = bw from neighbor further north

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

    def primary_interface(self):
        if not self._interfaces:
            return None
        primary_system_id = next(iter(self._interfaces))
        return self._interfaces[primary_system_id]

    def direction(self):
        return self.primary_interface().neighbor_direction()

    def set_egress_bandwidth(self, egress_bandwidth):
        self._egress_bandwidth = egress_bandwidth

    @staticmethod
    def cli_summary_headers():
        return [
            "System ID",
            "Direction",
            ["Interface", "Name"],
            ["Adjacency", "Name"]]

    def cli_summary_attributes(self):
        interface_names = []
        adjacency_names = []
        for intf_name, intf in self._interfaces.items():
            interface_names.append(intf_name)
            adjacency_names.append(intf.neighbor_lie.name)
        return [
            self._system_id,
            constants.direction_str(self.direction()),
            interface_names,
            adjacency_names]

    @staticmethod
    def cli_bw_summary_headers():
        return [
            "System ID",
            ["Neighbor", "Ingress", "North-Bound", "Bandwidth"],
            ["Neighbor", "Egress", "North-Bound", "Bandwidth"],
            ["Neighbor", "Traffic", "Percentage"],
            ["Interface", "Name"],
            ["Interface", "Traffic", "Percentage"]]

    def cli_bw_summary_attributes(self):
        interface_names = []
        interface_percentages = []
        for intf_name in self._interfaces:
            interface_names.append(intf_name)
            interface_percentages.append("10%")  ###@@@
        return [
            self._system_id,
            utils.value_str(self._ingress_bandwidth, "Mbps", "Mbps"),
            utils.value_str(self._egress_bandwidth, "Mbps", "Mbps"),
            "50%",   ###@@@
            interface_names,
            interface_percentages]
