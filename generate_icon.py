from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent
S=1024
img=Image.new("RGBA",(S,S),(15,17,23,255))
d=ImageDraw.Draw(img)
d.rounded_rectangle((80,80,944,944),radius=205,fill=(27,31,41,255))

# Video panel
d.rounded_rectangle((190,235,834,690),radius=80,fill=(245,247,250,255))
d.rounded_rectangle((225,270,799,655),radius=55,fill=(20,24,34,255))
# play symbol
d.polygon([(420,365),(420,560),(600,462)],fill=(80,125,255,255))

# compression arrows
d.line((285,785,450,785),fill=(99,102,241,255),width=42)
d.polygon([(450,735),(525,785),(450,835)],fill=(99,102,241,255))
d.line((740,785,575,785),fill=(14,165,233,255),width=42)
d.polygon([(575,735),(500,785),(575,835)],fill=(14,165,233,255))

# GPU spark / CPU dots
for x,y in [(285,190),(355,190),(425,190)]:
    d.ellipse((x-18,y-18,x+18,y+18),fill=(251,191,36,255))
for x,y in [(650,180),(710,205),(770,180)]:
    d.line((x,y,x+28,y-40),fill=(74,222,128,255),width=14)

png=ROOT/"video_optimizer_studio_icon.png"
ico=ROOT/"video_optimizer_studio.ico"
img.save(png)
img.save(ico,format="ICO",sizes=[(16,16),(20,20),(24,24),(32,32),(40,40),(48,48),(64,64),(96,96),(128,128),(256,256)])
print("Generated Video Optimizer Studio icon.")
