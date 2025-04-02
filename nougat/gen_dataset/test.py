from bs4 import BeautifulSoup

html_path = "/home/ninziwei/lyj/nougat/__test_new/html/2402.00041/2402.00041.html"
with open(html_path, encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

for img_tag in soup.find_all("img"):
    # src = img_tag.get("src", "")
    with open("tags.txt", "a") as f:
        f.write(f"{img_tag}\n")
