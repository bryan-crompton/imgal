from PIL import Image
from glob import glob
import numpy as np
import os
import sys

home = os.path.expanduser("~")

image_exts = ["png", "gif", "jpg", "jpeg", "bmp"]


def is_ext(f, exts):
	for e in exts:
		if f.lower().endswith("." + e):
			return True
	return False

def files_by_ext(path, exts, sort=None):
	if type(exts) != type([]):
		return "need list"
		
	try:
		filenames = next(os.walk(path))[2]
	except:
		filenames = []
		
	if sort == "modified":
		pairs = [(os.path.getmtime(path + i), i) for i in images ]
		pairs.sort()
		filenames = [p[1] for p in pairs]

	filtered = [f for f in filenames if is_ext(f, exts)]	
	
	return filtered

def get_subfolders(path):
	folders = [x[0].split("/")[-1] for x in os.walk(path)]
	return [f for f in folders if f != '']


import click

@click.command()
@click.argument("folder")
@click.option("--span", default=800)
@click.option("--max-width", default=-1)
@click.option("--recursive/--not-recursive", default=False)
@click.option("--thumbnails/--no-thumbnails", default=False)

# TODO: add sorting options: by size (kb or width x height...) by date modified...
# TODO: add multiple width options
# TODO: add thumbnail options...
# TODO: fix ugly end case, come up with better algo for some cases... (permute?)

def imgal(folder, span, max_width, recursive):
	print(folder, span, max_width, recursive)

	# select files...

def create_index(path, span=800, max_width=-1, thumbnails=True):

	if not path.endswith("/"):
		path = path + "/"
		
	if max_width == -1:
		max_width = span

	# collect images files in path
	images = files_by_ext(path, image_exts)
	
	# sort by date modified
	pairs = [(os.path.getmtime(path + i), i) for i in images ]
	pairs.sort()
	filenames = [p[1] for p in pairs]

	imgs = []
	sizes = []
	
	# keep only those that have a readable size
	for i in filenames:
		try:
			sizes += [Image.open(path + i).size]
			imgs += [i]
		except:
			pass

	# squish into max_width size if necessary
	# think about squishing in both directions...
	miw = max_width
	sizes = [(min(miw, w), int((h/w)*min(miw,w))) for w, h in sizes]
	
	# compute layout
	layout = block_layout(sizes, span=span)

	# assemble html



	if thumbnails and True:
		for i in imgs:
			# think about saving work by checking if file is already there...
			try:
				im = Image.open(path + i)
				im.thumbnail((400, 400))
				im.save(path + "." + i + ".thumbnail", "jpeg")
			except:
				pass
		
	fstr = "<a href='{l}'><img src='{f}' width='{w}' height='{h}'></a>"

	div_rows = []	
	for row in layout:
	
		div_items = []
		for ind, w, h in row:
			src=imgs[ind]
			if thumbnails:
				src = "." + src + ".thumbnail"
			div_items.append(fstr.format(f=src, l=imgs[ind], w=int(w-10), h=int(h-10)))	
			
		div_items = ["<div style='width:100%;'>"] + div_items + ["</div>"]
		div_row = "".join(div_items)	
		div_rows += [div_row]
	

	
	subfolders = [f[:-1].split('/')[-1] for f in glob(path+"*/")]
	
	fstr = "<a href='{f}/index.html' style='text-decoration:none; font-size:20pt; padding: 10px; margin: 10px; border-style: solid; border-width:2px'; background-color: white;  display: inline-block;'>{f}</a>"
	
	nav = "".join(fstr.format(f=f) for f in subfolders)
	
	head = """<!DOCTYPE html>
<html>
<head>
<link rel="stylesheet" href="style.css">
</head>"""
	
	a = head
	b = f"<body style='background-color:gray; text-align:center;'><h1>{path}</h1>"
	c = f"<div style='margin: 20px;'>{nav}</div>"
	d = "\n".join(div_rows)
	e = "</body></html>"
	
	html = "\n".join([a,b,c,d,e])
	
	f = open("style.css")
	style = f.read()
	f.close()
	
	f = open(path + "style.css", 'w')
	f.write(style)
	f.close()
	
	f = open(path + "index.html", 'w')
	f.write(html)
	f.close()
	
def block_layout(sizes, span=1000):

	def cost(x,y):
		return np.sum(np.abs(x-y))

	rows = []

	indices = list(range(len(sizes)))
	while len(sizes) > 0:
		ind = 1
		best_perf = span*100
		for k in range(1, min(len(sizes), 10)):
			ws = np.array([s[0] for s in sizes[:k]])
			hs = np.array([s[1] for s in sizes[:k]])
			
			new_h = span/np.sum(ws/hs)
			new_ws = ws/hs*new_h
			
			#perf = cost(new_ws,ws)
			perf = np.sum(np.abs(new_ws-ws))
			if perf <= best_perf:
				best_perf = perf
				ind = k
		
		ws = np.array([s[0] for s in sizes[:ind]])
		hs = np.array([s[1] for s in sizes[:ind]])

		new_h = span*1/np.sum(ws/hs)
		new_ws = ws/hs*new_h
		
		row = list(zip(indices[:ind], new_ws, [new_h]*ind))
		
		
		rows += [row]
		
		sizes = sizes[ind:]
		indices = indices[ind:]
		
	return rows


if __name__ == "__main__":

	for dirpath, dirs, files in os.walk("photos"):
		print(dirpath)

		create_index(dirpath, max_width=256, span=1200)


	



