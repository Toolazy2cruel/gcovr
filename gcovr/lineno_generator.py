# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2018 the gcovr authors
# Copyright 2013 Sandia Corporation
# This software is distributed under the BSD license.

import os
import sys
import time
import datetime
import zlib
import io
import json
from redis import StrictRedis,ConnectionError,TimeoutError
from .version import __version__
from .utils import commonpath, sort_coverage
from .coverage import FileCoverage


#
# Produce an lineno report
#

def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError

def print_lineno_report(covdata, output_file, options):
    details = options.lineno_details
    trace = options.trace
    port = options.port
    if output_file is None:
        details = False

    keys = sort_coverage(
        covdata, show_branch=False,
        by_num_uncovered=options.sort_uncovered,
        by_percent_uncovered=options.sort_percent)

    cdata_fname = {}
    for f in keys:
        filtered_fname = options.root_filter.sub('', f)
        cdata_fname[f] = filtered_fname

    cluster_source = dict()
    for f in keys:
        cdata = covdata[f]

        FILENAME = cdata_fname[f]

        currdir = os.getcwd()
        os.chdir(options.root_dir)
        with io.open(FILENAME, 'r', encoding=options.source_encoding,
                     errors='replace') as INPUT:
            flie_static = set()
            for ctr, line in enumerate(INPUT, 1):
                lineno_static = source_row(ctr, line.rstrip(), cdata.lines.get(ctr))

                if lineno_static:
                    flie_static = flie_static | lineno_static

        cluster_source[str(FILENAME)] = flie_static

    os.chdir(currdir)

    linenoOrigin = json.dumps(cluster_source,default = set_default)
    linenoString = linenoOrigin.decode('gbk')
    if output_file is None:
        sys.stdout.write(linenoString + '\n')
    else:
       with io.open(output_file, 'w', encoding=options.html_encoding,
                     errors='xmlcharrefreplace') as fh:
            fh.write(linenoString + '\n')
    if trace and port:
        try:
            redis_con = StrictRedis(host='localhost', port=int(port), db=0)
            redis_con.hset("coverage_resullt",trace,linenoOrigin)
            #redis_con.set(trace,linenoOrigin)
        except ConnectionError,TimeoutError:
            sys.stdout.write('reids case failure' + '\n')

    if not details:
        return


def source_row(lineno, source, line_cov):
    lineno_static = set()
    if line_cov and line_cov.is_covered:
        lineno_static.add(str(lineno))
    return lineno_static


