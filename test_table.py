from bs4 import BeautifulSoup
from toolkitx.html_utils import _expand_table_cells

html = """
<table>
  <tr><td rowspan="2">R1C1</td><td>R1C2</td></tr>
  <tr><td>R2C2</td></tr>
</table>
"""
# Wait, in the above example:
# Row 1: Col 1 (rowspan 2), Col 2. Max cols = 2.
# Row 2: Col 1 is occupied. Cell is R2C2, should go to Col 2.
# This works with max_cols = 2.

# Let's try one that fails:
html_fail = """
<table>
  <tr><td rowspan="2">A</td></tr>
  <tr><td>B</td></tr>
</table>
"""
# Row 1: Cell A (rowspan 2) -> Col 0. col_count = 1.
# Row 2: Cell B. col_count = 1.
# max_cols will be 1.
# Row 1 fills grid[0][0] and grid[1][0].
# Row 2: col=0. grid[1][0] is not None. col becomes 1.
# col (1) < max_cols (1) is False.
# Cell B is IGNORED.

soup = BeautifulSoup(html_fail, "html.parser")
table = soup.table
_expand_table_cells(table)
print(table)
