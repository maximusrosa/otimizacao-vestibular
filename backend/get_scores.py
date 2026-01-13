import requests
from bs4 import BeautifulSoup

year = "2025"

url = f"https://www.ufrgs.br/vestibular/cv{year}/histogramas/"
html = requests.get(url).text

soup = BeautifulSoup(html, "html.parser")

rows = soup.find_all("div", class_="row")

processed_subjects = set()

for row in rows:

    # Get the two columns inside the row 
    cols = row.select("div.col.s12.m6")

    # Ignores the second table with unecessary data
    if len(cols) < 2:
        continue

    table_heading = cols[1].select_one("table.col.s12")
    if not table_heading:
        continue

    th = table_heading.select_one("thead tr th[colspan='2']")
    if not th:
        continue

    subject = th.get_text(strip=True)

    processed_subjects.add(subject)

    print(f"\n--- {subject} ---")

    table = cols[0].select_one("table.col.s12")
    if not table:
        continue

    tbody = table.find("tbody")
    if not tbody:
        continue

    for tr in tbody.find_all("tr"):
        cols = [td.get_text(strip=True) for td in tr.find_all("td")]
        print(cols)