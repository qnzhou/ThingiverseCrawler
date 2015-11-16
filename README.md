# Thingiverse Crawler #

###About:###

Thingiverse Crawler is a simple script to batch download things from
Thingiverse.  It does not use the thingiverse API because non-web application
flow is not yet supported.

The script dynamically update wait time to prevent it being blocked by
Thingiverse website.

###Example:###

Retrieve information of the newest 1000 things:

    $ ./thingiverse_crawler.py 1000

A `summary.csv` will be created.  It contians the following information:

    * ``thing_id``
    * ``file_id``
    * ``file``: where to store the output file.
    * ``license``: info about the license it is published in.
    * ``link``: direct link for download.

To download all 1000 files:

    $ ./download_model.py summary.csv

###Author:###

Qingnan Zhou

New York University

<https://www.cs.nyu.edu/~qnzhou/>
