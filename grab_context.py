#!/usr/bin/env python

""" Retrieve context data from each thing.
"""

import argparse
import csv
import datetime
import re
import requests
import numpy as np
from thingiverse_crawler import get_url

def extract_publish_time(contents):
    pattern = "<time datetime=\"([\w\s\-:]*)\">";
    r = re.findall(pattern, contents);
    if (len(r) != 1):
        return None;
    return datetime.datetime.strptime(r[0], "%Y-%m-%d %H:%M:%S GMT");

def extract_category(contents):
    pattern = "\"/categories/([\w\-]*)(/([\w\-]*))?\"";
    r = re.findall(pattern, contents);
    if (len(r) == 0):
        return None;

    assert(len(r[0]) == 3);
    return r[0][0], r[0][2];

def extract_tags(contents):
    pattern = "\"/tag:([\w\-]*)\"";
    r = re.findall(pattern, contents);
    if (len(r) == 0):
        return [];
    return r;

def grab_context(thing_id):
    print("Thing id: {}".format(thing_id));
    url = "http://www.thingiverse.com/thing:{}".format(thing_id);
    contents = get_url(url);

    publish_time = extract_publish_time(contents);
    category = extract_category(contents);
    tags = extract_tags(contents);

    print("Published time: {}".format(publish_time.isoformat()));
    print("Category      : {}".format(category));
    print("Tags          : {}".format(tags));
    return publish_time, category, tags;

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__);
    parser.add_argument("summary", help="summary file");
    return parser.parse_args();

def main():
    args = parse_args();
    summary_file = args.summary;
    with open(summary_file, 'r') as fin:
        csv_reader = csv.reader(fin);
        header = next(csv_reader);
        header = [str(item).strip() for item in header];
        thing_id_idx = header.index("thing_id");
        thing_ids = [int(row[thing_id_idx]) for row in csv_reader];

    thing_ids = np.unique(thing_ids);
    contexts = [grab_context(thing_id) for thing_id in thing_ids];

    # Save context
    with open("context.csv", 'w') as fout:
        fout.write("thing_id, publish_time, category, subcategory\n");
        for thing_id, cts in zip(thing_ids, contexts):
            publish_date = cts[0];
            category = cts[1];
            if publish_date is not None:
                publis_date = publish_date.isoformat();

            fout.write("{}\n".format(
                ",".join([str(thing_id), publish_date.isoformat(),
                    category[0], category[1]])));

    # Save tags
    with open("tags.csv", 'w') as fout:
        fout.write("thing_id, tag\n");
        for thing_id, cts in zip(thing_ids, contexts):
            tags = cts[2];
            for tag in tags:
                fout.write("{},{}\n".format(thing_id, tag));

if __name__ == "__main__":
    main();

