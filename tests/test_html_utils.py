from bs4 import BeautifulSoup
from toolkitx.html_utils import _expand_table_cells

def test_expand_table_cells():
    html = """
    <table>
      <tr>
        <th rowspan="2">Header 1</th>
        <th>Header 2</th>
      </tr>
      <tr>
        <td>Data 1</td>
      </tr>
    </table>
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.table
    _expand_table_cells(table)
    
    rows = table.find_all("tr")
    assert len(rows) == 2
    
    cells_r1 = rows[0].find_all(["th", "td"])
    assert len(cells_r1) == 2
    assert cells_r1[0].get_text() == "Header 1"
    assert cells_r1[0].name == "th"
    assert cells_r1[1].get_text() == "Header 2"
    assert cells_r1[1].name == "th"
    
    cells_r2 = rows[1].find_all(["th", "td"])
    assert len(cells_r2) == 2
    assert cells_r2[0].get_text() == "Header 1"
    assert cells_r2[0].name == "th"
    assert cells_r2[1].get_text() == "Data 1"
    assert cells_r2[1].name == "td"

    print("Basic rowspan test passed!")

def test_colspan():
    html = """
    <table>
      <tr>
        <th colspan="2">Merged Header</th>
      </tr>
      <tr>
        <td>Data 1</td>
        <td>Data 2</td>
      </tr>
    </table>
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.table
    _expand_table_cells(table)
    
    rows = table.find_all("tr")
    cells_r1 = rows[0].find_all(["th", "td"])
    assert len(cells_r1) == 2
    assert cells_r1[0].get_text() == "Merged Header"
    assert cells_r1[1].get_text() == "Merged Header"
    
    print("Basic colspan test passed!")

def test_complex_table():
    html = """
    <table>
      <tr>
        <td rowspan="2" colspan="2">A</td>
        <td>B</td>
      </tr>
      <tr>
        <td>C</td>
      </tr>
      <tr>
        <td>D</td>
        <td>E</td>
        <td>F</td>
      </tr>
    </table>
    """
    # Grid should be:
    # A A B
    # A A C
    # D E F
    soup = BeautifulSoup(html, "html.parser")
    table = soup.table
    _expand_table_cells(table)
    
    rows = table.find_all("tr")
    grid = [[c.get_text() for c in r.find_all(["td", "th"])] for r in rows]
    
    expected = [
        ["A", "A", "B"],
        ["A", "A", "C"],
        ["D", "E", "F"]
    ]
    assert grid == expected
    print("Complex table test passed!")

if __name__ == "__main__":
    test_expand_table_cells()
    test_colspan()
    test_complex_table()
    print("All tests passed!")
