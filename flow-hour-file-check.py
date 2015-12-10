#!/usr/bin/env python

# author: Chuck King
# https://github.com/cwkingjr/silk-hour-file-check
# license: GPLv3, see license file
# purpose: Ensure silk sensor is generating data
# note: must run on python 2.4

from __future__ import print_function
from datetime import datetime, timedelta
import optparse
import os
from string import Template # real format functionality came in 2.6
import sys

# Silk allows systems to be configured with variations of the data path layout
# Below format is one option. If you use something different, you'll
# need to rearrange the format keywords to match your configuration layout.
# silkformat = '/${sclass}/${stype}/${year}/${month}/${day}/${stype}-${sensor}_${year}${month}${day}.${hour}'
silkformat = '/${sclass}/${stype}/${year}/${month}/${day}/${stype}-${sensor}_${year}${month}${day}.${hour}'

#--- keep out 

datadir = "/data"

# dev machine uses non-standard format, so swap in for testing when running on dev machine
if os.uname()[1] == 'ub1404':
    silkformat = '/${stype}/${year}/${month}/${day}/${stype}-${sensor}_${year}${month}${day}.${hour}'

def process_options():
    usage = "usage: %prog [options]"
    parser = optparse.OptionParser(usage)
    parser.add_option("-c",
                      "--silk-class",
                      dest="silkclass",
                      help="Silk class name you want to check.")
    parser.add_option("-o",
                      "--offset-hours",
                      dest="offset",
                      help="Optional. Offset of hours prior to invoked datetime hour. "
                      "Default is 0 (check for data in hour file one hour ago)."
                      "Must be an integer between 1-100. Allows for collection processing delay.")
    parser.add_option("-p",
                      "--silk-data-dir",
                      dest="silkdata",
                      help="Optional. Silk data parent directory. Default is /data).")
    parser.add_option("-s",
                      "--sensor-file",
                      dest="sensors",
                      help="Path to file with sensor listing, one sensor name per line.")
    parser.add_option("-t",
                      "--silk-types",
                      dest="silktypes",
                      help="Comma-separated list of silk types you want to check."
                      "Default is 'in,inweb,out,outweb'")

    (options,args) = parser.parse_args()
    return (options,args)

(options, args) = process_options()

if options.silkdata:
    datadir = options.silkdata.rstrip('/')

if not os.path.isdir(datadir):
    print("ERROR: Silk data dir '%s' does not exist" % datadir) 
    sys.exit(1)
    
# add the data path starting point to the silkdataformat string
silkformat = "%s%s" % (datadir, silkformat)

if not options.silkclass:
    print("ERROR: Silk Class argument required. See -h") 
    sys.exit(1)

if options.offset:
    msg = "ERROR: Offset hours must be an integer between 1-100" 
    try:
        options.offset = int(options.offset)
    except:
        print(msg) 
        sys.exit(1)
    if not 1 <= options.offset <= 100:
        print(msg) 
        sys.exit(1)

if not options.sensors:
    print("ERROR: Sensor file path required. See -h") 
    sys.exit(1)
else:
    if not os.path.isfile(options.sensors):
        print("ERROR: Sensor file path provided is not a file: %s" % options.sensors) 
        sys.exit(1)
    sensors = []
    with open(options.sensors, 'r') as f:
        for line in f.readlines():
            line = line.strip()
            if line == '' or line.startswith('#'):
                continue
            sensors.append(line) 
    sensors.sort()
    
if not options.silktypes:
    silktypes = ['in','inweb','out','outweb']
else:
    if ',' in options.silktypes:
        # process list of stypes
        silktypes = [t.strip() for t in options.silktypes.split(',')]
    else:
        # process single stype
        silktypes = []
        silktypes.append(options.silktypes.strip())
    silktypes.sort()

# generate current date time info
dt = datetime.now()
if options.offset:
    dt = dt - timedelta(hours=options.offset)

# grab the datetime parts we need
year  = dt.strftime('%Y')
month = dt.strftime('%m')
day   = dt.strftime('%d')
hour  = dt.strftime('%H')

# load the string format into a template
tmpl = Template(silkformat)

for sensor in sensors:
    for stype in silktypes:
        myfile = tmpl.substitute(sclass=options.silkclass, stype=stype,
                 year=year, month=month, day=day, sensor=sensor, hour=hour)
        if not os.path.isfile(myfile):
            print("Sensor %s missing file %s" % (sensor, myfile))
            continue
        # check for file size
        stat = os.stat(myfile)
        if stat.st_size < 1:
            print("Sensor %s file %s has zero bytes" % (sensor, myfile))
