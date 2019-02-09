import ipaddress

import next_hop

def test_next_hop_str():
    nhop = next_hop.NextHop("if1", ipaddress.IPv4Address("1.2.3.4"))
    assert str(nhop) == "if1 1.2.3.4"
    nhop = next_hop.NextHop("if1", ipaddress.IPv6Address("1111:1111::"))
    assert str(nhop) == "if1 1111:1111::"
    nhop = next_hop.NextHop("if2", None)
    assert str(nhop) == "if2"
    nhop = next_hop.NextHop(None, None)
    assert str(nhop) == ""

def test_next_hop_ordering():
    nhop1 = next_hop.NextHop(None, None)
    nhop2 = next_hop.NextHop("if1", None)
    nhop3 = next_hop.NextHop("if1", ipaddress.IPv4Address("1.1.1.1"))
    nhop4 = next_hop.NextHop("if1", ipaddress.IPv4Address("2.2.2.2"))
    nhop5 = next_hop.NextHop("if2", ipaddress.IPv4Address("1.1.1.1"))
    nhop6 = next_hop.NextHop("if2", ipaddress.IPv6Address("1111:1111::"))
    assert nhop1 < nhop2
    assert nhop2 < nhop3
    assert nhop3 < nhop4
    assert nhop4 < nhop5
    assert nhop5 < nhop6
    # pylint:disable=unneeded-not
    assert not nhop2 < nhop1
    assert not nhop3 < nhop2
    assert not nhop4 < nhop3
    assert not nhop5 < nhop4
    assert not nhop6 < nhop5
