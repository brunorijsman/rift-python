import rift.table

def test_simple_table():
    tab = rift.table.Table()
    tab.add_row(['Animal', 'Legs'])
    tab.add_row(['Slug', 0])
    tab.add_rows([['Human', 2], ['Horse', 4]])  # Use add_rows to add multiple rows
    tab.add_rows([['Ant', 6]])                  # Use add_rows to add a single row
    tab.add_rows([])                            # Call add_rows with zero rows
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

def test_multi_line_cells():
    tab = rift.table.Table()
    tab.add_row([['First', 'Name'],
                 ['Last', 'Name'],
                 'Address',
                 ['Country', 'of', 'Residence']])
    tab.add_row(['Marge',
                 'Simpson',
                 ['742 Evergreen Terrace', 'Springfield'],
                 ['United', 'States', 'of', 'America']])
    tab.add_row([['Annelies', 'Marie'],
                 'Frank',
                 ['263 Prinsengracht', 'Amsterdam'],
                 ['The', 'Netherlands']])
    tab_str = tab.to_string()
    assert (tab_str == "+----------+---------+-----------------------+-------------+\n"
                       "| First    | Last    | Address               | Country     |\n"
                       "| Name     | Name    |                       | of          |\n"
                       "|          |         |                       | Residence   |\n"
                       "+----------+---------+-----------------------+-------------+\n"
                       "| Marge    | Simpson | 742 Evergreen Terrace | United      |\n"
                       "|          |         | Springfield           | States      |\n"
                       "|          |         |                       | of          |\n"
                       "|          |         |                       | America     |\n"
                       "+----------+---------+-----------------------+-------------+\n"
                       "| Annelies | Frank   | 263 Prinsengracht     | The         |\n"
                       "| Marie    |         | Amsterdam             | Netherlands |\n"
                       "+----------+---------+-----------------------+-------------+\n")

def test_format_extend():
    # TODO: Add test where contents of extended cell spill over into next column
    tab = rift.table.Table()
    tab.add_row(['Item', 'Length', 'Width', 'Height'])
    tab.add_row(['Cube', '1 cm', '1 cm', '1 cm'])
    tab.add_row(['Line',
                 '2 cm',
                 'N/A',
                 rift.table.Table.Format.EXTEND_LEFT_CELL])
    tab.add_row(['Point',
                 'N/A',
                 rift.table.Table.Format.EXTEND_LEFT_CELL,
                 rift.table.Table.Format.EXTEND_LEFT_CELL])
    tab_str = tab.to_string()
    assert (tab_str == "+-------+--------+-------+--------+\n"
                       "| Item  | Length | Width | Height |\n"
                       "+-------+--------+-------+--------+\n"
                       "| Cube  | 1 cm   | 1 cm  | 1 cm   |\n"
                       "+-------+--------+-------+--------+\n"
                       "| Line  | 2 cm   | N/A            |\n"
                       "+-------+--------+-------+--------+\n"
                       "| Point | N/A                     |\n"
                       "+-------+--------+-------+--------+\n")

def test_no_separators():
    tab = rift.table.Table(separators=False)
    tab.add_row(['First Name', 'Jerry'])
    tab.add_row(['Last Name', 'Seinfeld'])
    tab.add_row(['Address', ['129 West 81st Street', 'Apartment 5A', 'New York, 10024 NY']])
    tab_str = tab.to_string()
    assert (tab_str == "+------------+----------------------+\n"
                       "| First Name | Jerry                |\n"
                       "| Last Name  | Seinfeld             |\n"
                       "| Address    | 129 West 81st Street |\n"
                       "|            | Apartment 5A         |\n"
                       "|            | New York, 10024 NY   |\n"
                       "+------------+----------------------+\n")
