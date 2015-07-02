#!/usr/bin/env python
"""
Data File Converter: Convert from {csv, tsv, json} to {csv, tsv, json, html}

Usage:
  data_file_converter.py [--from=<format>] [--to=<format>] <filename>

Options:
  --from=<format>  Input format (csv, tsv) [default: tsv]
  --to=<format>    Output format (csv, tsv, json, html) [default: json]
"""

from docopt import docopt
import pandas as pd

if __name__ == '__main__':
    arguments = docopt(__doc__, version='Data Converter')

    filename = arguments['<filename>']
    from_format = arguments['--from']
    to_format = arguments['--to']

    if from_format == 'csv':
        data = pd.read_csv(filename)
    elif from_format == 'tsv':
        data = pd.read_csv(filename, sep="\t")
    else:
        raise Exception("{0} from-format not supported".format(from_format))

    if to_format == 'csv':
        print data.to_csv()
    elif to_format == 'tsv':
        print data.to_csv(sep="\t")
    elif to_format == 'json':
        print data.to_json(orient='records')
    elif to_format == 'html':
        print data.to_html()
    else:
        raise Exception("{0} to-format not supported".format(to_format))
