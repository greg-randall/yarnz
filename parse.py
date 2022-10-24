import os
from bs4 import BeautifulSoup
import colorgram
from pathlib import Path
import torch
from carvekit.api.high import HiInterface
import json



debug = False
output_image_with_color = False



def rgb_to_hex(rgb):
    return "%02x%02x%02x" % rgb

def get_primary_color(image_name):
    colors = colorgram.extract(image_name, 2)  # extract the two most prominent colors

    if debug:
        print(f"function: {image_name} - {colors}")

    if len(colors) > 1:  # make sure we got some actual colors out
        rgb = colors[1].rgb  # typically the second color is the one we want

        if (
            rgb[0] > 240 and rgb[1] > 240 and rgb[2] > 240
        ):  # if the color is close to white, then we'll pick the other color
            rgb = colors[0].rgb

        average = (rgb[0] + rgb[1] + rgb[2]) / 3  # get the average rgb color
        if (
            abs(rgb[0] - average) < 5
            and abs(rgb[1] - average) < 5
            and abs(rgb[2] - average) < 5
        ):  # if the color is close to gray (ie all three rgb values are very similar) we'll pick the other color
            rgb = colors[0].rgb

        hex = rgb_to_hex(rgb)
        return hex


os.system("mkdir jpg")

if debug:
    os.system("mkdir png")

os.system(f"cat *.html > combined_html; mkdir htmls; mv *.html htmls/; mv combined_html combined.html")

#open our html file to parse
f = open("combined.html", "r")

#start up the parser
soup = BeautifulSoup(f, "html.parser")

#collect the breadcrumbs from the site to figure out what the brand and yarn name are
bread = soup.findAll("span", attrs={"class": "breadcrumbs__crumb"})
#bread_links = soup.findAll("span", attrs={"class": "breadcrumbs__crumb"}).findall('a').get('href')

#the format is always like yarn > company > yarn name, so we're getting only the second and third part and adding a dash
company = f"{bread[1].get_text().strip()} - {bread[2].get_text().strip()}"
company_url = bread[1].find("a").get('href')

output = {
    'name' : company,
    'url'  : company_url,
    'colorways' : []
}

if debug:
    print(f"company: {company} - company url: {company_url}")

#collect all the colorways squares
colorways = soup.findAll("div", attrs={"class": "yarn__colorway__preview"})

# set up the image segmenter (removes the subject from the background)
interface = HiInterface(
    batch_size_seg=1,
    batch_size_matting=1,
    device="cuda" if torch.cuda.is_available() else "cpu",
    seg_mask_size=320,
    matting_mask_size=2048,
)

#counter for showing progress
i = 1
color_count = len(colorways)

#loop through each colorway
for colorway in colorways:
    name = ( #get the colorway's name
        colorway.find("div", attrs={"class": "yarn__colorway__preview__title"})
        .get_text()
        .strip()
    )

    link = colorway.find("a", href=True) #get the link base
    link = f"https://www.ravelry.com{link['href']}" #add the domain to the link base
    
    image = colorway.find("img", src=True)
    image_og = image["src"]
    image = image["src"].replace("_small.j", ".j")
    image_save_name = (
        image.lower().replace("/", "_").replace(":", "").replace("jpeg", "jpg")
    )
    if not image_save_name.endswith(".jpg"):
        image_save_name = f"{image_save_name}.jpg"

    os.system(f"wget -q {image} -O {image_save_name}")
    if os.path.getsize(image_save_name) > 100:
        # start color extraction

        filename_without_extension = Path(
            image_save_name
        ).stem  # get the base filename without extensions -- ie asdf.jpg to asdf

        # run the image segmentation
        images_without_background = interface([image_save_name])
        image_without_background = images_without_background[0]

        color = get_primary_color(
            image_without_background
        )  # get the primary color from the segmented image

        if color is None:  # if we didn't get a color, try re-running but on the original image, not the segmented one
            color = get_primary_color(f"{image_save_name}")

        # sometimes if there isn't really a subject in the image (ie fully zoomed in picture of yarn), segmentation will return nonsese.
        # we're going to count the total unique colors, to determine if we're getting nonsense
        w, h = image_without_background.size
        uniqueColors = set()
        for x in range(w):
            for y in range(h):
                pixel = image_without_background.getpixel((x, y))
                uniqueColors.add(pixel)
        totalUniqueColors = len(uniqueColors)

        if (
            totalUniqueColors < 10
        ):  # if we didn't many unique colors in the segmented file we'll re run on just the raw file
            color = get_primary_color(f"{image_save_name}")

        if debug:
            print(f"pixels {w} {h} ; unique colors: {totalUniqueColors}")

        if debug or output_image_with_color:
            image_without_background.save(f"{filename_without_extension}.png")
            os.system(f"convert {filename_without_extension}.png -resize 500x500 -background '#{color}' label:'#{color}' -gravity Center -append {filename_without_extension}-color.png")

        if debug:
            os.system(f"mv {filename_without_extension}.png png/")

        os.system(f"convert {image_save_name} -resize 500x500 -background '#{color}' label:'#{color}' -gravity Center -append {filename_without_extension}-color.jpg")
        os.system(f"mv {image_save_name} jpg/")

        print(f"{i}/{color_count} | {company} - {name} - {link} - #{color}")

        output['colorways'].append({ 'hex' : f"#{color}", 'name' : name, 'direct_url' : link })


        i+=1
        if debug and i>4:
            break



if debug:
    print(json.dumps(output, indent=4))


f = open(f"{company}.json", "w")
f.write(json.dumps(output, indent=4))
f.close()