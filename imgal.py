from PIL import Image, ImageStat
import json
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
	
def files_by_ext_recurse(path, exts, sort=None):

	all_files = []

	for x in os.walk(path):
		relpath = os.path.relpath(x[0], start=path)
		all_files += [os.path.join(relpath, p) for p in files_by_ext(x[0], exts)]		
		
	print(all_files)
	return all_files
	

"""
	MAIN COMMAND LINE FUNCTION
"""

@click.command()

@click.option("-p", "--path",		type=str, default=os.getcwd())
@click.option("-o", "--output", 	type=str, default="index")

@click.option("-s", "--sort", 		type=str, default="none")
@click.option("--reverse-sort/--no-reverse-sort", "-z/ ", default=False)
@click.option("--group/--no-group", "-g/ ", default=False) 

@click.option("--width", "-w", 		type=int, default=800)
@click.option("--max-img-width", "-m", type=int,  default=-1)

@click.option("--nav-bar/--no-nav-bar", "-n/ ", 				default=False)
@click.option("--nav-path", 					type=str, 		default=None)
@click.option("--recurse/--dont-recurse", "-r/ ",	 			default=False)
@click.option("--thumbnails/--no-thumbnails", "-t/ ", 			default=False)
@click.option("--redo-thumbnails/--dont-redo-thumbnails", "-c",	default=False)
@click.option("--thumbnail-size", type=int, 					default=300)
@click.option("--description/--no-description", "-d/ ", 		default=False)
@click.option("--header", "-h", type=str, default="")

def imgal(**kwargs):

	path 			= kwargs['path']
	nav_path 		= kwargs['nav_path']

	# Step 1: Clean all input options	

	# fix max-img-width default
	if kwargs['max_img_width'] == -1:
		kwargs['max_img_width'] = kwargs['width']

	# fix nav-path default
	if nav_path is None:
		if path[-1] == '/':
			kwargs['nav_path'] = path[:-1].split('/')[-1]
		else:
			kwargs['nav_path'] = path.split('/')[-1]

	if kwargs['redo_thumbnails']:
		kwargs['thumbnails'] = True

	# Step 2: Create index for specified folder
	print(json.dumps(kwargs, indent=4))
	imgal_single(**kwargs)
	
	# Step 3: If recurse, repeat on all subdirectories
	if kwargs['recurse']:
		for x in os.walk(path):
			if x[0] == path:
				continue
			folder = os.path.relpath(x[0], start=path)
			print("...generating index for ", folder)
			
			kwargs['path'] = os.path.join(path, folder)
			kwargs['nav_path'] = os.path.join(nav_path, folder)
			
			imgal_single(**kwargs)

def imgal_single(**kwargs):				
	path 				= 	kwargs['path']
	sort 				= 	kwargs['sort']
	thumbnails 			= 	kwargs['thumbnails']
	thumbnail_size 		= 	kwargs['thumbnail_size']
	description 		= 	kwargs['description']
	max_img_width 		= 	kwargs['max_img_width']
	width 				= 	kwargs['width']	
	nav_bar 			= 	kwargs['nav_bar']
	output 				= 	kwargs['output']
	nav_path 			= 	kwargs['nav_path']
	
	
	try:
		header = open(kwargs['header']).read()
	except OSError:
		header = kwargs['header']



	images = files_by_ext_recurse(path, image_exts, sort=sort)
	links = [i for i in images]

	# Create thumbnails if specified
	update_meta(path)
	
	if thumbnails:
		update_thumbnails(path, (thumbnail_size, thumbnail_size), redo=kwargs['redo_thumbnails'])
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
	html = html.format(folder=path, header=header, nav=nav, path_link=path_link, css=style, gallery=gallery)
	
	# Write index file
	with open(os.path.join(path, output + ".html"), 'w') as f:
		f.write(html)

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
	imgal()
	
