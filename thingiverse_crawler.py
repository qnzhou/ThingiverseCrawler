#!//usr/bin/env python

import argparse
import datetime
import requests
import re
import time

def utc_mktime(utc_tuple):
    """Returns number of seconds elapsed since epoch
    Note that no timezone are taken into consideration.
    utc tuple must be: (year, month, day, hour, minute, second)
    """

    if len(utc_tuple) == 6:
        utc_tuple += (0, 0, 0)
    return time.mktime(utc_tuple) - time.mktime((1970, 1, 1, 0, 0, 0, 0, 0, 0))

def datetime_to_timestamp(dt):
    """Converts a datetime object to UTC timestamp"""
    return int(utc_mktime(dt.timetuple()))

def parse_thing_ids(text):
    pattern = "thing:(\d{5,7})";
    matched = re.findall(pattern, text);
    return set([int(val) for val in matched]);

def parse_file_ids(text):
    pattern = "download:(\d{5,7})";
    matched = re.findall(pattern, text);
    return [int(val) for val in matched];

def crawl_thing_ids(N, end_date=None):
    """ This method extract N things that were uploaded to thingiverse.com
    before end_date.  If end_date is None, use today's date.
    """
    baseurl = "http://www.thingiverse.com/search/recent/things/page:{}?q=&start_date=&stop_date={}&search_mode=advanced&description=&username=&tags=&license=";

    end_date = datetime_to_timestamp(end_date);
    thing_ids = [];
    for i in range(N/12 + 1):
        url = baseurl.format(i, end_date);
        r = requests.get(url);
        assert(r.status_code==200);
        thing_ids += parse_thing_ids(r.text);
        if len(thing_ids) > N:
            break;

    return thing_ids[:N];

def crawl_new_things(N):
    baseurl = "http://www.thingiverse.com/newest/page:{}";
    thing_ids = [];
    for i in range(N/12 + 1):
        url = baseurl.format(i+1);
        r = requests.get(url);
        assert(r.status_code==200);
        thing_ids += parse_thing_ids(r.text);
        if len(thing_ids) > N:
            break;

    return thing_ids[:N];

def get_download_links(thing_ids):
    base_url = "http://www.thingiverse.com/{}:{}";
    file_ids = [];
    for thing_id in thing_ids:
        url = base_url.format("thing", thing_id);
        r = requests.get(url);
        assert(r.status_code == 200);
        file_ids.append(parse_file_ids(r.text));

    links = [];
    for i, thing_id in enumerate(thing_ids):
        for file_id in file_ids[i]:
            url = base_url.format("download", file_id);
            r = requests.head(url);
            link = r.headers.get("Location", None);
            if link is not None:
                links.append([thing_id, file_id, link]);

    return links;

def parse_args():
    parser = argparse.ArgumentParser(
            description="Crawl data from thingiverse",
            epilog="Written by Qingnan Zhou <qnzhou at gmail dot com>");
    #parser.add_argument("--end-date", help="e.g. 06/22/2015", default=None);
    parser.add_argument("N", type=int,
            help="how many files to crawl");
    return parser.parse_args();

def main():
    args = parse_args();

    #if args.end_date is not None:
    #    month, day, year = args.end_date.split("/");
    #    args.end_date = datetime.date(year, month, day);
    #else:
    #    args.end_date = datetime.datetime.now().date();

    #print("Crawling things uploaded before {}".format(args.end_date));
    #thing_ids = crawl_thing_ids(args.N, args.end_date);
    thing_ids = crawl_new_things(args.N);
    links = get_download_links(thing_ids);
    links = links[:args.N];

    with open("summary.csv", 'w') as fout:
        fout.write("thing_id, fild_id, link\n");
        for link in links:
            fout.write(",".join([str(val) for val in link]) + "\n");

    with open("links.txt", 'w') as fout:
        fout.write("\n".join([row[2] for row in links]));

if __name__ == "__main__":
    main();
