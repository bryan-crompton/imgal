import os

with open("markdown_template.html") as f:
	MARKDOWN_TEMPLATE = f.read()
with open("markdown_style.css") as f:
	MARKDOWN_STYLE = f.read()	

pandoc_options="-f markdown+hard_line_breaks --mathjax"

def render_markdown(path, output, md_file):

	f = os.path.join(path, md_file)
	fn = md_file
	
	last = path.split("/")[-1]	
	body = os.popen(f"pandoc {f} {pandoc_options}").read()
	
	path_link = f"<a href='./{output}.html'>{last}</a>/{fn}"
	
	template_args = {
		"script"		: "",
		"title"			: fn,
		"path_link"		: path_link,
		"css"			: MARKDOWN_STYLE,
		"body"			: body
	}
		
	html = MARKDOWN_TEMPLATE.format(**template_args)
	
	return html

