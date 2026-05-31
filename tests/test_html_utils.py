from bs4 import BeautifulSoup

from toolkitx.html_utils import _expand_table_cells, html_to_markdown


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

def test_html_to_markdown_simple():
    html = "<p>Hello <b>World</b></p>"
    md = html_to_markdown(html)
    assert md == "Hello **World**"

def test_html_to_markdown_nested_table():
    html = """
    <table>
      <tr>
        <td>Outer 1</td>
        <td>
          <table>
            <tr><td>Inner 1</td></tr>
            <tr><td>Inner 2</td></tr>
          </table>
        </td>
      </tr>
    </table>
    """
    md = html_to_markdown(html)
    # The nested table should be a JSON string in a code block
    assert "Outer 1" in md
    assert "[[\"Inner 1\"], [\"Inner 2\"]]" in md

def test_html_to_markdown_images():
    html = """
    <table>
      <tr>
        <td>Text</td>
        <td><img src="test.png" alt="Test Image"></td>
      </tr>
    </table>
    """
    md = html_to_markdown(html)
    assert "Text" in md
    assert "![Test Image](test.png)" in md

def test_html_to_markdown_standard_layout():
    html = """
    <table>
      <thead>
        <tr><th>Col 1</th><th>Col 2</th></tr>
      </thead>
      <tbody>
        <tr><td>Val 1</td><td>Val 2</td></tr>
      </tbody>
      <tfoot>
        <tr><td>Foot 1</td><td>Foot 2</td></tr>
      </tfoot>
    </table>
    """
    md = html_to_markdown(html)
    assert "Col 1" in md
    assert "Col 2" in md
    assert "Val 1" in md
    assert "Val 2" in md
    assert "Foot 1" in md
    assert "Foot 2" in md

def test_nested_table_with_markdown_preservation():
    html = """
    <table>
      <tr>
        <td>Outer</td>
        <td>
          <table>
            <tr><td><b>Inner Bold</b></td></tr>
            <tr><td><a href="http://example.com">Link</a></td></tr>
          </table>
        </td>
      </tr>
    </table>
    """
    md_out = html_to_markdown(html)
    assert "Outer" in md_out
    # Nested table cells should contain Markdown
    assert "**Inner Bold**" in md_out
    assert "Link" in md_out
    assert "http://example.com" in md_out

def test_nested_table_extraction_and_expansion():
    html = """
    <table>
      <tr>
        <td>Outer</td>
        <td>
          <table>
            <thead>
              <tr><th colspan="2">Inner Header</th></tr>
            </thead>
            <tbody>
              <tr><td>Inner 1</td><td>Inner 2</td></tr>
            </tbody>
          </table>
        </td>
      </tr>
    </table>
    """
    md_out = html_to_markdown(html)
    assert "Outer" in md_out
    # Check for expansion and correct row discovery (thead/tbody)
    assert '["Inner Header", "Inner Header"]' in md_out
    assert '["Inner 1", "Inner 2"]' in md_out

def test_nested_table_link_escaping():
    html = """
    <table>
      <tr>
        <td>Outer</td>
        <td>
          <table>
            <tr><td><a href="http://example.com" title="My Title">Link</a></td></tr>
          </table>
        </td>
      </tr>
    </table>
    """
    md_out = html_to_markdown(html)
    # The title would normally have double quotes which would be escaped in JSON.
    # Our fix should change them to single quotes or at least we should check the output.
    # Standard markdownify might produce: [Link](http://example.com "My Title")
    # Our fix changes it to: [Link](http://example.com 'My Title')
    # So JSON will be: ["[Link](http://example.com 'My Title')"]
    assert "Outer" in md_out
    assert "Link" in md_out
    assert "My Title" in md_out
    assert "\\\"" not in md_out # Ensure no escaped double quotes
