import sys, argparse

def write_html(output):
	f = open(vars(args)['output'], 'w')
	print_str = """
			<!DOCTYPE html>
			<html>
			<head>
			</head>
			<body style="font:14px/1.5 Arial, Helvetica, sans-serif;">
			    <h1><center>Harmony Point</center></h1>
			  	<h2 id="title"><center><small><i>Secure Compute Results</i></small></center></h2>
			  	<h4><center>Significant Genes Identified by 1185 Breast Cancer Samples</center></h4>
				<center><img src="image.png"/></center>
			</body>
			</html>
	"""

	f.write(print_str)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Generate HTML Harmony Point Page.')
	parser.add_argument('-i', '--input', dest = "input", nargs='?', default=None, help='Input file.')
	parser.add_argument('-o', '--output', dest = "output", nargs='?', default=None, help='Output file.')
	args = parser.parse_args()

	write_html(vars(args)['output'])