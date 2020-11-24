# IMGAL

A simple python script to generate a pleasing static html image gallery of the images in a given folder.

## Example

![imgal-example](imgal-example.png)

## Usage

```
Usage: imgal.py [OPTIONS]

Options:
  -p, --path TEXT
  -o, --output TEXT
  -s, --sort TEXT
  -g, --group / --no-group
  -w, --width INTEGER
  -m, --max-img-width INTEGER
  -n, --nav-bar / --no-nav-bar
  --nav-path TEXT
  -r, --recurse / --dont-recurse
  -t, --thumbnails / --no-thumbnails
  --help                          Show this message and exit.
```

## Dependencies

## TODOs

- [x] recreate a thumbnail when image is modified with date AFTER modification date of thumbnail
- [ ] Create height cutoff for thumbnails... i.e. make hard limit for aspect ratio
- [ ] create thumbnail size options
- [ ] create redo all thumbnails options?
- [ ] Implement more sorting options
	- [x] date modified
- [ ] implement binning option
- [ ] implement reverse sort option
- [ ] Add option for custom html insertion in head and/or body (this is to manage multiple versions)
- [ ] Implement alt-text or text overlay options
- [ ] Clean up layout block algorithm to be nicer
	- [ ] try optimizing for more than 1 row at a time
	- [ ] fix blown up images at the bottom of the page, either globally optimizing to be pretty or otherwise fix
- [ ] Fix issue with horizontal margins (CSS issue)
- [ ] use setup tools to make system-wide command line tool, have default option of no path to generate in current directory
