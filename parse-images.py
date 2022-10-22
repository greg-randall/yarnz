import colorgram
import os
from pathlib import Path
import torch
from carvekit.api.high import HiInterface

debug = True

def rgb_to_hex(rgb):
    return '%02x%02x%02x' % rgb

def get_primary_color(image_name):
    colors = colorgram.extract(image_name, 2) # extract the two most prominent colors

    if debug:
        print(f"function: {image_name} - {colors}")

    if len(colors) > 1: # make sure we got some actual colors out
        rgb = colors[1].rgb # typically the second color is the one we want

        if rgb[0]>240 and rgb[1]>240 and rgb[2]>240: # if the color is close to white, then we'll pick the other color
            rgb = colors[0].rgb

        average = ( rgb[0] + rgb[1] + rgb[2] ) / 3 # get the average rgb color
        if abs(rgb[0]-average) < 5 and abs(rgb[1]-average) < 5  and abs(rgb[2]-average) < 5 : # if the color is close to gray (ie all three rgb values are very similar) we'll pick the other color 
             rgb = colors[0].rgb

        hex = rgb_to_hex(rgb) 
        return (hex)


if debug:
    os.system("mkdir jpg")
    os.system("mkdir png")

#set up the image segmenter (removes the subject from the background)
interface = HiInterface(batch_size_seg=1, batch_size_matting=1, device='cuda' if torch.cuda.is_available() else 'cpu', seg_mask_size=320, matting_mask_size=2048)

#get all the files in the current directory
for filename in os.listdir("."):
    if filename.endswith('jpg') and os.path.isfile(filename) and os.path.getsize(filename) > 100: #filter for files that have jpg extensions, are files not folders, and have a size that makes sense
        filename_without_extension = Path(filename).stem #get the base filename without extensions -- ie asdf.jpg to asdf

        #run the image segmentation
        images_without_background = interface([filename])                   
        image_without_background = images_without_background[0]

        color = get_primary_color( image_without_background ) #get the primary color from the segmented image


        if color is None: #if we didn't get a color, try re-running but on the original image, not the segmented one
            color = get_primary_color(f"{filename}")

        
        #sometimes if there isn't really a subject in the image (ie fully zoomed in picture of yarn), segmentation will return nonsese.
        #we're going to count the total unique colors, to determine if we're getting nonsense
        w, h = image_without_background.size
        uniqueColors = set()
        for x in range(w):
            for y in range(h):
                pixel = image_without_background.getpixel((x, y))
                uniqueColors.add(pixel)
        totalUniqueColors = len(uniqueColors)

        if totalUniqueColors <10: #if we didn't many unique colors in the segmented file we'll re run on just the raw file
            color = get_primary_color(f"{filename}")
     
        if debug:
            image_without_background.save(f"{filename_without_extension}.png")

            print(f"pixels {w} {h} ; unique colors: {totalUniqueColors}")

            os.system(f"convert {filename} -resize 500x500 -background '#{color}' label:'#{color}' -gravity Center -append {filename_without_extension}-color.jpg")
            os.system(f"convert {filename_without_extension}.png -resize 500x500 -background '#{color}' label:'#{color}' -gravity Center -append {filename_without_extension}-color.png")

        if debug:
            os.system(f"mv {filename} jpg/")
            os.system(f"mv {filename_without_extension}.png png/")

        print(f"Segmented & Color Found: #{color} - {filename}")