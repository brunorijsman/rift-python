import stats

def test_group():
    group = stats.Group()
    _counter_1 = stats.Counter(group, "Sent Packets", "Packet")
    _counter_1.increase()
    _counter_2 = stats.Counter(group, "Received Packets", "Packet")
    _counter_3 = stats.Counter(group, "Dropped Packets", "Packet")
    _counter_3.add(5)
    _counter_4 = stats.MultiCounter(group, "Sent Hellos", ["Packet", "Byte"])
    _counter_5 = stats.MultiCounter(group, "Received Hellos", ["Packet", "Byte"])
    _counter_5.add([2, 33])
    assert group.table(exclude_zero=False).to_string() == (
        "+------------------+---------------------+\n"
        "| Description      | Value               |\n"
        "+------------------+---------------------+\n"
        "| Sent Packets     | 1 Packet            |\n"
        "+------------------+---------------------+\n"
        "| Received Packets | 0 Packets           |\n"
        "+------------------+---------------------+\n"
        "| Dropped Packets  | 5 Packets           |\n"
        "+------------------+---------------------+\n"
        "| Sent Hellos      | 0 Packets, 0 Bytes  |\n"
        "+------------------+---------------------+\n"
        "| Received Hellos  | 2 Packets, 33 Bytes |\n"
        "+------------------+---------------------+\n")
    assert group.table(exclude_zero=True).to_string() == (
        "+-----------------+---------------------+\n"
        "| Description     | Value               |\n"
        "+-----------------+---------------------+\n"
        "| Sent Packets    | 1 Packet            |\n"
        "+-----------------+---------------------+\n"
        "| Dropped Packets | 5 Packets           |\n"
        "+-----------------+---------------------+\n"
        "| Received Hellos | 2 Packets, 33 Bytes |\n"
        "+-----------------+---------------------+\n")

def test_counter():
    group = stats.Group()
    counter_1 = stats.Counter(group, "RX TIE Packets", "Packet")
    assert counter_1.description() == "RX TIE Packets"
    assert counter_1.value_display_str() == "0 Packets"
    assert counter_1.is_zero()
    counter_1.increase()
    assert counter_1.value_display_str() == "1 Packet"
    assert not counter_1.is_zero()
    counter_1.increase()
    assert counter_1.value_display_str() == "2 Packets"
    assert not counter_1.is_zero()
    counter_1.add(7)
    assert counter_1.value_display_str() == "9 Packets"
    assert not counter_1.is_zero()
    counter_2 = stats.Counter(group, "Caught Fish", "Fish", "Fish")
    assert counter_2.description() == "Caught Fish"
    assert counter_2.value_display_str() == "0 Fish"
    assert counter_2.is_zero()
    counter_2.increase()
    assert counter_2.value_display_str() == "1 Fish"
    assert not counter_2.is_zero()

def test_multi_counter():
    group = stats.Group()
    counter_1 = stats.MultiCounter(group, "RX TIE Packets", ["Packet", "Byte"])
    assert counter_1.description() == "RX TIE Packets"
    assert counter_1.value_display_str() == "0 Packets, 0 Bytes"
    assert counter_1.is_zero()
    counter_1.add([1, 0])
    assert counter_1.value_display_str() == "1 Packet, 0 Bytes"
    assert not counter_1.is_zero()
    counter_1.add([0, 1])
    assert counter_1.value_display_str() == "1 Packet, 1 Byte"
    assert not counter_1.is_zero()
    counter_1.add([2, 66])
    assert counter_1.value_display_str() == "3 Packets, 67 Bytes"
    assert not counter_1.is_zero()
    counter_2 = stats.MultiCounter(group, "Caught Fish", ["Fish", "Gram"], ["Fish", "Grams"])
    assert counter_2.value_display_str() == "0 Fish, 0 Grams"
    assert counter_2.is_zero()
    counter_2.add([1, 0])
    assert counter_2.value_display_str() == "1 Fish, 0 Grams"
    assert not counter_2.is_zero()
    counter_2.add([0, 1])
    assert counter_2.value_display_str() == "1 Fish, 1 Gram"
    assert not counter_2.is_zero()
    counter_2.add([2, 66])
    assert counter_2.value_display_str() == "3 Fish, 67 Grams"
    assert not counter_2.is_zero()
