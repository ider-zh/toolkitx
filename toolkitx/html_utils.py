import json
import re

from bs4 import BeautifulSoup
from markdownify import markdownify as md


def _get_table_rows(table):
    """Robustly find all logical rows in a table, including those in thead/tbody/tfoot."""
    rows = []
    for child in table.find_all(["tr", "thead", "tbody", "tfoot"], recursive=False):
        if child.name == "tr":
            rows.append(child)
        else:
            rows.extend(child.find_all("tr", recursive=False))
    return rows

def _expand_table_cells(table):
    """Normalizes a table by expanding colspan and rowspan."""
    rows = _get_table_rows(table)
            
    if not rows:
        return
    
    num_rows = len(rows)
    # Calculate actual grid width accounting for rowspans
    max_cols = 0
    occupied = set() # (row, col)
    for row_idx, tr in enumerate(rows):
        cells = tr.find_all(["td", "th"], recursive=False)
        col = 0
        for cell in cells:
            while (row_idx, col) in occupied:
                col += 1
            rs = max(1, int(cell.get("rowspan", 1)))
            cs = max(1, int(cell.get("colspan", 1)))
            for dr in range(rs):
                for dc in range(cs):
                    occupied.add((row_idx + dr, col + dc))
            col += cs
            max_cols = max(max_cols, col)
        
    grid = [[None] * max_cols for _ in range(num_rows)]
    
    for row_idx, tr in enumerate(rows):
        cells = tr.find_all(["td", "th"], recursive=False)
        col = 0
        cell_idx = 0
        while cell_idx < len(cells) and col < max_cols:
            while col < max_cols and grid[row_idx][col] is not None:
                col += 1
            if col >= max_cols:
                break
                
            cell = cells[cell_idx]
            rs = max(1, int(cell.get("rowspan", 1)))
            cs = max(1, int(cell.get("colspan", 1)))
            
            # Keep the tag structure for images and other inline elements
            # But simplify block elements within cells to keep Markdown table valid
            for block in cell.find_all(["p", "ul", "ol", "li", "div"]):
                block.insert_before(" ")
                block.insert_after(" ")
                block.unwrap()
            
            content = "".join(str(c) for c in cell.contents).strip()
            tag_name = cell.name
            
            for dr in range(rs):
                for dc in range(cs):
                    r, c = row_idx + dr, col + dc
                    if r < num_rows and c < max_cols:
                        grid[r][c] = (content, tag_name)
            
            col += cs
            cell_idx += 1

    # Reconstruct the table rows
    # Get the BeautifulSoup object to use as a tag factory
    soup = table
    while soup.parent:
        soup = soup.parent

    for row_idx, tr in enumerate(rows):
        for cell in tr.find_all(["td", "th"], recursive=False):
            cell.decompose()
        for col_idx in range(max_cols):
            data = grid[row_idx][col_idx]
            if data:
                content, tag_name = data
                new_cell = soup.new_tag(tag_name)
                # Use BeautifulSoup to parse content to preserve tags like <img> or <a>
                sub_soup = BeautifulSoup(content, "html.parser")
                for child in list(sub_soup.contents):
                    new_cell.append(child)
                # Empty cells (e.g. <td rowspan="2"></td>) yield no parseable
                # children; keep a zero-width space to preserve the cell.
                if not new_cell.contents:
                    new_cell.string = "\u200b"
            else:
                new_cell = soup.new_tag("td")
                new_cell.string = "\u200b"
            tr.append(new_cell)

def html_to_markdown(
    html: str, 
    handle_nested_tables: str = "json", 
    use_first_row_as_header: bool = True,
    **kwargs
) -> str:
    """
    Converts HTML to Markdown with robust table support.
    
    Nested tables are converted to JSON strings to maintain structure in Markdown cells.
    Merged cells (colspan/rowspan) are expanded.
    If no header is found, the first row is used as a header by default.

    Args:
        html: Input HTML string.
        handle_nested_tables: How to handle nested tables ('json' or 'unwrap').
        use_first_row_as_header: If True and no <th>/<thead> is found, use the first row as header.
        **kwargs: Additional arguments for markdownify.

    Examples:
        # Standard table conversion (first row promoted to header by default)
        >>> html = "<table><tr><td>Cell 1</td><td>Cell 2</td></tr><tr><td>Data</td><td>Val</td></tr></table>"
        >>> print(html_to_markdown(html))
        | Cell 1 | Cell 2 |
        | --- | --- |
        | Data | Val |
        
        # Disable automatic header promotion
        >>> print(html_to_markdown(html, use_first_row_as_header=False))
        |  |  |
        | --- | --- |
        | Cell 1 | Cell 2 |
        | Data | Val |

        # Colspan expansion
        >>> html_colspan = "<table><tr><td colspan='2'>Merged</td><td>Normal</td></tr></table>"
        >>> print(html_to_markdown(html_colspan))
        | Merged | Merged | Normal |
        | --- | --- | --- |

        # Rowspan expansion
        >>> html_rowspan = "<table><tr><td rowspan='2'>Rows</td><td>A</td></tr><tr><td>B</td></tr></table>"
        >>> print(html_to_markdown(html_rowspan))
        | Rows | A |
        | --- | --- |
        | Rows | B |
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # Process tables innermost-first
    while True:
        tables = soup.find_all("table")
        if not tables:
            break
            
        # Find a table that doesn't contain other tables
        innermost_table = None
        for t in tables:
            if not t.find("table"):
                innermost_table = t
                break
        
        if not innermost_table:
            innermost_table = tables[0]
            
        # If this table is inside another table, convert it to JSON
        if innermost_table.find_parent("table"):
            if handle_nested_tables == "json":
                # Expand nested table before JSON-ification
                _expand_table_cells(innermost_table)
                
                rows_data = []
                for tr in _get_table_rows(innermost_table):
                    row = []
                    for cell in tr.find_all(["td", "th"], recursive=False):
                        content_html = "".join(str(c) for c in cell.contents).strip()
                        cell_md = md(content_html, **kwargs).strip()
                        if '\"' in cell_md:
                            cell_md = re.sub(r'(\[[^\]]*\]\([^)]*)\"([^)]*)\"', r"\1'\2'", cell_md)
                            cell_md = re.sub(r'(\!\[[^\]]*\]\([^)]*)\"([^)]*)\"', r"\1'\2'", cell_md)
                        row.append(cell_md)
                    rows_data.append(row)
                
                json_str = json.dumps(rows_data, ensure_ascii=False)
                new_tag = soup.new_tag("code")
                new_tag.string = json_str
                innermost_table.replace_with(new_tag)
            else:
                innermost_table.unwrap() 
        else:
            # Top-level table: Expand it
            _expand_table_cells(innermost_table)

            # Fix: If no <th> or <thead> exists, promote the first row to header
            if use_first_row_as_header:
                has_header = innermost_table.find(["th", "thead"])
                if not has_header:
                    rows = _get_table_rows(innermost_table)
                    if rows:
                        first_row = rows[0]
                        for cell in first_row.find_all("td", recursive=False):
                            cell.name = "th"

            # Mark it so we don't process it again in this loop
            innermost_table.name = "processed_table"

    # Restore tag names
    for t in soup.find_all("processed_table"):
        t.name = "table"
        
    # Ensure images are kept in table cells
    if "keep_inline_images_in" not in kwargs:
        kwargs["keep_inline_images_in"] = ["td", "th"]
        
    return md(str(soup), **kwargs).strip()

