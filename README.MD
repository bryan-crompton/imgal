# IMGAL

A simple python script to generate a pleasing static html image gallery of the images in a given folder.

## Examples

## Usage

[To fill in]

Show how to override a specific folder with recursive stuff.

Show how to generate two pairs of different widths.

Show how to create html links to flip between widths.

## Dependencies

## TODOs

- [ ] Deal with changing thumbnails (look for dates modified conflicts)
- [ ] Create height cutoff for thumbnails... i.e. make hard limit for aspect ratio
- [ ] Implement more sorting options
	- [x] date modified
- [ ] Add option for custom html insertion in head and/or body (this is to manage multiple versions)
- [ ] Clean up layout block algorithm to be nicer
	- [ ] try optimizing for more than 1 row at a time
	- [ ] fix blown up images at the bottom of the page, either globally optimizing to be pretty or otherwise fix
- [ ] Fix issue with horizontal margins (CSS issue)
- [ ] Implement alt-text or text overlay options
- [ ] use setup tools to make system-wide command line tool, have default option of no path to generate in current directory
