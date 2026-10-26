#!/usr/bin/env python3
"""tile.py PDF FIRST LAST OUTDIR [per_sheet=2] [dpi=170]
Renders pages, crops empty margins (keeps page number/footnotes), tiles N pages per sheet side by side,
labels each page with its PDF page number in a thin header strip."""
import sys,subprocess,os,tempfile
from PIL import Image,ImageDraw,ImageOps
pdf,a,b,out=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]
n=int(sys.argv[5]) if len(sys.argv)>5 else 2
dpi=int(sys.argv[6]) if len(sys.argv)>6 else 170
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
    H=max(p.height for _,p in grp)+26
    W=sum(p.width for _,p in grp)+8*(len(grp)-1)
    sheet=Image.new('L',(W,H),255); d=ImageDraw.Draw(sheet); x=0
    for num,p in grp:
        d.rectangle((x,0,x+p.width,22),fill=215); d.text((x+4,4),'PDF p.%d'%num,fill=0)
        sheet.paste(p,(x,26)); x+=p.width+8
        if x<W: d.line((x-4,0,x-4,H),fill=120)
    name='sheet_%03d-%03d.png'%(grp[0][0],grp[-1][0])
    sheet.save(os.path.join(out,name),optimize=True)
    print(name,sheet.size)
