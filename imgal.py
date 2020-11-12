from PIL import Image
from glob import glob
import numpy as np
import os
import sys

import click

@click.command()
@click.argument("folder")
@click.option("--width", default=800)
@click.option("--max-width", default=-1)
@click.option("--page-limit", default=-1)
@click.option("--recursive/--not-recursive", default=False)
@click.option("--folders/--no-folders", default=False)

# TODO: add sorting options: by size (kb or width x height...) by date modified...
# TODO: add multiple width options
# TODO: add thumbnail options...

def imgal(folder, width, max_width, page_limit, recursive, folders):
	print(folder, width, max_width, page_limit, recursive, folders)

	if max_width == -1:
		max_width = width
	
	if page_limit == -1:
		page_limit = None

	if not folder.endswith("/"):
		folder = folder + "/"

	filenames = get_imgs(folder, recursive=recursive)

	# try to get sizes if possible...
	sizes = []
	imgs = []
	
	for i in filenames:
		try:
			sizes += [Image.open(i).size]
			imgs += [i.split('/')[-1]]
		except:
			pass
	
	# scale sizes based on size limit
	miw = max_width
	sizes = [(min(miw, w), int((h/w)*min(miw,w))) for w, h in sizes]
	
	html = f"<head><title>{folder}</title></head>"
	
	gallery = gallery_html(imgs, sizes, width=width) 
	
	subfolders = glob(folder + "*/")
	subfolders += ["../"]
	nav = ""
	for f in subfolders:
		print(f)
		fold = f.split('/')[-2]
		nav += f"<a href='{fold}/index.html'>{f[:-1]}</a>"
	
	gallery = nav + gallery
	
	html += f"<body style='background-color:gray;'><h1>{folder}</h1>" + gallery + "</body>"

	f = open(f"{folder}/index.html", 'w')
	f.write(html)
	f.close()

	# select files...

def get_imgs(path, recursive=False):
	if recursive:
		pngs = get_of_type(path, "png")	
		jpgs = get_of_type(path, "jpg")
		jpegs = get_of_type(path, "jpeg")
		bmps = get_of_type(path, "bmp")
		gifs = get_of_type(path, "gif")		
		imgs = pngs + jpegs + jpgs + bmps + gifs
		return imgs
	else:
		pngs = glob(path + "*.png") + glob(path + "*.PNG")
		jpgs = glob(path + "*.jpg") + glob(path + "*.JPG")
		jpegs = glob(path + "*.jpeg") + glob(path + "*.JPEG")
		bmps = glob(path + "*.bmp")	+ glob(path + "*.BMP")
		gifs = glob(path + "*.gif")	+ glob(path + "*.GIF")	
		imgs = pngs + jpegs + jpgs + gifs + bmps
		return imgs

def gallery_html(filenames, sizes, width=1000, margin=10):
	
	body = """<div style='margin: auto; text-align: center; background-color:gray;' >{gallery}</div>"""
	

	lines = []

	pairs = list(zip(filenames, sizes))

	while len(sizes) > 0:
		ind = 1
		best_perf = 1000000
		for k in range(1, min(len(sizes), 10)):
			
			ws = np.array([s[0] for s in sizes[:k]])
			hs = np.array([s[1] for s in sizes[:k]])
			
			new_h = width/np.sum(ws/hs)
			new_ws = ws/hs*new_h

			perf = np.sum(np.abs(new_ws-ws))
			if perf <= best_perf:
				best_perf = perf
				ind = k
		
		#ind = 5
		
		ws = np.array([s[0] for s in sizes[:ind]])
		hs = np.array([s[1] for s in sizes[:ind]])

		new_h = width*1/np.sum(ws/hs)
		new_ws = ws/hs*new_h
		s = ""
		m = 10
		
		names = filenames[:ind]
		
		for w, n in zip(new_ws, names):
			img = f"<img src='{n}' style='width:{int(w)-m}; height:{int(new_h)-m}; box-sizing: border-box; margin-left: 10px; margin-bottom: 10px; display: inline-block; background-color: black;'>"
			a = f"<a href='{n}' target='_blank'>{img}</a>"
			s += a

		line = f"<div style='width:100%;'>{s}</div>"
		lines += [line]
		
		sizes = sizes[ind:]
		filenames = filenames[ind:]
		
	gallery = "\n\n".join(lines)
	body = body.format(gallery=gallery)

	return body

def get_of_type(folder, ext):
	filenames = []
	for (path, dirs, files) in os.walk(folder):
		filenames += [path + "/" + f for f in files if f.lower().endswith("." + ext)]
	return filenames

def get_imgs(path, recursive=False):
	if recursive:
		pngs = get_of_type(path, "png")	
		jpgs = get_of_type(path, "jpg")
		jpegs = get_of_type(path, "jpeg")
		bmps = get_of_type(path, "bmp")
		gifs = get_of_type(path, "gif")		
		imgs = pngs + jpegs + jpgs + bmps + gifs
		return imgs
	else:
		pngs = glob(path + "*.png") + glob(path + "*.PNG")
		jpgs = glob(path + "*.jpg") + glob(path + "*.JPG")
		jpegs = glob(path + "*.jpeg") + glob(path + "*.JPEG")
		bmps = glob(path + "*.bmp")	+ glob(path + "*.BMP")
		gifs = glob(path + "*.gif")	+ glob(path + "*.GIF")	
		imgs = pngs + jpegs + jpgs + gifs + bmps
		return imgs
		
if __name__ == "__main__":

	imgal()
	sys.exit()


