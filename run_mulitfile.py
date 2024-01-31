import subprocess
import pandas as pd
from pathlib import Path

csv = "/mnt/ssd1/data/project-shimh-parking-202302/reordered/itemlist/filelist-movie_for_tracking-202302-scenewise.csv"
rootpath = "/mnt/ssd1/data/project-shimh-parking-202302/reordered/items"

df = pd.read_csv(csv)
for i, d in df.iterrows():
    print(d["relative_path"])
    filepath = Path(rootpath).joinpath(d["relative_path"])
    subprocess.run("ls -o {}".format(filepath), shell=True)
    command_str = "python demo/video_demo.py {} detr_r50_8xb2-150e_coco.py detr_r50_8xb2-150e_coco_20221023_153551-436d03e8.pth --out out.mp4".format(filepath)
    subprocess.run(command_str, shell=True)

