from bs4 import BeautifulSoup

soup = BeautifulSoup("<table><tr></tr></table>", "html.parser")
tr = soup.tr
content = "<b>Bold</b> and <img src='test.png'>"
new_cell = soup.new_tag("td")
new_cell.append(BeautifulSoup(content, "html.parser"))
tr.append(new_cell)
print(str(tr))
