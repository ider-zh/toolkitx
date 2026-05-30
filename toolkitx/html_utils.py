from bs4 import BeautifulSoup
import json

def _expand_table_cells(table):
    """Normalizes a table by expanding colspan and rowspan."""
    rows = table.find_all("tr", recursive=False)
    if not rows:
        return
    
    num_rows = len(rows)
    # Calculate max columns
    max_cols = 0
    for tr in rows:
        cells = tr.find_all(["td", "th"], recursive=False)
        col_count = sum(max(1, int(c.get("colspan", 1))) for c in cells)
        max_cols = max(max_cols, col_count)
        
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
        for cell in tr.find_all(["td", "th"]):
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
