from toolkitx.html_utils import html_to_markdown

html = """
<table>
  <tr>
    <td>Outer</td>
    <td>
      <table>
        <tr><td><p>Paragraph in nested table</p></td></tr>
      </table>
    </td>
  </tr>
</table>
"""
md_out = html_to_markdown(html)
print(f"MD_OUT:\n{md_out}")
