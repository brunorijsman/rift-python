import stats

def test_group():
    group = stats.Group()
    _counter_1 = stats.Counter(group, "Sent Packets", "Packet")
    _counter_1.increase()
    _counter_2 = stats.Counter(group, "Received Packets", "Packet")
    _counter_3 = stats.Counter(group, "Dropped Packets", "Packet")
    _counter_3.add(5)
    assert group.table(exclude_zero=False).to_string() == (
        "+------------------+-----------+\n"
        "| Description      | Value     |\n"
        "+------------------+-----------+\n"
        "| Sent Packets     | 1 Packet  |\n"
        "+------------------+-----------+\n"
        "| Received Packets | 0 Packets |\n"
        "+------------------+-----------+\n"
        "| Dropped Packets  | 5 Packets |\n"
        "+------------------+-----------+\n")
    assert group.table(exclude_zero=True).to_string() == (
        "+-----------------+-----------+\n"
        "| Description     | Value     |\n"
        "+-----------------+-----------+\n"
        "| Sent Packets    | 1 Packet  |\n"
        "+-----------------+-----------+\n"
        "| Dropped Packets | 5 Packets |\n"
        "+-----------------+-----------+\n")

def test_counter():
    group = stats.Group()
    counter_1 = stats.Counter(group, "RX TIE Packets", "Packet")
    assert counter_1.description == "RX TIE Packets"
    assert counter_1.value == 0
    assert counter_1.value_with_units == "0 Packets"
    counter_1.increase()
    assert counter_1.value == 1
    assert counter_1.value_with_units == "1 Packet"
    counter_1.increase()
    assert counter_1.value == 2
    assert counter_1.value_with_units == "2 Packets"
    counter_1.add(7)
    assert counter_1.value == 9
    assert counter_1.value_with_units == "9 Packets"
    counter_2 = stats.Counter(group, "Caught Fish", "Fish", "Fish")
    assert counter_2.description == "Caught Fish"
    assert counter_2.value == 0
    assert counter_2.value_with_units == "0 Fish"
    counter_2.increase()
    assert counter_2.value == 1
    assert counter_2.value_with_units == "1 Fish"
