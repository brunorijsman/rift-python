class Neighbor:
    """
    A node may have multiple parallel interfaces in state 3-way to the same neighbor. In that case
    there is single Neighbor object and there are multiple Interface objects (each having a
    NeighborLIE object to represent the LIE received from the Neighbor).
    """

    def __init__(self, system_id):
        self._system_id = system_id
        self._interfaces = {}    # Reference to Interface object indexed by interface name

    def add_interface(self, intf):
        assert intf.name not in self._interfaces
        self._interfaces[intf.name] = intf

    def remove_interface(self, intf):
        assert intf.name in self._interfaces
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

    @staticmethod
    def cli_summary_headers():
        return [
            "System ID",
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
            interface_names,
            adjacency_names]
