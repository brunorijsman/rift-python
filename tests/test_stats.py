import stats

def counter_add_wrapper(counter, simulated_time, add_value):
    stats.TIME_FUNCTION = lambda: simulated_time
    counter.add(add_value)

def test_group():
    group = stats.Group()
    _counter_1 = stats.Counter(group, "Sent Packets", "Packet")
    _counter_1.increase()
    _counter_2 = stats.Counter(group, "Received Packets", "Packet")
    _counter_3 = stats.Counter(group, "Dropped Packets", "Packet")
    counter_add_wrapper(_counter_3, 1.00, 5)
    counter_add_wrapper(_counter_3, 3.00, 6)
    counter_add_wrapper(_counter_3, 4.00, 3)
    _counter_4 = stats.MultiCounter(group, "Sent Hellos", ["Packet", "Byte"])
    _counter_5 = stats.MultiCounter(group, "Received Hellos", ["Packet", "Byte"])
    counter_add_wrapper(_counter_5, 12.00, [2, 33])
    counter_add_wrapper(_counter_5, 13.00, [1, 12])
    _counter_6 = stats.MultiCounter(group, "Sent Byes", ["Packet", "Byte"])
    counter_add_wrapper(_counter_6, 13.00, [9, 1023])
    _counter_7 = stats.MultiCounter(group, "Received Byes", ["Packet", "Byte"])
    counter_add_wrapper(_counter_7, 14.00, [1, 10])
    counter_add_wrapper(_counter_7, 14.00, [1, 10])
    assert group.table(exclude_zero=False).to_string() == (
        "+------------------+-----------------------+------------------------------------------+\n"
        "| Description      | Value                 | Recent Rate                              |\n"
        "|                  |                       | Over Last 5 Changes                      |\n"
        "+------------------+-----------------------+------------------------------------------+\n"
        "| Sent Packets     | 1 Packet              |                                          |\n"
        "+------------------+-----------------------+------------------------------------------+\n"
        "| Received Packets | 0 Packets             |                                          |\n"
        "+------------------+-----------------------+------------------------------------------+\n"
        "| Dropped Packets  | 14 Packets            | 3.00 Packets/Sec                         |\n"
        "+------------------+-----------------------+------------------------------------------+\n"
        "| Sent Hellos      | 0 Packets, 0 Bytes    |                                          |\n"
        "+------------------+-----------------------+------------------------------------------+\n"
        "| Received Hellos  | 3 Packets, 45 Bytes   | 1.00 Packets/Sec, 12.00 Bytes/Sec        |\n"
        "+------------------+-----------------------+------------------------------------------+\n"
        "| Sent Byes        | 9 Packets, 1023 Bytes |                                          |\n"
        "+------------------+-----------------------+------------------------------------------+\n"
        "| Received Byes    | 2 Packets, 20 Bytes   | Infinite Packets/Sec, Infinite Bytes/Sec |\n"
        "+------------------+-----------------------+------------------------------------------+\n")
    assert group.table(exclude_zero=True).to_string() == (
        "+-----------------+-----------------------+------------------------------------------+\n"
        "| Description     | Value                 | Recent Rate                              |\n"
        "|                 |                       | Over Last 5 Changes                      |\n"
        "+-----------------+-----------------------+------------------------------------------+\n"
        "| Sent Packets    | 1 Packet              |                                          |\n"
        "+-----------------+-----------------------+------------------------------------------+\n"
        "| Dropped Packets | 14 Packets            | 3.00 Packets/Sec                         |\n"
        "+-----------------+-----------------------+------------------------------------------+\n"
        "| Received Hellos | 3 Packets, 45 Bytes   | 1.00 Packets/Sec, 12.00 Bytes/Sec        |\n"
        "+-----------------+-----------------------+------------------------------------------+\n"
        "| Sent Byes       | 9 Packets, 1023 Bytes |                                          |\n"
        "+-----------------+-----------------------+------------------------------------------+\n"
        "| Received Byes   | 2 Packets, 20 Bytes   | Infinite Packets/Sec, Infinite Bytes/Sec |\n"
        "+-----------------+-----------------------+------------------------------------------+\n")

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
