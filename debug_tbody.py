from toolkitx.html_utils import html_to_markdown

html = """
<table>
  <tr>
    <td>Outer</td>
    <td>
      <table>
        <tbody>
          <tr><td>Inner Row 1</td></tr>
          <tr><td>Inner Row 2</td></tr>
        </tbody>
      </table>
    </td>
  </tr>
</table>
"""
md_out = html_to_markdown(html)
print(f"MD_OUT:\n{md_out}")
