#!/usr/bin/env python2.7

# Gathers a small set of (system resource) facts for all registered hosts within a Satellite 6 setup that match 'foobar' for value hostname.

import csv
import json
import urllib2
import urllib
import datetime
import base64
import sys
import ast
import re
import math
from base64 import b64encode

## Credentials and constants

login = 'xxxxxxx'
password = 'xxxxxxx'
satellite = 'xxxxxxx'
url = 'https://' + satellite + '/api/v2/hosts'


## Convert bytes to GB for storage

def convert_size_storage(size_bytes):
    if size_bytes == 0:
        return 0
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)

    return '%s' % s


## Convert bytes to GB for mem

def convert_size_mem(size_bytes):
    if size_bytes == 0:
        return 0

    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)

    if int(round(s)) == 126:
        s = 128
    if int(round(s)) % 2 == 1:
        s = s + 1

    return '%s' % s


## Determine how many hosts match the given search criteria

def get_host_count():

    _url = 'https://' + satellite \
        + '/api/v2/hosts?search=foobar&per_page=1'
    request = urllib2.Request(_url)
    base64string = base64.encodestring('%s:%s' % (login,
            password)).strip()
    request.add_header('Authorization', 'Basic %s' % base64string)
    result = urllib2.urlopen(request)
    jsonresult = json.load(result)

  # # Check if its possible to connect with the Satellite API

    if jsonresult['total']:
        host_count = jsonresult['total']
    else:
        print 'Could not connect to api'
        sys.exit(1)

  # # Return total matching hosts

    return int(host_count)


## Debug print

print str('HOSTNAME,MEM,CPU,STORAGE')


## For each host return matching facts

def get_resource_facts(hostname):

    _url2 = 'https://' + satellite + '/api/v2/hosts/' + hostname \
        + '/facts?per_page=700'
    request = urllib2.Request(_url2)
    base64string = base64.encodestring('%s:%s' % (login,
            password)).strip()
    request.add_header('Authorization', 'Basic %s' % base64string)
    result = urllib2.urlopen(request)
    jsonresult = json.load(result)

    host = hostname

     # # Check if its possible to connect with the Satellite API

    if jsonresult['results']:
        mesg = 'OK'
    else:
        mesg = 'ERR'
        resource_facts_err = '%s,%s,%s,%s' % (host, mesg, mesg, mesg)
        return resource_facts_err

    try:
        mem = \
            int(round(float(convert_size_mem(float(jsonresult['results'
                ][hostname]['memorysize_mb'])))))
    except KeyError, error:
        mem = \
            int(round(float(convert_size_mem(float(jsonresult['results'
                ][hostname]['memory::memtotal'])))))
    except KeyError, error:
        mem = 'ERR'

    try:
        cpu = int(jsonresult['results'][hostname]['processorcount'])
    except KeyError, error:
        cpu = int(jsonresult['results'][hostname]['cpu::cpu(s)'])
    except KeyError, error:
        cpu = 'ERR'

    disk_sizes = 0

    try:
        for facts in jsonresult['results'][hostname]:
            if 'blockdevice_' in facts:
                if '_size' in facts:
                    disk_size = jsonresult['results'][hostname][facts]
                    disk_sizes += \
                        float(convert_size_storage(float(disk_size)))

        disk = int(disk_sizes)
    except KeyError, error:
        disk = 'ERR'

    resource_facts = '%s,%s,%s,%s' % (host, mem, cpu, disk)
    return resource_facts


## Print hostname with resource_facts

def get_host_list(host_count):

    pages = host_count / 10

    pagenr = 0
    while pagenr != pages:

        pagenr += 1

        _url = 'https://' + satellite \
            + '/api/v2/hosts?search=foobar&per_page=10&page=' \
            + str(pagenr)
        request = urllib2.Request(_url)
        base64string = base64.encodestring('%s:%s' % (login,
                password)).strip()
        request.add_header('Authorization', 'Basic %s' % base64string)
        result = urllib2.urlopen(request)
        jsonresult = json.load(result)

        i = 0
        while i != int(jsonresult['per_page']):

            try:
                hostname = jsonresult['results'][i]['certname']
            except KeyError, error:
                hostname = jsonresult['results'][i]['hostname']
            except KeyError, error:
                hostname = jsonresult['results'][i]['host']

            result = str(get_resource_facts(hostname)).encode('utf-8'
                    ).strip("('')")

            print result

            i += 1


# Main function

get_host_list(get_host_count())
sys.exit(0)
