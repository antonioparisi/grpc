#!/usr/bin/env python
# Copyright 2017, Google Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.
#     * Neither the name of Google Inc. nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import subprocess
import re
import sys
import os

import python_utils.jobset as jobset
import python_utils.report_utils as report_utils

import dns_records_config

_ROOT = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), '../..'))
os.chdir(_ROOT)

def _fail_error(cmd, found, expected):
  expected_str = ''
  for e in expected:
    expected_str += ' '.join(e)
    expected_str += '\n'
  jobset.message('FAILED', '\"%s\" yielded bad record: \n  Found: \n    %s\n  Expected: \n    %s' %
    (cmd, found and ' '.join(found), expected_str))
  sys.exit(1)


def _matches_any(parsed_record, candidates):
  for e in candidates:
    if len(e) == len(parsed_record):
      matches = True
      for i in range(len(e)):
        if e[i] != parsed_record[i]:
          matches = False
      if matches:
        return True
  return False


def check_dns_record(command, expected_data):
  output = subprocess.check_output(re.split('\s+', command))
  lines = output.splitlines()

  found = None
  i = 0
  for l in lines:
    if l == ';; ANSWER SECTION:':
      found = i # re.split('\s+', lines[i + 1])
      break
    i += 1

  if found is None or len(expected_data) > len(lines) - found:
    _fail_error(command, found, expected_data)
  for l in lines[found:found+len(expected_data)]:
    parsed = re.split('\s+', lines[i + 1])
    if not _matches_any(parsed, expected_data):
      _fail_error(command, parsed, expected_data)


def sanity_check_dns_records(dns_records):
  for r in dns_records:
    cmd = 'dig %s %s' % (r.record_type, r.record_name)
    expected_data = []
    for d in r.record_data.split(','):
      expected_line = '%s %s %s %s %s' % (r.record_name, r.ttl, r.record_class, r.record_type, d)
      expected_data.append(expected_line.split(' '))

    check_dns_record(
      command=cmd,
      expected_data=expected_data)


sanity_check_dns_records(dns_records_config.DNS_RECORDS)