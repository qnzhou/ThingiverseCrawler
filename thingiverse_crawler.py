#!//usr/bin/env python

import argparse
import datetime
import os
import os.path
import requests
import re
import time
import pymesh
from subprocess import check_call

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
    return [int(val) for val in matched];

def parse_file_ids(text):
    pattern = "download:(\d{5,7})";
    matched = re.findall(pattern, text);
    return [int(val) for val in matched];

known_licenses = [
        ("Creative Commons - Attribution",
        re.compile("http://creativecommons.org/licenses/by/\d(.\d)?/")),

        ("Creative Commons - Attribution - Share Alike",
        re.compile("http://creativecommons.org/licenses/by-sa/\d(.\d)?/")),

        ("Creative Commons - Attribution - No Derivatives",
        re.compile("http://creativecommons.org/licenses/by-nd/\d(.\d)?/")),

        ("Creative Commons - Attribution - Non-Commercial",
        re.compile("http://creativecommons.org/licenses/by-nc/\d(.\d)?/")),

        ("Attribution - Non-Commercial - Share Alike",
        re.compile("http://creativecommons.org/licenses/by-nc-sa/\d(.\d)?/")),

        ("Attribution - Non-Commercial - No Derivatives",
        re.compile("http://creativecommons.org/licenses/by-nc-nd/\d(.\d)?/")),

        ("Creative Commons - Public Domain Dedication",
        re.compile("http://creativecommons.org/publicdomain/zero/\d(.\d)?/")),

        ("GNU - GPL",
        re.compile("http://creativecommons.org/licenses/GPL/\d(.\d)?/")),

        ("GNU - LGPL",
        re.compile("http://creativecommons.org/licenses/LGPL/\d(.\d)?/")),

        ("BSD License",
        re.compile("http://creativecommons.org/licenses/BSD/")),

        ("Nokia",
        re.compile("http://www.developer.nokia.com/Terms_and_conditions/3d-printing.xhtml")),

        ("Public Domain",
        re.compile("http://creativecommons.org/licenses/publicdomain/")),
        ];

def parse_license(text):
    for name, pattern in known_licenses:
        if pattern.search(text):
            return name;
    return "unknown_license";

def crawl_thing_ids(N, end_date=None):
    """ This method extract N things that were uploaded to thingiverse.com
    before end_date.  If end_date is None, use today's date.
    """
    baseurl = "http://www.thingiverse.com/search/recent/things/page:{}?q=&start_date=&stop_date={}&search_mode=advanced&description=&username=&tags=&license=";

    end_date = datetime_to_timestamp(end_date);
    thing_ids = set();
    for i in range(N/12 + 1):
        url = baseurl.format(i, end_date);
        r = requests.get(url);
        assert(r.status_code==200);
        thing_ids.update(parse_thing_ids(r.text));
        if len(thing_ids) > N:
            break;

        # Sleep a bit to avoid being mistaken as DoS.
        time.sleep(0.5);

    return thing_ids;

def crawl_new_things(N, sleep_seconds, output_dir):
    #baseurl = "http://www.thingiverse.com/newest/page:{}";
    #baseurl = "http://www.thingiverse.com/explore/popular/page:{}";
    baseurl = "http://www.thingiverse.com/explore/featured/page:{}";
    thing_ids = set();
    file_ids = set();
    records = [];
    num_files = 0;
    page = 0;

    while True:
        url = baseurl.format(page+1);
        r = requests.get(url);
        if r.status_code != 200:
            print("failed to retrieve page {}".format(url));

        for thing_id in parse_thing_ids(r.text):
            if thing_id in thing_ids:
                continue;
            print("thing id: {}".format(thing_id))
            thing_ids.add(thing_id);
            licnese, thing_files = get_thing(thing_id, sleep_seconds);
            for file_id in thing_files:
                if file_id in file_ids:
                    continue;
                file_ids.add(file_id);
                print("  file id: {}".format(file_id));
                result = download_file(file_id, output_dir);
                if result is None: continue;
                filename, name, link = result;
                if filename is not None:
                    records.append((thing_id, file_id, filename, name, license, link));
                    if len(records) >= N:
                        return records;

        page += 1;
        # Sleep a bit to avoid being mistaken as DoS.
        time.sleep(sleep_seconds);

def get_thing(thing_id, sleep_seconds):
    base_url = "http://www.thingiverse.com/{}:{}";
    file_ids = [];

    url = base_url.format("thing", thing_id);
    r = requests.get(url);
    if r.status_code != 200:
        print("failed to retrieve thing {}".format(thing_id));
    license = parse_license(r.text);
    return license, parse_file_ids(r.text);

def get_download_link(file_id):
    base_url = "http://www.thingiverse.com/{}:{}";
    url = base_url.format("download", file_id);
    r = requests.head(url);
    link = r.headers.get("Location", None);
    if link is not None:
        __, ext = os.path.splitext(link);
        if ext.lower() not in [".stl", ".obj", ".ply", ".off"]:
            return None;
        return link;

def download_file(file_id, output_dir):
    link = get_download_link(file_id);
    if link is None:
        return None;
    name, ext = os.path.splitext(link);
    output_file = "{}{}".format(file_id, ext.lower());
    output_file = os.path.join(output_dir, output_file);
    command = "wget -q --tries=20 --waitretry 20 -O {} {}".format(output_file, link);
    #check_call(command.split());
    return output_file, name, link;

def should_keep(filename):
    return true;
    try:
        mesh = pymesh.load_mesh(filename);
        if mesh.dim != 3: return False;
        if mesh.vertex_per_face != 3: return False;
        if not mesh.is_oriented(): return False;
        if not mesh.is_closed(): return False;
        degenerated_faces = pymesh.get_degenerated_faces(mesh);
        if len(degenerated_faces) > 0: return True;
        self_intersections = pymesh.detect_self_intersection(mesh);
        if len(self_intersections) > 0: return True;
        return False;
    except:
        return False;

def parse_args():
    parser = argparse.ArgumentParser(
            description="Crawl data from thingiverse",
            epilog="Written by Qingnan Zhou <qnzhou at gmail dot com>");
    #parser.add_argument("--end-date", help="e.g. 06/22/2015", default=None);
    parser.add_argument("--sleep", type=float, default=0.0,
            help="pause between downloads in s");
    parser.add_argument("--output-dir", "-o", help="output directories",
            default=".");
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
    sleep_seconds = args.sleep;
    output_dir = args.output_dir
    records = crawl_new_things(args.N, sleep_seconds, output_dir);

    with open("summary.csv", 'w') as fout:
        fout.write("thing_id, fild_id, file, name, license, link\n");
        for entry in records:
            fout.write(",".join([str(val) for val in entry]) + "\n");

if __name__ == "__main__":
    main();
