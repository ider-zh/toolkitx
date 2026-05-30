from bs4 import BeautifulSoup
import json

def _expand_table_cells(table):
    """Normalizes a table by expanding colspan and rowspan."""
    rows = []
    for child in table.find_all(["tr", "thead", "tbody", "tfoot"], recursive=False):
        if child.name == "tr":
            rows.append(child)
        else:
            rows.extend(child.find_all("tr", recursive=False))
            
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
                new_cell.append(BeautifulSoup(content, "html.parser"))
            else:
                new_cell = soup.new_tag("td")
                new_cell.string = "\u200b"
            tr.append(new_cell)

from markdownify import markdownify as md

def html_to_markdown(html: str, handle_nested_tables: str = "json", **kwargs) -> str:
    """
    Converts HTML to Markdown with robust table support.
    
    Nested tables are converted to JSON strings to maintain structure in Markdown cells.
    Merged cells (colspan/rowspan) are expanded.
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
            # All remaining tables have cycles? (Should not happen with valid HTML)
            # Just process the first one
            innermost_table = tables[0]
            
        # If this table is inside another table, convert it to JSON
        if innermost_table.find_parent("table"):
            if handle_nested_tables == "json":
                rows_data = []
                for tr in innermost_table.find_all("tr", recursive=False):
                    row = [cell.get_text(strip=True) for cell in tr.find_all(["td", "th"], recursive=False)]
                    rows_data.append(row)
                json_str = json.dumps(rows_data, ensure_ascii=False)
                innermost_table.replace_with(f"`{json_str}`")
            else:
                # Default behavior: let markdownify handle it or simple text
                innermost_table.unwrap() 
        else:
            # Top-level table: Expand it
            _expand_table_cells(innermost_table)
            # Mark it so we don't process it again in this loop
            innermost_table.name = "processed_table"

    # Restore tag names
    for t in soup.find_all("processed_table"):
        t.name = "table"
        
    return md(str(soup), **kwargs).strip()

