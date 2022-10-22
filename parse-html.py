import os

from bs4 import BeautifulSoup

os.system(f"cat *.html > combined_html")

f = open("combined_html", "r")

os.system(f"mkdir htmls; mv *.html htmls/")

soup = BeautifulSoup(f,'html.parser')

company = soup.find('span', attrs={"class":"breadcrumbs__crumb--active"}).get_text().strip()

colorways = soup.findAll('div', attrs={"class":"yarn__colorway__preview"})
for color in colorways:
    name = color.find('div', attrs={"class":"yarn__colorway__preview__title"}).get_text().strip()
    link = color.find('a', href=True)
    link = link['href']
    image = color.find('img', src=True)
    image_og = image['src']
    image = image['src'].replace("_small.j", ".j")
    image_save_name = image.lower().replace("/","_").replace(":","").replace("jpeg","jpg")
    if not image_save_name.endswith('.jpg'):
        image_save_name = f"{image_save_name}.jpg"
    
    os.system(f"wget -q {image} -O {image_save_name}")
    if os.path.getsize(image_save_name) < 100:
        print(f"{company} - {name} - {link} - og: {image_og} dl: {image} - save: {image_save_name}")
        print("\n===================================================\n")

for filename in os.listdir("."):
    if filename.endswith('jpg') and os.path.isfile(filename) and os.path.getsize(filename) < 100:
        os.remove(filename)