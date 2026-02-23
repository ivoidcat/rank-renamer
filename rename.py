"""GUI 批量重命名：Flask Web 版，显示缩略图，拖拽排序，复制到新文件夹"""

import os
import re
import shutil
import webbrowser
from flask import Flask, send_from_directory, jsonify, request, redirect

app = Flask(__name__)
IMAGES_DIR = ""

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"MS Sans Serif",Tahoma,sans-serif;background:#008080;font-size:11px;height:100vh;display:flex;justify-content:center;align-items:center}
.window{background:#c0c0c0;border:2px solid;border-color:#fff #808080 #808080 #fff;display:flex;flex-direction:column}
.titlebar{background:linear-gradient(90deg,#000080,#1084d0);padding:3px 6px}
.titlebar span{color:#fff;font-weight:bold;font-size:12px;text-shadow:1px 1px #000}
.body{display:flex;flex:1;overflow:hidden;padding:4px;gap:4px}
.sidebar{width:220px;flex-shrink:0;display:flex;flex-direction:column;gap:4px}
.groupbox{border:2px solid;border-color:#808080 #fff #fff #808080;padding:8px;padding-top:4px}
.groupbox legend{background:#c0c0c0;padding:0 4px}
.field{margin-bottom:4px;display:flex;align-items:center;gap:4px}
.field label{width:55px;text-align:right}
.field input,.field select{flex:1;background:#fff;border:2px solid;border-color:#808080 #fff #fff #808080;padding:2px 4px;font-family:inherit;font-size:11px;outline:none}
.btn98{background:#c0c0c0;border:2px solid;border-color:#fff #808080 #808080 #fff;padding:3px 12px;font-family:inherit;font-size:11px;cursor:pointer;min-width:80px;text-align:center}
.btn98:active{border-color:#808080 #fff #fff #808080;padding:4px 11px 2px 13px}
.example98{background:#fff;border:2px solid;border-color:#808080 #fff #fff #808080;padding:4px;margin-top:4px;text-align:center}
.example98 b{color:#000080}
.main{flex:1;background:#fff;border:2px solid;border-color:#808080 #fff #fff #808080;overflow-y:auto;padding:4px}
.grid{display:flex;flex-wrap:wrap;gap:4px}
.item{width:80px;padding:4px;text-align:center;cursor:grab;border:1px solid transparent}
.item:hover,.item.over{background:#000080}
.item:hover span,.item.over span{color:#fff}
.item img{width:48px;height:48px;object-fit:contain;display:block;margin:0 auto 2px}
.item span{font-size:10px;display:block;word-break:break-all;line-height:1.2}
.item.dragging{opacity:0.3}
.section-title{font-size:11px;font-weight:bold;margin:8px 0 4px;color:#000080}
.statusbar{background:#c0c0c0;border-top:2px solid;border-color:#808080 #fff #fff #808080;padding:2px 6px;display:flex;gap:8px}
.statusbar .cell{border:1px solid;border-color:#808080 #fff #fff #808080;padding:1px 6px;flex:1}
.main::-webkit-scrollbar{width:16px}
.main::-webkit-scrollbar-track{background:#c0c0c0}
.main::-webkit-scrollbar-thumb{background:#c0c0c0;border:2px solid;border-color:#fff #808080 #808080 #fff}
"""

SCRIPT = """
<script>
let dragged=null;
function initDrag(){
  document.querySelectorAll('#grid .item').forEach(el=>{
    el.addEventListener('dragstart',e=>{dragged=el;el.classList.add('dragging')});
    el.addEventListener('dragend',e=>{el.classList.remove('dragging');dragged=null});
    el.addEventListener('dragover',e=>e.preventDefault());
    el.addEventListener('dragenter',e=>{e.preventDefault();el.classList.add('over')});
    el.addEventListener('dragleave',e=>el.classList.remove('over'));
    el.addEventListener('drop',e=>{
      e.preventDefault();el.classList.remove('over');
      if(dragged&&dragged!==el){
        let grid=document.getElementById('grid');
        let items=[...grid.children];
        let from=items.indexOf(dragged),to=items.indexOf(el);
        grid.removeChild(dragged);
        if(from<to)el.after(dragged);else el.before(dragged);
        [...grid.children].forEach((c,i)=>c.querySelector('span').textContent=(i+1)+'. '+c.dataset.name);
      }
    });
  });
}
initDrag();
function getOpts(){
  let start=parseInt(document.getElementById('start').value)||1;
  let step=parseInt(document.getElementById('step').value)||1;
  let digits=parseInt(document.getElementById('digits').value)||0;
  return {prefix:document.getElementById('prefix').value,suffix:document.getElementById('suffix').value,start,step,digits};
}
function makeName(i,ext){
  let o=getOpts();let num=String(o.start+i*o.step);
  if(o.digits>0)num=num.padStart(o.digits,'0');
  return o.prefix+num+o.suffix+ext;
}
function updateExample(){
  let o=getOpts();let num=String(o.start);
  if(o.digits>0)num=num.padStart(o.digits,'0');
  document.getElementById('example').textContent=o.prefix+num+o.suffix+'.png';
}
document.querySelectorAll('#prefix,#start,#step,#digits,#suffix').forEach(el=>el.addEventListener('input',updateExample));
updateExample();
function getOrder(){return [...document.querySelectorAll('#grid .item')].map(e=>e.dataset.name)}
function doPreview(){
  let order=getOrder();
  let html=order.map((f,i)=>{let ext=f.substring(f.lastIndexOf('.'));
    return '<div style="width:80px;padding:4px;text-align:center;display:inline-block"><img src="/images/'+f+'" style="width:48px;height:48px;object-fit:contain"><div style="font-size:10px;word-break:break-all">'+makeName(i,ext)+'</div></div>';}).join('');
  let w=window.open('','preview','width=800,height=600');
  w.document.write('<html><head><title>重命名预览</title><style>body{font-family:Tahoma,sans-serif;background:#c0c0c0;margin:0}.titlebar{background:linear-gradient(90deg,#000080,#1084d0);padding:3px 6px;color:#fff;font-weight:bold;font-size:12px;text-shadow:1px 1px #000}.content{background:#fff;border:2px solid;border-color:#808080 #fff #fff #808080;margin:4px;padding:8px;overflow:auto;height:calc(100vh - 40px)}</style></head><body><div class="titlebar">重命名预览 - 共 '+order.length+' 个文件</div><div class="content">'+html+'</div></body></html>');
  w.document.close();
}
function doRename(){
  let order=getOrder();
  let mapping=order.map((f,i)=>{let ext=f.substring(f.lastIndexOf('.'));return [f,makeName(i,ext)]});
  if(!confirm('确认复制并重命名 '+order.length+' 个文件到 output 文件夹？'))return;
  fetch('/rename',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(mapping)})
  .then(r=>r.json()).then(d=>{alert(d.msg)});
}
</script>"""


def natural_sort_key(filename):
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', filename)]


def get_files_sorted(sort_by="name"):
    files = [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if sort_by == "name":
        files.sort(key=natural_sort_key)
    elif sort_by == "name_desc":
        files.sort(key=natural_sort_key, reverse=True)
    elif sort_by == "original":
        def orig_key(fn):
            m = re.match(r'^(\d+)@\d+x(?:\((\d+)\))?\.', fn)
            return (int(m.group(1)), int(m.group(2) or 0)) if m else (float('inf'), 0)
        files.sort(key=orig_key)
    elif sort_by == "mtime":
        files.sort(key=lambda f: os.path.getmtime(os.path.join(IMAGES_DIR, f)))
    elif sort_by == "mtime_desc":
        files.sort(key=lambda f: os.path.getmtime(os.path.join(IMAGES_DIR, f)), reverse=True)
    elif sort_by == "ctime":
        files.sort(key=lambda f: os.stat(os.path.join(IMAGES_DIR, f)).st_birthtime)
    elif sort_by == "ctime_desc":
        files.sort(key=lambda f: os.stat(os.path.join(IMAGES_DIR, f)).st_birthtime, reverse=True)
    elif sort_by == "size":
        files.sort(key=lambda f: os.path.getsize(os.path.join(IMAGES_DIR, f)))
    elif sort_by == "size_desc":
        files.sort(key=lambda f: os.path.getsize(os.path.join(IMAGES_DIR, f)), reverse=True)
    elif sort_by == "ext":
        files.sort(key=lambda f: (os.path.splitext(f)[1].lower(), natural_sort_key(f)))
    return files


SORTS = {"original": "原始名称", "name": "名称 ↑", "name_desc": "名称 ↓",
         "mtime": "修改时间 ↑", "mtime_desc": "修改时间 ↓",
         "ctime": "创建时间 ↑", "ctime_desc": "创建时间 ↓",
         "size": "文件大小 ↑", "size_desc": "文件大小 ↓", "ext": "扩展名"}


@app.route("/")
def home():
    if IMAGES_DIR:
        return redirect("/app")
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>批量重命名</title>
<style>{CSS}
.home{{text-align:center;padding:40px}}
.home h2{{margin-bottom:16px;color:#000080}}
.home p{{margin:8px 0;color:#444}}
.pathbox{{background:#fff;border:2px solid;border-color:#808080 #fff #fff #808080;padding:4px 8px;font-size:12px;width:350px;font-family:inherit}}
</style></head><body>
<div class="window" style="width:500px;height:auto">
  <div class="titlebar"><span>批量重命名工具</span></div>
  <div class="home">
    <h2>选择图片文件夹</h2>
    <p>请输入包含图片的文件夹路径：</p>
    <form action="/setdir" method="POST" style="margin:16px 0">
      <input class="pathbox" name="path" placeholder="/path/to/images" value="{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')}">
      <br><br>
      <button class="btn98" type="submit" style="padding:6px 24px">打开文件夹(O)</button>
    </form>
  </div>
</div></body></html>"""


@app.route("/setdir", methods=["POST"])
def setdir():
    global IMAGES_DIR
    path = request.form.get("path", "").strip()
    if os.path.isdir(path):
        IMAGES_DIR = os.path.abspath(path)
        return redirect("/app")
    return redirect("/")


@app.route("/reset")
def reset():
    global IMAGES_DIR
    IMAGES_DIR = ""
    return redirect("/")


@app.route("/app")
def main_app():
    if not IMAGES_DIR:
        return redirect("/")
    sort_by = request.args.get("sort", "original")
    files = get_files_sorted(sort_by)
    items = "".join(
        f'<div class="item" draggable="true" data-name="{f}">'
        f'<img src="/images/{f}"><span>{i+1}. {f}</span></div>'
        for i, f in enumerate(files)
    )
    opts = "".join(
        f'<option value="{k}"{"selected" if k == sort_by else ""}>{v}</option>'
        for k, v in SORTS.items()
    )
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>批量重命名</title>
<style>{CSS}</style></head><body>
<div class="window" style="width:95vw;height:92vh">
  <div class="titlebar"><span>批量重命名工具 - {IMAGES_DIR}</span></div>
  <div class="body">
    <div class="sidebar">
      <fieldset class="groupbox"><legend>排序方式</legend>
        <div class="field"><select style="width:100%" onchange="location.href='/app?sort='+this.value">{opts}</select></div>
      </fieldset>
      <fieldset class="groupbox"><legend>命名规则</legend>
        <div class="field"><label>前缀：</label><input id="prefix" value="rank_"></div>
        <div class="field"><label>起始：</label><input id="start" type="number" value="1" min="0"></div>
        <div class="field"><label>步长：</label><input id="step" type="number" value="1" min="1"></div>
        <div class="field"><label>位数：</label><input id="digits" type="number" value="0" min="0"></div>
        <div class="field"><label>后缀：</label><input id="suffix" value="" placeholder="可选"></div>
        <div class="example98">示例：<b id="example"></b></div>
      </fieldset>
      <fieldset class="groupbox"><legend>操作</legend>
        <div style="display:flex;flex-direction:column;gap:4px">
          <button class="btn98" onclick="doPreview()">预览结果(P)</button>
          <button class="btn98" onclick="doRename()">执行重命名(R)</button>
          <button class="btn98" onclick="location.href='/reset'">更换文件夹(C)</button>
        </div>
      </fieldset>
    </div>
    <div class="main">
      <div class="grid" id="grid">{items}</div>
    </div>
  </div>
  <div class="statusbar">
    <div class="cell">共 {len(files)} 个对象</div>
    <div class="cell">{IMAGES_DIR}</div>
  </div>
</div>
""" + SCRIPT + "</body></html>"


@app.route("/images/<path:name>")
def serve_image(name):
    return send_from_directory(IMAGES_DIR, name)


@app.route("/rename", methods=["POST"])
def rename():
    mapping = request.json
    output_dir = os.path.join(os.path.dirname(IMAGES_DIR), "output")
    os.makedirs(output_dir, exist_ok=True)
    for old_name, new_name in mapping:
        shutil.copy2(os.path.join(IMAGES_DIR, old_name), os.path.join(output_dir, new_name))
    return jsonify(msg=f"完成！已复制 {len(mapping)} 个文件到 {output_dir}")


if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=False, port=5000)
