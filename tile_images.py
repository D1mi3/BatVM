import cv2
import numpy as np
import os
import glob
from pathlib import Path
import pandas as pd


IMG_DIR = "photos"
MASK_DIR = "masks"
OUTPUT_DIR = "dataset"
TILE_SIZE = 256
OVERLAP_PCT = 0.4
STRIDE = int(TILE_SIZE * (1 - OVERLAP_PCT))
STARTING_POINT = (0, 0)

def tile_stack(image_path, mask_paths, save_dir, img_name):

    measurements = pd.DataFrame(columns=["filename", "coordinates_xy"])
    img = cv2.imread(str(image_path))
    img_h, img_w, _ = img.shape
    
    loaded_masks = {}
    for mp in mask_paths:
        m = cv2.imread(str(mp), cv2.IMREAD_COLOR)
        if m is not None: loaded_masks[Path(mp).stem] = m

    os.makedirs(os.path.join(save_dir, "source"), exist_ok=True)
    os.makedirs(os.path.join(save_dir, "mask", "raw"), exist_ok=True)
    os.makedirs(os.path.join(save_dir, "mask", "colorized"), exist_ok=True)

    count = 0

    for y in range(STARTING_POINT[1], img_h, STRIDE):
        for x in range(STARTING_POINT[0], img_w, STRIDE):
            
            count += 1

            x_end = min(x + TILE_SIZE, img_w)
            y_end = min(y + TILE_SIZE, img_h)
            
            tmp_img = img[y:y_end, x:x_end]
            pad_h = TILE_SIZE - tmp_img.shape[0]
            pad_w = TILE_SIZE - tmp_img.shape[1]
            
            tile_img = cv2.copyMakeBorder(tmp_img, 0, pad_h, 0, pad_w, cv2.BORDER_CONSTANT, value=[0,0,0])
            
            coordinates = ((((x - STARTING_POINT[0]) // STRIDE)), ((img_h - (y - STARTING_POINT[1])) // STRIDE))
            tile_name = f"{img_name}_{count:04d}.png"

            cv2.imwrite(os.path.join(save_dir, "source", tile_name), tile_img)
            measurements = pd.concat([measurements, pd.DataFrame(
                [{"filename": tile_name, "coordinates_xy": f"{coordinates[0]},{coordinates[1]}"}])], ignore_index=True)

            for mask_name, mask_arr in loaded_masks.items():
                tmp_mask = mask_arr[y:y_end, x:x_end]
                
                colorized_tile = cv2.copyMakeBorder(tmp_mask, 0, pad_h, 0, pad_w, cv2.BORDER_CONSTANT, value=[0, 0, 0])
                cv2.imwrite(os.path.join(save_dir, "mask", "colorized", tile_name), colorized_tile)
                
                binary_tile = (cv2.cvtColor(colorized_tile, cv2.COLOR_BGR2GRAY) > 0).astype(np.uint8)
                cv2.imwrite(os.path.join(save_dir, "mask", "raw", tile_name), binary_tile)
        
    measurements.to_csv(os.path.join(save_dir, "measurements.csv"), index=False)

def main():
    img_files = list(Path(IMG_DIR).glob("*.jpg")) + list(Path(IMG_DIR).glob("*.png"))
    
    for img_path in img_files:

        search_pattern = str(Path(MASK_DIR) / f"*{img_path.stem}*.png")
        mask_candidates = glob.glob(search_pattern)
        output_dir = os.path.join(OUTPUT_DIR, img_path.stem)
        os.makedirs(output_dir, exist_ok=True)
        
        tile_stack(img_path, mask_candidates, output_dir, img_path.stem)

if __name__ == "__main__":
    main()