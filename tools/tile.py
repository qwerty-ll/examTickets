#!/usr/bin/env python3
"""tile.py PDF FIRST LAST OUTDIR [per_sheet=2] [dpi=170] [cols=2]
Renders pages, crops empty margins (keeps page number/footnotes), tiles N pages per sheet in a grid
(cols columns), labels each page with its PDF page number in a thin header strip.
Limit found by test: 2 pages/sheet = crisp (forms, tables); 4 pages/sheet (2x2) = prose fine, fine marks borderline;
8 pages/sheet is unreadable after the viewer downscales (~2000px long side)."""
import sys,subprocess,os,tempfile
from PIL import Image,ImageDraw,ImageOps
pdf,a,b,out=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]
n=int(sys.argv[5]) if len(sys.argv)>5 else 2
dpi=int(sys.argv[6]) if len(sys.argv)>6 else 170
cols=int(sys.argv[7]) if len(sys.argv)>7 else 2
os.makedirs(out,exist_ok=True)
tmp=tempfile.mkdtemp()
subprocess.run(['pdftoppm','-f',str(a),'-l',str(b),'-r',str(dpi),'-gray','-png',pdf,tmp+'/pg'],check=True)
files=sorted(os.listdir(tmp))
def crop(path):
    im=Image.open(path).convert('L')
    w,h=im.size
    # ignore 2.5% scan border when finding content
    mx,my=int(w*.025),int(h*.025)
    core=im.crop((mx,my,w-mx,h-my))
    bw=core.point(lambda v:255 if v<150 else 0)
    # ignore tiny specks: dilate-free approach — use projection thresholds
    cols=bw.resize((core.width,1),Image.BOX); rows=bw.resize((1,core.height),Image.BOX)
    cv=list(cols.getdata()); rv=list(rows.getdata())
    xs=[i for i,v in enumerate(cv) if v>2.0]; ys=[i for i,v in enumerate(rv) if v>2.0]
    if not xs or not ys: return im
    pad=14
    box=(max(mx+xs[0]-pad,0),max(my+ys[0]-pad,0),min(mx+xs[-1]+pad,w),min(my+ys[-1]+pad,h))
    return im.crop(box)
pages=[]
for f in files:
    num=int(f.split('-')[-1].split('.')[0])
    pages.append((num,crop(os.path.join(tmp,f))))
for i in range(0,len(pages),n):
    grp=pages[i:i+n]
    rows=[grp[j:j+cols] for j in range(0,len(grp),cols)]
    cw=max(p.width for _,p in grp)
    rh=[max(p.height for _,p in r)+26 for r in rows]
    W=cw*cols+8*(cols-1); H=sum(rh)
    sheet=Image.new('L',(W,H),255); d=ImageDraw.Draw(sheet); y=0
    for r,h in zip(rows,rh):
        x=0
        for num,p in r:
            d.rectangle((x,y,x+cw,y+22),fill=215); d.text((x+4,y+4),'PDF p.%d'%num,fill=0)
            sheet.paste(p,(x+(cw-p.width)//2,y+26)); x+=cw+8
            d.line((x-4,y,x-4,y+h),fill=120)
        d.line((0,y+h-1,W,y+h-1),fill=120); y+=h
    name='sheet_%03d-%03d.png'%(grp[0][0],grp[-1][0])
    sheet.save(os.path.join(out,name),optimize=True)
    print(name,sheet.size)
