import colorgram
import os
from pathlib import Path
import torch
from carvekit.api.high import HiInterface


# https://www.codespeedy.com/convert-rgb-to-hex-color-code-in-python/

def rgb_to_hex(rgb):
    return '%02x%02x%02x' % rgb
def get_primary_color(image_name):
    colors = colorgram.extract(image_name, 2)
    first_color = colors[1]
    rgb = first_color.rgb # e.g. (255, 151, 210)
    if rgb[0]>240 and rgb[1]>240 and rgb[2]>240:
        first_color = colors[0]
        rgb = first_color.rgb # e.g. (255, 151, 210)

    print(rgb)
    hex = rgb_to_hex(rgb)
    return (hex)


os.system("mkdir jpg")
os.system("mkdir png")

interface = HiInterface(batch_size_seg=1, batch_size_matting=1, device='cuda' if torch.cuda.is_available() else 'cpu', seg_mask_size=320, matting_mask_size=2048)

for filename in os.listdir("."):
    if filename.endswith('jpg') and os.path.isfile(filename) and os.path.getsize(filename) > 100:
        filename_without_extension = Path(filename).stem
        images_without_background = interface([filename])                               
        cat_wo_bg = images_without_background[0]
        cat_wo_bg.save(f"{filename_without_extension}.png")



for filename in os.listdir("."):
    if filename.endswith('png') and os.path.isfile(filename) and os.path.getsize(filename) > 100:
        color = get_primary_color(filename) 
        original_file = Path(filename).stem
        os.system(f"convert {original_file}.jpg -resize 500x500 -background '#{color}'  label:'#{color}' -gravity Center -append {original_file}-color.jpg")
        #os.system(f"mv {original_file}.jpg jpg/")
        #os.system(f"mv {filename} png/")





