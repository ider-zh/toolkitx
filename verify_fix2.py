import json
from toolkitx.html_utils import html_to_markdown

html = """
<table>
    <tr>
        <th>Header 1</th>
        <th>Header 2</th>
    </tr>
    <tr>
        <td>
            <table>
                <tr><td>Nested 1</td><td>Nested 2</td></tr>
            </table>
        </td>
        <td rowspan="2">Merged</td>
    </tr>
    <tr>
        <td>Row 3, Cell 1</td>
    </tr>
</table>
"""

print("--- Markdown ---")
print(html_to_markdown(html))
