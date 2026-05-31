import sys
from unittest.mock import MagicMock

# Mock missing dependencies before importing toolkitx.html_utils
sys.modules["tencentcloud"] = MagicMock()
sys.modules["tencentcloud.common"] = MagicMock()
sys.modules["tencentcloud.common.credential"] = MagicMock()
sys.modules["tencentcloud.tmt"] = MagicMock()
sys.modules["tencentcloud.tmt.v20180321"] = MagicMock()
sys.modules["tencentcloud.tmt.v20180321.models"] = MagicMock()
sys.modules["tencentcloud.tmt.v20180321.tmt_client"] = MagicMock()
sys.modules["diskcache"] = MagicMock()

from bs4 import BeautifulSoup
from toolkitx.html_utils import _expand_table_cells

def test_thead_tbody_robustness():
    html = """
    <table>
        <thead>
            <tr><th>Header 1</th><th>Header 2</th></tr>
        </thead>
        <tbody>
            <tr><td>Body 1</td><td>Body 2</td></tr>
        </tbody>
        <tfoot>
            <tr><td>Footer 1</td><td>Footer 2</td></tr>
        </tfoot>
    </table>
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.table
    
    _expand_table_cells(table)
    
    # Verify the cells are now direct children of tr in their respective containers
    thead_tr = table.thead.tr
    tbody_tr = table.tbody.tr
    tfoot_tr = table.tfoot.tr
    
    print(f"thead_tr cells: {[c.get_text() for c in thead_tr.find_all(['td', 'th'], recursive=False)]}")
    print(f"tbody_tr cells: {[c.get_text() for c in tbody_tr.find_all(['td', 'th'], recursive=False)]}")
    print(f"tfoot_tr cells: {[c.get_text() for c in tfoot_tr.find_all(['td', 'th'], recursive=False)]}")
    
    assert len(thead_tr.find_all(['td', 'th'], recursive=False)) == 2
    assert len(tbody_tr.find_all(['td', 'th'], recursive=False)) == 2
    assert len(tfoot_tr.find_all(['td', 'th'], recursive=False)) == 2
    
    print("Test passed!")

def test_complex_table_in_tbody():
    html = """
    <table>
        <tbody>
            <tr>
                <td rowspan="2">R1-2C1</td>
                <td>R1C2</td>
            </tr>
            <tr>
                <td>R2C2</td>
            </tr>
            <tr>
                <td colspan="2">R3C1-2</td>
            </tr>
        </tbody>
    </table>
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.table
    
    _expand_table_cells(table)
    
    rows = table.find_all('tr')
    print(f"DEBUG: Found {len(rows)} rows after expansion")
    
    grid = []
    for tr in rows:
        grid.append([c.get_text() for c in tr.find_all(['td', 'th'], recursive=False)])
    
    for i, row in enumerate(grid):
        print(f"Row {i}: {row}")
    
    assert grid[0] == ["R1-2C1", "R1C2"]
    assert grid[1] == ["R1-2C1", "R2C2"]
    assert grid[2] == ["R3C1-2", "R3C1-2"]
    
    print("Complex test passed!")

if __name__ == "__main__":
    test_thead_tbody_robustness()
    test_complex_table_in_tbody()
