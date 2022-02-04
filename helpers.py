import os
from glob import glob
import numpy as np

""" Helper functions """

# Collect style and html index templates	
with open("index_style.css") as f:
	INDEX_STYLE = f.read()

with open("script.js") as f:
	SCRIPT = f.read()

with open("index_template.html") as f:
	HTML_TEMPLATE = f.read()
	
with open("folder_template.html") as f:
	FOLDER_TEMPLATE = f.read()	

def is_ext(f, exts):
	return any( f.lower().endswith("."+e) for e in exts )

def files_by_ext(path, exts):
	if type(exts) != type([]):
		exts = [exts]
	
	filenames = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
	filtered = [f for f in filenames if is_ext(f, exts)]	
	
	return filtered
	
def files_by_ext_recurse(path, exts):

	all_files = []

	for x in os.walk(path):
		
		relpath = os.path.relpath(x[0], start=path)
		
		if relpath == ".":
			relpath = ""
		
		all_files += [os.path.join(relpath, p) for p in files_by_ext(x[0], exts)]		
		
	return all_files



def heatmap(x):
	return int(0.5*np.log2(1+x))

def create_nav(path, output, **kwargs):

	subfolders = [f for f in glob(os.path.join(path,"*/"))]
	tags = []
	tag_pairs = []	
		
	for folder in subfolders:
	
		name 			= folder[:-1].split('/')[-1]

		if kwargs["heatmap"] and "exts" in kwargs:
			file_count 		= len(files_by_ext_recurse(folder, kwargs["exts"]))
			heat 			= heatmap(file_count)
		else:
			heat = 0

		html_tag = FOLDER_TEMPLATE.format(folder=name, heat=heat, output=output)
		
		sort_key = name
		tag_pairs.append((sort_key, html_tag))

	tag_pairs.sort()
	tags = [t[1] for t in tag_pairs]
	nav = "\n\t".join(tags)
		
	return nav

def create_nav_bar(path, nav_path, output, **kwargs):
			
	items = path.split("/") if nav_path is None else nav_path.strip("/").split("/")
			
	path_link = ""
	href = ".."
	for k, i in enumerate(items):
		href = "/".join([".."]*(len(items)-k-1))
		if href == "":
			href = "."
		path_link += f"<a href='{href}/{output}.html'>{i}</a>/"

	return path_link
	
def gen_gal(root, exts, **kwargs):

	kwargs_defaults = {
		"flat" 			:  False,
		"sort_func"   	: lambda x : x,
		"select_func" 	: lambda x: True
	}

	for key in kwargs_defaults:
		if key not in kwargs:
			kwargs[key] = kwargs_defaults[key]

	# recurse or not... high level selection
	if kwargs["flat"]:
		pdfs = helpers.files_by_ext_recurse(root, "pdf")
	else:
		pdfs = helpers.files_by_ext(root, "pdf")

	# select	
	# much to add... generally should be a function
	files = [f for f in files if select_func(f)]
	
	# sort
	# much to add... general should be a function
	pdfs = sorted(pdfs, key= sort_func)
	
	items = []
	
	for pdf in pdfs:
		card_html = card_map(root, pdf, **kwargs)
		items += [card_html]
	
	s = "\n".join(items)
	
	return s	
	
	
def gen_index(index_path, **kwargs):	

	kwargs_defaults = {
		"gallery"		: "",
		"flat_gallery"	: "",
		"gal_style"		: "",
		"output"		: "index",
		"nav"			: True,
		"nav_root"		: None,
		"heatmap"		: False,
		"heatmap_exts"	: ["none"],
		"header"		: "",
		"flatgal"		: False,
		"css_path"		: None,
		"html_path"		: None,
		"script_path"	: None,
		"duplicate_galleries": False
	}
	
	for key in kwargs_defaults:
		if key not in kwargs:
			kwargs[key] = kwargs_defaults[key]
	
	# Construct the nav bar and folder list
	nav_html 		= ""
	path_link_html 	= ""
	
	if kwargs['nav']:		
		nav_html 		= create_nav(index_path, kwargs['output'], exts=kwargs["heatmap_exts"], heatmap=True)
		nav_bar_html 	= create_nav_bar(index_path, kwargs['nav_root'], kwargs["output"])	
	
	# manage header as either file or string
	try:
		header = open(kwargs['header']).read()
	except OSError:
		header = kwargs['header']
	
	gallery 		= kwargs["gallery"]
	flat_gallery 	= kwargs["flat_gallery"]
	
	if not kwargs['duplicate_galleries'] and gallery.strip() == flat_gallery.strip():
		flat_gallery = ""
	
	# Substitute into template
	
	html_args = {
		"title"			: index_path.strip("/").split("/")[-1],
		"css"			: INDEX_STYLE,
		"card_style"	: kwargs["gal_style"],
		"script"		: SCRIPT,
		"header"		: header,
		"nav"   		: nav_html,
		"path_link"		: nav_bar_html,
		"gallery" 		: gallery,
		"flat_gallery"	: flat_gallery
	}
	
	html = HTML_TEMPLATE.format(**html_args)

	return html
	
	
