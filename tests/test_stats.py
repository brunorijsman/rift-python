import stats

#pylint:disable=line-too-long

def counter_increase_wrapper(counter, simulated_time):
    stats.TIME_FUNCTION = lambda: simulated_time
    counter.increase()

def counter_add_wrapper(counter, simulated_time, add_value):
    stats.TIME_FUNCTION = lambda: simulated_time
    counter.add(add_value)

def test_group():
    group = stats.Group()
    _counter_1 = stats.Counter(group, "Sent Packets", "Packet")
    counter_increase_wrapper(_counter_1, 0.00)
    _counter_2 = stats.Counter(group, "Received Packets", "Packet")
    _counter_3 = stats.Counter(group, "Dropped Packets", "Packet")
    counter_add_wrapper(_counter_3, 1.00, 5)
    counter_add_wrapper(_counter_3, 3.00, 6)
    counter_add_wrapper(_counter_3, 4.00, 3)
    counter_hellos = stats.MultiCounter(None, "Total Hellos", ["Packet", "Byte"])
    _counter_4 = stats.MultiCounter(group, "Sent Hellos", ["Packet", "Byte"],
                                    sum_counters=[counter_hellos])
    _counter_5 = stats.MultiCounter(group, "Received Hellos", ["Packet", "Byte"],
                                    sum_counters=[counter_hellos])
    counter_hellos.add_to_group(group)
    counter_add_wrapper(_counter_5, 12.00, [2, 33])
    counter_add_wrapper(_counter_5, 13.00, [1, 12])
    counter_byes = stats.MultiCounter(None, "Total Byes", ["Packet", "Byte"])
    _counter_6 = stats.MultiCounter(group, "Sent Byes", ["Packet", "Byte"],
                                    sum_counters=[counter_byes])
    counter_add_wrapper(_counter_6, 13.00, [9, 1023])
    _counter_7 = stats.MultiCounter(group, "Received Byes", ["Packet", "Byte"],
                                    sum_counters=[counter_byes])
    counter_byes.add_to_group(group)
    counter_add_wrapper(_counter_7, 14.00, [1, 10])
    counter_add_wrapper(_counter_7, 14.00, [1, 10])
    stats.TIME_FUNCTION = lambda: 15.00
    assert group.table(exclude_zero=False).to_string() == (
        "+------------------+------------------------+------------------------------------------+-------------------+\n"
        "| Description      | Value                  | Last Rate                                | Last Change       |\n"
        "|                  |                        | Over Last 5 Changes                      |                   |\n"
        "+------------------+------------------------+------------------------------------------+-------------------+\n"
        "| Sent Packets     | 1 Packet               |                                          | 0d 00h:00m:15.00s |\n"
        "+------------------+------------------------+------------------------------------------+-------------------+\n"
        "| Received Packets | 0 Packets              |                                          |                   |\n"
        "+------------------+------------------------+------------------------------------------+-------------------+\n"
        "| Dropped Packets  | 14 Packets             | 3.00 Packets/Sec                         | 0d 00h:00m:11.00s |\n"
        "+------------------+------------------------+------------------------------------------+-------------------+\n"
        "| Sent Hellos      | 0 Packets, 0 Bytes     |                                          |                   |\n"
        "+------------------+------------------------+------------------------------------------+-------------------+\n"
        "| Received Hellos  | 3 Packets, 45 Bytes    | 1.00 Packets/Sec, 12.00 Bytes/Sec        | 0d 00h:00m:02.00s |\n"
        "+------------------+------------------------+------------------------------------------+-------------------+\n"
        "| Total Hellos     | 3 Packets, 45 Bytes    | 1.00 Packets/Sec, 12.00 Bytes/Sec        | 0d 00h:00m:02.00s |\n"
        "+------------------+------------------------+------------------------------------------+-------------------+\n"
        "| Sent Byes        | 9 Packets, 1023 Bytes  |                                          | 0d 00h:00m:02.00s |\n"
        "+------------------+------------------------+------------------------------------------+-------------------+\n"
        "| Received Byes    | 2 Packets, 20 Bytes    | Infinite Packets/Sec, Infinite Bytes/Sec | 0d 00h:00m:01.00s |\n"
        "+------------------+------------------------+------------------------------------------+-------------------+\n"
        "| Total Byes       | 11 Packets, 1043 Bytes | 2.00 Packets/Sec, 20.00 Bytes/Sec        | 0d 00h:00m:01.00s |\n"
        "+------------------+------------------------+------------------------------------------+-------------------+\n")
    assert group.table(exclude_zero=True).to_string() == (
        "+-----------------+------------------------+------------------------------------------+-------------------+\n"
        "| Description     | Value                  | Last Rate                                | Last Change       |\n"
        "|                 |                        | Over Last 5 Changes                      |                   |\n"
        "+-----------------+------------------------+------------------------------------------+-------------------+\n"
        "| Sent Packets    | 1 Packet               |                                          | 0d 00h:00m:15.00s |\n"
        "+-----------------+------------------------+------------------------------------------+-------------------+\n"
        "| Dropped Packets | 14 Packets             | 3.00 Packets/Sec                         | 0d 00h:00m:11.00s |\n"
        "+-----------------+------------------------+------------------------------------------+-------------------+\n"
        "| Received Hellos | 3 Packets, 45 Bytes    | 1.00 Packets/Sec, 12.00 Bytes/Sec        | 0d 00h:00m:02.00s |\n"
        "+-----------------+------------------------+------------------------------------------+-------------------+\n"
        "| Total Hellos    | 3 Packets, 45 Bytes    | 1.00 Packets/Sec, 12.00 Bytes/Sec        | 0d 00h:00m:02.00s |\n"
        "+-----------------+------------------------+------------------------------------------+-------------------+\n"
        "| Sent Byes       | 9 Packets, 1023 Bytes  |                                          | 0d 00h:00m:02.00s |\n"
        "+-----------------+------------------------+------------------------------------------+-------------------+\n"
        "| Received Byes   | 2 Packets, 20 Bytes    | Infinite Packets/Sec, Infinite Bytes/Sec | 0d 00h:00m:01.00s |\n"
        "+-----------------+------------------------+------------------------------------------+-------------------+\n"
        "| Total Byes      | 11 Packets, 1043 Bytes | 2.00 Packets/Sec, 20.00 Bytes/Sec        | 0d 00h:00m:01.00s |\n"
        "+-----------------+------------------------+------------------------------------------+-------------------+\n")
    group.clear()
    counter_increase_wrapper(_counter_1, 16.00)
    counter_increase_wrapper(_counter_1, 17.00)
    stats.TIME_FUNCTION = lambda: 19.00
    assert group.table(exclude_zero=True).to_string() == (
        "+--------------+-----------+---------------------+-------------------+\n"
        "| Description  | Value     | Last Rate           | Last Change       |\n"
        "|              |           | Over Last 5 Changes |                   |\n"
        "+--------------+-----------+---------------------+-------------------+\n"
        "| Sent Packets | 2 Packets | 1.00 Packets/Sec    | 0d 00h:00m:02.00s |\n"
        "+--------------+-----------+---------------------+-------------------+\n")

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

def test_sum_counter():
    # pylint:disable=too-many-statements
    group = stats.Group()
    counter_total_rx = stats.Counter(group, "Total RX Packets", "Packet")
    counter_total_tx = stats.Counter(group, "Total TX Packets", "Packet")
    counter_total_foo = stats.Counter(None, "Total Foo Packets", "Packet")
    counter_total_bar = stats.Counter(None, "Total Bar Packets", "Packet")
    counter_rx_foo = stats.Counter(group, "RX Foo Packets", "Packet",
                                   sum_counters=[counter_total_rx, counter_total_foo])
    counter_tx_foo = stats.Counter(group, "TX Foo Packets", "Packet",
                                   sum_counters=[counter_total_tx, counter_total_foo])
    counter_rx_bar = stats.Counter(group, "RX Bar Packets", "Packet",
                                   sum_counters=[counter_total_rx, counter_total_bar])
    counter_tx_bar = stats.Counter(group, "TX Bar Packets", "Packet",
                                   sum_counters=[counter_total_tx, counter_total_bar])
    counter_total_foo.add_to_group(group)
    # Note: counter_total_bar is never added to group which is unusual, but allowed
    assert counter_total_rx.value_display_str() == "0 Packets"
    assert counter_total_tx.value_display_str() == "0 Packets"
    assert counter_total_foo.value_display_str() == "0 Packets"
    assert counter_total_bar.value_display_str() == "0 Packets"
    assert counter_rx_foo.value_display_str() == "0 Packets"
    assert counter_tx_foo.value_display_str() == "0 Packets"
    assert counter_rx_bar.value_display_str() == "0 Packets"
    assert counter_tx_bar.value_display_str() == "0 Packets"
    counter_rx_foo.increase()
    assert counter_total_rx.value_display_str() == "1 Packet"
    assert counter_total_tx.value_display_str() == "0 Packets"
    assert counter_total_foo.value_display_str() == "1 Packet"
    assert counter_total_bar.value_display_str() == "0 Packets"
    assert counter_rx_foo.value_display_str() == "1 Packet"
    assert counter_tx_foo.value_display_str() == "0 Packets"
    assert counter_rx_bar.value_display_str() == "0 Packets"
    assert counter_tx_bar.value_display_str() == "0 Packets"
    counter_rx_bar.add(5)
    assert counter_total_rx.value_display_str() == "6 Packets"
    assert counter_total_tx.value_display_str() == "0 Packets"
    assert counter_total_foo.value_display_str() == "1 Packet"
    assert counter_total_bar.value_display_str() == "5 Packets"
    assert counter_rx_foo.value_display_str() == "1 Packet"
    assert counter_tx_foo.value_display_str() == "0 Packets"
    assert counter_rx_bar.value_display_str() == "5 Packets"
    assert counter_tx_bar.value_display_str() == "0 Packets"
    counter_tx_bar.add(4)
    assert counter_total_rx.value_display_str() == "6 Packets"
    assert counter_total_tx.value_display_str() == "4 Packets"
    assert counter_total_foo.value_display_str() == "1 Packet"
    assert counter_total_bar.value_display_str() == "9 Packets"
    assert counter_rx_foo.value_display_str() == "1 Packet"
    assert counter_tx_foo.value_display_str() == "0 Packets"
    assert counter_rx_bar.value_display_str() == "5 Packets"
    assert counter_tx_bar.value_display_str() == "4 Packets"
    counter_tx_bar.add(2)
    assert counter_total_rx.value_display_str() == "6 Packets"
    assert counter_total_tx.value_display_str() == "6 Packets"
    assert counter_total_foo.value_display_str() == "1 Packet"
    assert counter_total_bar.value_display_str() == "11 Packets"
    assert counter_rx_foo.value_display_str() == "1 Packet"
    assert counter_tx_foo.value_display_str() == "0 Packets"
    assert counter_rx_bar.value_display_str() == "5 Packets"
    assert counter_tx_bar.value_display_str() == "6 Packets"

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
    counter_1.clear()
    assert counter_1.value_display_str() == "0 Packets, 0 Bytes"
    counter_1.add([12, 34])
    assert counter_1.value_display_str() == "12 Packets, 34 Bytes"
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
    counter_2.clear()
    assert counter_2.value_display_str() == "0 Fish, 0 Grams"

def test_sum_multi_counter():
    # pylint:disable=too-many-statements
    group = stats.Group()
    counter_total_rx = stats.MultiCounter(group, "Total RX Packets", ["Packet", "Byte"])
    counter_total_tx = stats.MultiCounter(group, "Total TX Packets", ["Packet", "Byte"])
    counter_total_foo = stats.MultiCounter(None, "Total Foo Packets", ["Packet", "Byte"])
    counter_total_bar = stats.MultiCounter(None, "Total Bar Packets", ["Packet", "Byte"])
    counter_rx_foo = stats.MultiCounter(group, "RX Foo Packets", ["Packet", "Byte"],
                                        sum_counters=[counter_total_rx, counter_total_foo])
    counter_tx_foo = stats.MultiCounter(group, "TX Foo Packets", ["Packet", "Byte"],
                                        sum_counters=[counter_total_tx, counter_total_foo])
    counter_rx_bar = stats.MultiCounter(group, "RX Bar Packets", ["Packet", "Byte"],
                                        sum_counters=[counter_total_rx, counter_total_bar])
    counter_tx_bar = stats.MultiCounter(group, "TX Bar Packets", ["Packet", "Byte"],
                                        sum_counters=[counter_total_tx, counter_total_bar])
    counter_total_foo.add_to_group(group)
    # Note: counter_total_bar is never added to group which is unusual, but allowed
    assert counter_total_rx.value_display_str() == "0 Packets, 0 Bytes"
    assert counter_total_tx.value_display_str() == "0 Packets, 0 Bytes"
    assert counter_total_foo.value_display_str() == "0 Packets, 0 Bytes"
    assert counter_total_bar.value_display_str() == "0 Packets, 0 Bytes"
    assert counter_rx_foo.value_display_str() == "0 Packets, 0 Bytes"
    assert counter_tx_foo.value_display_str() == "0 Packets, 0 Bytes"
    assert counter_rx_bar.value_display_str() == "0 Packets, 0 Bytes"
    assert counter_tx_bar.value_display_str() == "0 Packets, 0 Bytes"
    counter_rx_foo.add([1, 10])
    assert counter_total_rx.value_display_str() == "1 Packet, 10 Bytes"
    assert counter_total_tx.value_display_str() == "0 Packets, 0 Bytes"
    assert counter_total_foo.value_display_str() == "1 Packet, 10 Bytes"
    assert counter_total_bar.value_display_str() == "0 Packets, 0 Bytes"
    assert counter_rx_foo.value_display_str() == "1 Packet, 10 Bytes"
    assert counter_tx_foo.value_display_str() == "0 Packets, 0 Bytes"
    assert counter_rx_bar.value_display_str() == "0 Packets, 0 Bytes"
    assert counter_tx_bar.value_display_str() == "0 Packets, 0 Bytes"
    counter_rx_bar.add([5, 50])
    assert counter_total_rx.value_display_str() == "6 Packets, 60 Bytes"
    assert counter_total_tx.value_display_str() == "0 Packets, 0 Bytes"
    assert counter_total_foo.value_display_str() == "1 Packet, 10 Bytes"
    assert counter_total_bar.value_display_str() == "5 Packets, 50 Bytes"
    assert counter_rx_foo.value_display_str() == "1 Packet, 10 Bytes"
    assert counter_tx_foo.value_display_str() == "0 Packets, 0 Bytes"
    assert counter_rx_bar.value_display_str() == "5 Packets, 50 Bytes"
    assert counter_tx_bar.value_display_str() == "0 Packets, 0 Bytes"
    counter_tx_bar.add([4, 40])
    assert counter_total_rx.value_display_str() == "6 Packets, 60 Bytes"
    assert counter_total_tx.value_display_str() == "4 Packets, 40 Bytes"
    assert counter_total_foo.value_display_str() == "1 Packet, 10 Bytes"
    assert counter_total_bar.value_display_str() == "9 Packets, 90 Bytes"
    assert counter_rx_foo.value_display_str() == "1 Packet, 10 Bytes"
    assert counter_tx_foo.value_display_str() == "0 Packets, 0 Bytes"
    assert counter_rx_bar.value_display_str() == "5 Packets, 50 Bytes"
    assert counter_tx_bar.value_display_str() == "4 Packets, 40 Bytes"
    counter_tx_bar.add([2, 20])
    assert counter_total_rx.value_display_str() == "6 Packets, 60 Bytes"
    assert counter_total_tx.value_display_str() == "6 Packets, 60 Bytes"
    assert counter_total_foo.value_display_str() == "1 Packet, 10 Bytes"
    assert counter_total_bar.value_display_str() == "11 Packets, 110 Bytes"
    assert counter_rx_foo.value_display_str() == "1 Packet, 10 Bytes"
    assert counter_tx_foo.value_display_str() == "0 Packets, 0 Bytes"
    assert counter_rx_bar.value_display_str() == "5 Packets, 50 Bytes"
    assert counter_tx_bar.value_display_str() == "6 Packets, 60 Bytes"

def test_secs_to_dmhs_str():
    assert stats.secs_to_dmhs_str(0.0) == "0d 00h:00m:00.00s"
    assert stats.secs_to_dmhs_str(0.01) == "0d 00h:00m:00.01s"
    assert stats.secs_to_dmhs_str(59.99) == "0d 00h:00m:59.99s"
    assert stats.secs_to_dmhs_str(60.00) == "0d 00h:01m:00.00s"
    assert stats.secs_to_dmhs_str(72.34) == "0d 00h:01m:12.34s"
    assert stats.secs_to_dmhs_str(45296.78) == "0d 12h:34m:56.78s"
    assert stats.secs_to_dmhs_str(218096.78) == "2d 12h:34m:56.78s"
