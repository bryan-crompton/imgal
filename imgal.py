from PIL import Image, ImageStat
import json
import numpy as np
import os
import sys
import click

import helpers
from helpers import is_ext, files_by_ext, files_by_ext_recurse

with open("style.css") as f:
	STYLE = f.read()

with open("index_template.html") as f:
	HTML_TEMPLATE = f.read()

with open("img_card_template.html") as f:
	IMG_CARD_TEMPLATE = f.read()

image_exts = ["png", "gif", "jpg", "jpeg", "bmp"]
	
def update_meta(path):
		
	for im in files_by_ext(path, image_exts):
		if update_meta_file(path, im):
			print("Updating metadata for ", im)

def update_meta_file(path, filename):

	# check to see if meta exists
	
	meta_filename = os.path.join(path, "." + filename + ".json.meta")
	full_filename = os.path.join(path, filename)
	
	if os.path.exists(meta_filename):
		meta = json.load(open(meta_filename))
		if os.path.getmtime(full_filename) < os.path.getmtime(meta_filename):
			return False
			
	else:
		meta = {"description":"", "url":""}

	im = Image.open(full_filename)
	
	try:
		c = im.resize((1, 1)).getpixel((0, 0))
		color = '#{:02x}{:02x}{:02x}'.format(*c)
	except (TypeError, IndexError) as e:
		color = "#FFFFF"


	meta['color'] = color
	
	s = im.size
	meta['size'] = s
	meta['filesize'] 		= os.path.getsize(full_filename)	
	meta['compression'] 	= s[0]*s[1]*3/meta['filesize']
	meta['aspect'] 			= s[0]/s[1] 
	meta['diagonal'] 		= (s[0]**2+s[1]**2)**0.5
	meta['modified'] 		= os.path.getmtime(full_filename)
	
	try:
		meta['brightness'] 		= ImageStat.Stat(im.convert('L')).mean[0]
		
	except OSError:
		meta['brightness'] = 1
   
	for key in meta:
		if isinstance(meta[key], (int, float)):
			meta[key] = int(100*meta[key]) / 100  
	
	json.dump(meta, open(meta_filename, 'w'), indent=4)
	return True

	

@click.command()

@click.option("-p", "--path",		type=str, default=os.getcwd())
@click.option("-o", "--output", 	type=str, default="index")
@click.option("--recurse/--dont-recurse", "-r/ ",	 			default=False)
@click.option("--flatten/--dont-flatten", "-f/ ", default=False)
@click.option("-s", "--sort", 		type=str, default="none")
@click.option("--reverse-sort/--no-reverse-sort", "-z/ ", default=False)
@click.option("--nav/--no-nav", "-n/ ", 				default=False)
@click.option("--nav-root", 					type=str, 		default=None)
@click.option("--heatmap-nav/--no-heatmap-nav", "-c/ ", default=True)
@click.option("--verbose/--quiet", "-v/ ", default=False)
@click.option("--header", "-h", type=str, default="")

# imgal specific options
@click.option("--width", "-w", 		type=int, default=800)
@click.option("--max-img-width", "-m", type=int,  default=-1)
@click.option("--thumbnails/--no-thumbnails", "-t/ ", 			default=False)
@click.option("--redo-thumbnails/--dont-redo-thumbnails", "-c",	default=False)
@click.option("--thumbnail-size", type=int, 					default=300)
@click.option("--description/--no-description", "-d/ ", 		default=False)

def root(**kwargs):

	path 			= kwargs['path']
	nav_root 		= kwargs['nav_root']

	# Step 1: Clean all input options	
	if kwargs["nav_root"] is None:
		kwargs["nav_root"] = path.strip('/').split('/')[-1]
	kwargs["nav_path"] = nav_root
	
	# imgal specific 
	if kwargs['max_img_width'] == -1:
		kwargs['max_img_width'] = kwargs['width']	
	
	if kwargs['redo_thumbnails']:
		kwargs['thumbnails'] = True
	# end imgal specific
	
	if kwargs["verbose"]:	
		print(json.dumps(kwargs, indent=4))

	# Step 2: Create index for specified folder
	html = gen_index(**kwargs)

	with open(os.path.join(path, kwargs['output'] + ".html"), 'w') as f:
		f.write(html)
	
	# Step 3: If recurse, repeat on all subdirectories
	if kwargs['recurse']:
		for x in os.walk(path):

			if x[0] == path:
				continue
		
			if "." in  x[0][0]:
				if kwargs['verbose']:
					print('skipping hidden folder ', x[0])
				continue
				
			folder = os.path.relpath(x[0], start=path)
			
			if kwargs['verbose']:
				print("...generating index for ", folder)

			kwargs['path'] 		= os.path.join(path, folder)
			kwargs['nav_path'] 	= os.path.join(nav_root, folder)
					
			## unique to imgal
			# Create thumbnails if specified
			update_meta(kwargs['path'])
			if kwargs['thumbnails']:
				thumbnail_size 		= 	kwargs['thumbnail_size']
				update_thumbnails(kwargs['path'], (thumbnail_size, thumbnail_size), redo=kwargs['redo_thumbnails'])	
			## end unique to imgal
			
			html = gen_index(**kwargs)
			with open(os.path.join(kwargs['path'], kwargs['output'] + ".html"), 'w') as f:
				f.write(html)

def gen_index(**kwargs):	
			
	path 				= 	kwargs['path']
	sort 				= 	kwargs['sort']
	thumbnails 			= 	kwargs['thumbnails']

	description 		= 	kwargs['description']
	max_img_width 		= 	kwargs['max_img_width']
	width 				= 	kwargs['width']	
	output 				= 	kwargs['output']
	
	# Construct the nav bar and folder list
	nav_html 		= ""
	path_link_html 	= ""
	
	if kwargs['nav']:		
		nav_html 		= helpers.create_nav(path, kwargs['output'], exts=image_exts, heatmap=True)
		nav_bar_html 	= helpers.create_nav_bar(path, kwargs['nav_path'], output)	
	
	# manage header as either file or string
	try:
		header = open(kwargs['header']).read()
	except OSError:
		header = kwargs['header']
	
	# create gallery

	#images = files_by_ext_recurse(path, image_exts, sort=sort)
	images = files_by_ext(path, image_exts)
	links = [i for i in images]
	
	if kwargs["thumbnails"]:
		images = ["." + i + ".thumbnail" for i in images]
	
	#print(images)

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
			
			meta = json.load(open(os.path.join(path, "." + l + ".json.meta")))
			
			if description:
				alt = "title='" + meta['description'] + "'"
			else:
				alt = ""
			
			# room to expand here..
			if sort in meta:
				sort_param = meta[sort]
			elif sort == "width":
				sort_param = meta["size"][0]
			elif sort == "height":
				sort_param = meta["size"][1]
			else:
				sort_param = i
			
			w, h = s
			miw = max_img_width
			s = (min(miw, w), int((h/w)*min(miw,w)))
			
			
			imgs += [(sort_param, i,l,s, alt)]
			
		except OSError:
			pass	
					
	imgs.sort()
	if kwargs['reverse_sort']:
		imgs.reverse()

	# Hackish way to fix no images in folder edge case
	if len(imgs) != 0:
		__, images, links, sizes, descriptions = zip(*imgs)
	else:
		__, images, links, sizes, descriptions = [], [], [], [], []

	# Generate the html for the gallery
	gallery = create_gallery(images=images, links=links, sizes=sizes, alts=descriptions, span=width)

	# Generate flat gallery if desired
	flat_gallery = ""
	
	# construct index
	html_args = {
		"title"			: path.strip("/").split("/")[-1],
		"css"			: STYLE,
		"script"		: "",
		"header"		: header,
		"nav"   		: nav_html,
		"path_link"		: nav_bar_html,
		"gallery" 		: gallery,
		"flat_gallery"	: flat_gallery
	}
	html = HTML_TEMPLATE.format(**html_args)
	return html
	

def update_thumbnails(path, size=(300,300), redo=False):

	# Collect all image files and .thumbnail files in path
	thumbnails = files_by_ext(path, ["thumbnail"])
	images = files_by_ext(path, image_exts)

	for i in images:
		if not redo:
			# Check to see if date modified of image file is before date modified of thumbnail
			if "." + i + ".thumbnail" in thumbnails:
				thumb_time = os.path.getmtime(os.path.join(path, "." + i + ".thumbnail"))
				img_time = os.path.getmtime(os.path.join(path, i))
				if img_time < thumb_time:
					continue

		# Try to create thumbnail
		try:
			im = Image.open(os.path.join(path, i))
			
			s = im.size
			# if heigh is more than 2x width, crop thumbnail...
			if s[1] > 2*s[0]:
				im = im.crop((0,0, s[0], 2*s[0]))
			
			im.thumbnail(size)
			im.save(os.path.join(path, "." + i + ".thumbnail"), "png")
		except OSError:
			print("Failed to generate thumbnail for ", path, i)
			


def create_gallery(images=None, links=None, alts=None, sizes=None, span=800):
	
	# assemble gallery with block layout
	fstr = "<a href='{l}' target='_blank' class='img-link'><img src='{f}' width='{w}' {alt} height='{h}'></a>"
	layout = block_layout(sizes, span=span)
	
	div_rows = []	
	for row in layout:

		div_items = [fstr.format(f=images[ind], l=links[ind], alt=alts[ind], w=int(w-10), h=int(h-10)) for ind, w, h in row]
		div_items = ["<div>"] + div_items + ["</div>"]
		div_row = "".join(div_items)	
		div_rows += [div_row]
	
	gallery = "\n\n".join(['<div>'] + div_rows + ['</div>'])
	
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
		for k in range(1, min(len(sizes)+1, 10)):
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
		new_ws[0] = new_ws[0] + (span + 10 - sum(new_ws))

		if len(sizes) == ind and ind == 1:
			alpha = np.min(new_ws/ws) 
			if alpha >= 2:
				print(np.min(new_ws/ws), new_h)
				new_ws = [ws[0]*2]
				new_h = hs[0]*2

		
		row = list(zip(indices[:ind], new_ws, [int(new_h)]*ind))
		
		rows += [row]
		
		sizes = sizes[ind:]
		indices = indices[ind:]
		
	return rows

if __name__ == "__main__":
	root()
	
