import ipaddress

class NextHop:

    def __init__(self, interface, address):
        assert (interface is None) or isinstance(interface, str)
        assert ((address is None) or
                isinstance(address, (ipaddress.IPv4Address, ipaddress.IPv6Address)))
        self.interface = interface
        self.address = address

    def __str__(self):
        result_str = ""
        if self.interface is not None:
            result_str += self.interface
        if self.address is not None:
            if result_str != "":
                result_str += " "
            result_str += str(self.address)
        return result_str

    def __lt__(self, other):
        # String is not comparable with None
        if (self.interface is None) and (other.interface is not None):
            return True
        if (self.interface is not None) and (other.interface is None):
            return False
        if self.interface < other.interface:
            return True
        if self.interface > other.interface:
            return False
        # Address is not comparable with None
        if (self.address is None) and (other.address is not None):
            return True
        if (self.address is not None) and (other.address is None):
            return False
        # Address of different address families are not comparable
        if (isinstance(self.address, ipaddress.IPv4Address) and
                isinstance(other.address, ipaddress.IPv6Address)):
            return True
        if (isinstance(self.address, ipaddress.IPv6Address) and
                isinstance(other.address, ipaddress.IPv4Address)):
            return False
        return self.address < other.address
