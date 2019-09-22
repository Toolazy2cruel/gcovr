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
from .version import __version__
from .utils import commonpath, sort_coverage
from .coverage import FileCoverage
from redis import StrictRedis,ConnectionError,TimeoutError


#
# Produce an lineno report
#

def calculate_coverage(covered, total, nan_value=0.0):
    return nan_value if total == 0 else round(100.0 * covered / total, 1)

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

    data = {}
    branchTotal = 0
    branchCovered = 0
    for key in covdata.keys():
        (total, covered, percent) = covdata[key].branch_coverage()
        branchTotal += total
        branchCovered += covered

    coverage = calculate_coverage(branchCovered, branchTotal, nan_value=None)
    data['branchs_coverage'] = '-' if coverage is None else str(coverage)

    lineTotal = 0
    lineCovered = 0
    for key in covdata.keys():
        (total, covered, percent) = covdata[key].line_coverage()
        lineTotal += total
        lineCovered += covered
    coverage = calculate_coverage(lineCovered, lineTotal)
    data['lines_coverage'] = str(coverage)

    funcTotal = 0
    funcCovered = 0
    for key in covdata.keys():
        (total, covered, percent) = covdata[key].func_coverage()
        funcTotal += total
        funcCovered += covered
    coverage = calculate_coverage(funcCovered, funcTotal, nan_value=None)
    data['functions_coverage'] = str(coverage)

    keys = sort_coverage(
        covdata, show_branch=False,
        by_num_uncovered=options.sort_uncovered,
        by_percent_uncovered=options.sort_percent)

    cdata_fname = {}
    for f in keys:
        filtered_fname = options.root_filter.sub('', f)
        cdata_fname[f] = filtered_fname


    currdir = os.getcwd()
    cluster_source, func_source = dict(), dict()
    for f in keys:
        cdata = covdata[f]
        for func_name in sorted(cdata.funcs):
            func_cov = cdata.funcs[func_name]
            if func_cov.is_covered:
                func_source[func_name] = func_cov.execute_rate

        FILENAME = cdata_fname[f]
        os.chdir(options.root_dir)
        with io.open(FILENAME, 'r', encoding=options.source_encoding,
                     errors='replace') as INPUT:
            flie_static = set()
            for ctr, line in enumerate(INPUT, 1):
                line_set, temp = set(), cdata.lines.get(ctr)
                if temp and temp.is_covered:
                    line_set.add(str(ctr))

                if line_set:
                    flie_static = flie_static | line_set

        cluster_source[str(FILENAME)] = flie_static

    os.chdir(currdir)

    data['functions_source'] = func_source
    data['clusters_source'] = cluster_source

    coverage_result = json.dumps(data,default = set_default)

    coverage_result_console = coverage_result.decode('gbk')

    if output_file is None:
        sys.stdout.write(coverage_result_console + '\n')
    else:
       with io.open(output_file, 'w', encoding=options.html_encoding,
                     errors='xmlcharrefreplace') as fh:
            fh.write(coverage_result_console + '\n')
    if trace and port:
        try:
            redis_con = StrictRedis(host='localhost', port=int(port), db=0)
            redis_con.hset("coverage_result",trace,coverage_result)
        except ConnectionError,TimeoutError:
            sys.stdout.write('reids case failure' + '\n')




