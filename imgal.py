from PIL import Image
from glob import glob
import numpy as np
import os
import sys
import click


"""
	HELPER FUNCTIONS
"""
image_exts = ["png", "gif", "jpg", "jpeg", "bmp"]

def is_ext(f, exts):
	return any( f.lower().endswith("."+e) for e in exts )

def files_by_ext(path, exts, sort=None):
	if type(exts) != type([]):
		return "need list"
	
	filenames = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
		
	if sort == "modified":
		pairs = [(os.path.getmtime(os.path.join(path, i)), i) for i in filenames ]
		pairs.sort()
		filenames = [p[1] for p in pairs]

	filtered = [f for f in filenames if is_ext(f, exts)]	
	
	return filtered

"""
	MAIN COMMAND LINE FUNCTION
"""

@click.command()

@click.option("-p", "--path",		type=str, default="")
@click.option("-o", "--output", 	type=str, default="index")

@click.option("-s", "--sort", 		type=str, default="none")
@click.option("--group/--no-group", "-g/ ", default=False) 

@click.option("--width", "-w", 		type=int, default=800)
@click.option("--max-img-width", "-m", type=int,  default=-1)

@click.option("--nav-bar/--no-nav-bar", "-n/ ", default=False)
@click.option("--nav-path", 					type=str, default=None)
@click.option("--recurse/--dont-recurse", "-r/ ",	 	default=False)
@click.option("--thumbnails/--no-thumbnails", "-t/ ", 	default=False)

def imgal(path, output, nav_bar, nav_path, sort, group, width, max_img_width, recurse, thumbnails):

	# Step 1: Clean all input options	
	
	# fix max-img-width default
	if max_img_width == -1:
		max_img_width = width

	# fix nav-path default
	if nav_path is None:
		if path[-1] == '/':
			nav_path = path[:-1].split('/')[-1]
		else:
			nav_path = path.split('/')[-1]

	# Step 2: Create index for specified folder
	imgal_single(path, output, nav_bar, nav_path, sort, group, width, max_img_width, recurse, thumbnails)
	
	# Step 3: If recurse, repeat on all subdirectories
	if recurse:
		for x in os.walk(path):
			if x[0] == path:
				continue
			folder = os.path.relpath(x[0], start=path)
			print("...generating index for ", folder)
			
			imgal_single(os.path.join(path, folder), output, nav_bar, os.path.join(nav_path, folder), sort, group, width, max_img_width, recurse, thumbnails)
	
def imgal_single(path, output, nav_bar, nav_path, sort, group, width, max_img_width, recurse, thumbnails):

	images = files_by_ext(path, image_exts, sort=sort)
	links = [i for i in images]

	# Create thumbnails if specified
	if thumbnails:
		update_thumbnails(path)
		images = ["." + i + ".thumbnail" for i in images]	
		
	# Extract size information for block layout algorithm
	imgs = []
	for i, l in zip(images, links):
		# Use try block in case Pillow.Image fails
		try:
			# Use thumbnail size if thumbnail option specified
			if thumbnails:
				s = Image.open(os.path.join(path, "." + l + ".thumbnail")).size
			else:
				s = Image.open(os.path.join(path, l)).size

			# Compress image size using max_img_width
			w, h = s
			miw = max_img_width
			s = (min(miw, w), int((h/w)*min(miw,w)))
			
			imgs += [(i,l,s)]
			
		except OSError:
			pass	

	# Hackish way to fix no images in folder edge case
	if len(imgs) != 0:
		images, links, sizes = zip(*imgs)
	else:
		images, links, sizes = [], [], []
		
	# Generate the html for the gallery
	gallery = create_gallery(images=images, links=links, sizes=sizes, span=width)

	# Construct the nav bar and folder list
	if nav_bar:
		subfolders = [f[:-1].split('/')[-1] for f in glob(os.path.join(path,"*/"))]
		subfolders.sort()
		
		fstr = "<a href='{f}/{output}.html' class='folder'>{f}</a>"
		nav = "\n\t".join(fstr.format(f=f, output=output) for f in subfolders)
		
		if nav_path is not None:
			if nav_path[-1] == "/":
				nav_path = nav_path[:-1]	
			items = nav_path.split("/")
		else:
			items = path.split("/")
			
		items = path.split("/") if nav_path is None else nav_path.split("/")
			
		path_link = ""
		href = ".."
		for k, i in enumerate(items):
			href = "/".join([".."]*(len(items)-k-1))
			if href == "":
				href = "."
			path_link += f"<a href='{href}/{output}.html'>{i}</a>/"
	else:
		nav = ""
		path_link = ""	
	
	# Collect style and html index templates	
	with open("style.css") as f:
		style = f.read()
	
	with open("template.html") as f:
		html = f.read()
	
	# Substitute into template	
	html = html.format(folder=path, nav=nav, path_link=path_link, css=style, gallery=gallery)
	
	# Write index file
	with open(os.path.join(path, output + ".html"), 'w') as f:
		f.write(html)

def update_thumbnails(path, size=(300,300)):

	# Collect all image files and .thumbnail files in path
	thumbnails = files_by_ext(path, ["thumbnail"])
	images = files_by_ext(path, image_exts)

	for i in images:
	
		# Check to see if date modified of image file is before date modified of thumbnail
		if "." + i + ".thumbnail" in thumbnails:
			thumb_time = os.path.getmtime(os.path.join(path, "." + i + ".thumbnail"))
			img_time = os.path.getmtime(os.path.join(path, i))
			if img_time < thumb_time:
				continue

		# Try to create thumbnail
		try:
			im = Image.open(os.path.join(path, i))
			im.thumbnail(size)
			im.save(os.path.join(path, "." + i + ".thumbnail"), "png")
		except OSError:
			print("Failed to generate thumbnail for ", path, i)
			

def create_gallery(images=None, links=None, alts=None, sizes=None, span=800):
	
	# assemble gallery with block layout
	fstr = "<a href='{l}' target='_blank' ><img src='{f}' width='{w}' {alt} height='{h}'></a>"
	layout = block_layout(sizes, span=span)
	
	div_rows = []	
	for row in layout:
		alt_text = ""
		div_items = [fstr.format(f=images[ind], l=links[ind], alt=alt_text, w=int(w-10), h=int(h-10)) for ind, w, h in row]
		div_items = ["<div>"] + div_items + ["</div>"]
		div_row = "\n".join(div_items)	
		div_rows += [div_row]
	
	gallery = "\n\n".join(div_rows)
	
	return gallery
	
def block_layout(sizes, span=1000):

	# Define the cost function
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
		
		new_ws = [int(w) for w in new_ws]
		new_ws[0] = new_ws[0] + (span - sum(new_ws))
		
		row = list(zip(indices[:ind], new_ws, [int(new_h)]*ind))
		
		rows += [row]
		
		sizes = sizes[ind:]
		indices = indices[ind:]
		
	return rows

if __name__ == "__main__":
	imgal()
	
