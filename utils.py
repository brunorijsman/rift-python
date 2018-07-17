import netifaces

def interface_ipv4_address(interface_name, log = None):
    default_interface_ipv4_address = ''
    interface_addresses = netifaces.interfaces()
    if not interface_name in netifaces.interfaces():
        if log:
            log.warning('Cannot determine IPv4 address: interface {} does not exists'.format(interface_name))
        return default_interface_ipv4_address
    interface_addresses = netifaces.ifaddresses(interface_name)
    if not netifaces.AF_INET in interface_addresses:
        if log:
            log.warning('Interface {} does not have an IPv4 address'.format(interface_name))
        return default_interface_ipv4_address
    return interface_addresses[netifaces.AF_INET][0]['addr']

def system_id_str(system_id):
    # Heuristic: if the system_id < 1000000 then it is probably configured, otherwise it is probably
    # derived from the MAC address, the process ID, and the node nr.
    if system_id < 1000000:
        return "{}".format(system_id)
    else:
        return "{:016x}".format(system_id)
