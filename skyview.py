#!/usr/bin/python3
"""
skyview.py

Command line utility for processing skyview user logs. Instead of uploading the
entire file, allows a part of the file delimited by a start date and an end
date to be uploaded to www.saavyanalysis.com
"""

import argparse
from collections import defaultdict
import datetime
import getpass
import logging
logging.basicConfig(level=logging.DEBUG)
import re
import subprocess
import sys


def create_parser():
    parser = argparse.ArgumentParser(description='Process skyview user logs')
    subparsers = parser.add_subparsers(help="commands")

    showdates_parser = subparsers.add_parser(
        "showdates",
        help="Show distinct flight dates in file")
    filter_parser = subparsers.add_parser(
        "filter",
        help="Filter the file by dates",
        description='e.g. skyview.py filter sample.csv --start 2017-01-29 --end 2017-02-01 --outfile test.csv')
    upload_parser = subparsers.add_parser(
        "upload",
        help="Upload the file to savvyanalysis.",
        description='e.g. skyview.py upload out.csv username 3434')

    showdates_parser.set_defaults(cmd='showdates')
    showdates_parser.add_argument('infile', type=argparse.FileType('r'),
                                  help="skyview logfile in csv format")

    filter_parser.set_defaults(cmd='filter')
    filter_parser.add_argument('infile', type=argparse.FileType('r'),
                               help="skyview logfile in csv format")
    filter_parser.add_argument('--outfile', type=argparse.FileType('w'),
                               default=sys.stdout,
                               help="output file")
    filter_parser.add_argument('--start', metavar="START_DATE_TIME",
                               help='specify start date (and optionally time).'
                               ' e.g. --start "2017-01-28 20:04:34" or "2017-01-28"')
    filter_parser.add_argument('--end', metavar="END_DATE_TIME",
                               help="specify end date (and optionally time). same as start")

    upload_parser.set_defaults(cmd='upload')
    upload_parser.add_argument('uploadfile',
                               help="file to upload to savvyanalysis.")
    upload_parser.add_argument('username',
                               help="username at savvyanalysis. you will be prompted for password.")
    upload_parser.add_argument('aircraft_id',
                               help="aircraft_id at savvyanalysis")
    return parser

def check_infile():
    file = args.infile
    headerline = file.readline()
    headers = headerline.split(',')
    assert headers[0] == 'Session Time', "Input file is missing 'Session Time' as first header item."
    return headers

def start_end_file_generator():
    if 'start' in args and args.start:
        state = "look for start"
    elif 'end' in args and args.end:
        state = "look for end"
    else:
        state = "process file"
    for line in args.infile:
        if state == "process file":
            yield line
        else:
            fields = line.split(',', maxsplit=4)
            linedate = fields[3]
            if state == "look for start" and linedate.startswith(args.start):
                if args.end:
                    state = "look for end"
                else:
                    state = "process file"
                    yield line
            elif state == "look for end":
                if linedate.startswith(args.end):
                    return
                else:
                    yield line    
                    
def cmd_showdates():
    block = defaultdict(int)
    blocks = []
    for line in start_end_file_generator():
        fields = line.split(',', maxsplit=4)
        sessiontime = float(fields[0])
        linedate = fields[3]
        if linedate:
            if block['endsession']:
                if sessiontime < block['endsession']:
                    blocks.append(block)
                    block = defaultdict(int)
                else:
                    block['end'] = linedate
                    block['endsession'] = sessiontime
            else:
                block['endsession'] = sessiontime
                block['startsession'] = sessiontime
                block['start'] = linedate
    else:
        blocks.append(block)
    if len(blocks):
        print("Found %d dates:" % (len(blocks)))
        print("Number. [StartSession--EndSession] [StartDateTime--EndDateTime] Duration")
        for i, block in enumerate(blocks):
            start = datetime.datetime.strptime(block['start'], "%Y-%m-%d %H:%M:%S")
            end = datetime.datetime.strptime(block['end'], "%Y-%m-%d %H:%M:%S")
            print("%2d. [%8.2f--%8.2f] [%s--%s] %s" % 
                  (i+1, block['startsession'], block['endsession'], block['start'], block['end'],
                   end-start))
    else:
        print("No dates found.")

                    
def cmd_filter():
    for line in start_end_file_generator():
        args.outfile.write(line)


def cmd_upload():
    username = args.username
    password = getpass.getpass()
    csrftoken = ''
    logging.debug("%s : %s" % (username, password))
    output = subprocess.check_output("http -v --verify=no --session=skyview GET https://www.savvyanalysis.com/login",
                                     shell=True)
    m = re.search(b'csrftoken=(\w+)', output)
    if not m:
        logging.error("Error obtaining csrftoken")
        exit()

    csrftoken = m.group(1).decode("utf-8")

    output = subprocess.check_output("http -v --verify=no --session=skyview --form POST https://www.savvyanalysis.com/login "
                                     "username=%s password=%s csrfmiddlewaretoken=%s Referer:https://www.savvyanalysis.com/login" %
                                     (username, password, csrftoken), shell=True)
    if not re.search(b'HTTP\/\d\.\d 302 Found', output):
        logging.error("Error logging in to savvyanalysis with given credentials '%s'" % (username))
        exit()
    logging.debug("logged in successfully")

    output = subprocess.check_output('http -v --session=test --form POST https://www.savvyanalysis.com/upload_files/%s '
                                     'name="test1" aircraft_id="%s" file@%s' %
                                     (args.aircraft_id, args.aircraft_id, args.uploadfile), shell=True)
    if not re.search(b'HTTP/\d\.\d 200 OK', output):
        logging.error("Unknown error uploading file.")
        exit()

    print("File was uploaded successfully.")
    

#MAIN
if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    if hasattr(args, 'cmd') is False:
        parser.print_help()
    elif args.cmd == "showdates":
        check_infile()
        cmd_showdates()
    elif args.cmd == "filter":
        headers = check_infile()
        args.outfile.write(','.join(headers))
        cmd_filter()
    elif args.cmd == "upload":
        cmd_upload()
    else:
        exit()

