import os
from pathlib import Path
from PIL import Image
import numpy as np
import xml.etree.ElementTree as ET
import pandas as pd

# "annotations_png/SegmentationClass"
def generate_empty_masks(path_true:str, path_mask:str) -> None:
    path_true, path_mask = Path(path_true), Path(path_mask)
    # Works only for "Caro_pers_" prefix
    mask_names = os.listdir(path_mask)
    true_names = os.listdir(path_true)
    mask_ids = [int(k[10:-4]) for k in mask_names]

    for name in true_names:

        id = int(name[10:-4])
        if id in mask_ids: continue

        with Image.open(os.path.join(path_true, name)) as img:
            size = (img.width, img.height)

        arr = np.zeros(size, dtype=np.uint8)
        path = os.path.join(path_mask, f"Phyl_disc_{'0' * (4 - len(str(id)))}{id}.png")
        Image.fromarray(arr, mode="L").save(path)

#generate_empty_masks(path_true="Stack_Phyl_disc", path_mask="Phyl_disc_masks\SegmentationClass")

def fix_annotation_xml(tag_mapping: dict, ignore_tags: list, input_file: str, output_file: str) -> None:

    tree = ET.parse(input_file)
    root = tree.getroot()

    for image in root.findall("image"):
        
        vein_mask = None
        for mask in image.findall("mask"):
            if mask.get("label") == "Vein":
                vein_mask = mask
                break

        tags_to_remove = []
        for tag in image.findall("tag"):
            label = tag.get("label")
            
            if label in ignore_tags:
                continue
                
            if label in tag_mapping:
                old_attr_key, new_attr_key = tag_mapping[label]

                if vein_mask is None:
                    tags_to_remove.append(tag)
                    continue
                
                for attr in tag.findall("attribute"):
                    if attr.get("name") == old_attr_key:
                        value = attr.text
                        
                        existing = vein_mask.find(f"./attribute[@name='{new_attr_key}']")
                        if existing is None:
                            new_attr = ET.SubElement(vein_mask, "attribute")
                            new_attr.set("name", new_attr_key)
                            new_attr.text = value
                
                tags_to_remove.append(tag)

        for tag in tags_to_remove:
            image.remove(tag)

    tree.write(output_file, encoding="utf-8", xml_declaration=True)
    print(f"Refactoring complete. Saved to {output_file}")

# fix_annotation_xml(
#     tag_mapping={
#         "Width":  ("mm",  "width_mm"),
#         "Length": ("mm",  "length_mm")
#     },
#     ignore_tags=["Coordinates", "Area"],
#     input_file="annotations.xml",
#     output_file="annotations_fixed2.xml"
# )

def parse_cvat_xml_to_csv(input_file, output_file):

    tree = ET.parse(input_file)
    root = tree.getroot()

    data_rows = []

    for image in root.findall("image"):

        filename = image.get("name")
        
        row = {'filename': filename}

        for tag in image.findall("tag"):
            label = tag.get("label")
            attr = tag.findall("attribute")[0]
            row[f"{label.lower()}_{attr.get('name')}"] = attr.text

        # 2. Capture Sparse Attributes (Mask Attributes)
        # We assume ONE mask of interest per image (Binary segmentation)
        # In CVAT, these are <polygon>, <box>, or <points>
        # We take the first shape we find, as you are doing binary masks
        vein_mask = image.find("mask")
        
        if vein_mask is not None:
            for attr in vein_mask.findall("attribute"):
                attr_name = attr.get("name")
                attr_value = attr.text
                row[attr_name] = attr_value
        data_rows.append(row)

    df = pd.DataFrame(data_rows)
    
    df.to_csv(output_file, index=False)
    print(f"Saved metadata to {output_file} with {len(df)} rows.")

parse_cvat_xml_to_csv("Phyl_disc_data\\annotations_fixed2.xml", "measurements.csv")

# for name in os.listdir("Stack_Caro_pers"):
#     if "Copy" in name:
#         os.remove(f"Stack_Caro_pers/{name}")

# dir_path = "annotations_png_color/SegmentationClass"

# for i, n in enumerate(sorted(os.listdir(dir_path), key=lambda x: int(x[10:-4]))):
#         i += 1
#         os.rename(f"{dir_path}/{n}", f"{dir_path}/Caro_pers_{'0' * (4 - len(str(i)))}{i}.png")


# for n in os.listdir("Stack_Phyl_disc"):
#     os.rename(f"Stack_Phyl_disc/{n}", f"Stack_Phyl_disc/Phyl_disc_{n[5:]}")