# Thingiverse Crawler #

###About:###

Thingiverse Crawler is a simple script to batch download things from
Thingiverse.  It does not use the thingiverse API because non-web application
flow is not yet supported.

###Example:###

Retrieve information of the newest 1000 things:

    $ ./thingiverse_crawler.py 1000

Two files will be created: `links.txt` and `summary.csv`.  To download all 1000 things:

    $ wget -i links.txt

The summary file contains the thing ID and file ID of each file.

    $ head summary.csv
    thing_id, fild_id, link
    894587,1414437,https://thingiverse-production-new.s3.amazonaws.com/assets/e1/9b/6e/ca/ad/CORE.stl
    894587,1414438,https://thingiverse-production-new.s3.amazonaws.com/assets/26/7c/82/a9/77/LAMPSHADE.stl
    ...

###Author:###

Qingnan Zhou
