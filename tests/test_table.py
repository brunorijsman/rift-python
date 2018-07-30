import rift.table

def test_simple_table():
    tab = rift.table.Table()
    tab.add_row(['Animal', 'Legs'])
    tab.add_row(['Slug', 0])
    tab.add_row(['Human', 2])
    tab.add_row(['Horse', 4])
    tab.add_row(['Ant', 6])
    tab_str = tab.to_string()
    assert (tab_str == "+--------+------+\n"
                       "| Animal | Legs |\n"
                       "+--------+------+\n"
                       "| Slug   | 0    |\n"
                       "+--------+------+\n"
                       "| Human  | 2    |\n"
                       "+--------+------+\n"
                       "| Horse  | 4    |\n"
                       "+--------+------+\n"
                       "| Ant    | 6    |\n"
                       "+--------+------+\n")
