#!/usr/bin/env python
# Copyright 2017 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# This script is invoked by a Jenkins pull request job and executes all
# args passed to this script if the pull request affect C/C++ code

# Populates a DNS managed zone on DNS with records for testing

import argparse
import subprocess

import dns_records_config


argp = argparse.ArgumentParser(description='')
argp.add_argument('--dry_run', default=False, action='store_const', const=True,
                  help='Print the commands that would be ran, without running them')
argp.add_argument('--list_records', default=False, action='store_const', const=True,
                  help='Don\'t modify records and use gcloud API to print existing records')
args = argp.parse_args()

def main():
  cmds = []
  cmds.append(('gcloud dns record-sets transaction start -z=%s' % dns_records_config.ZONE_NAME).split(' '))

  for name in dns_records_config.RECORDS_BY_NAME.keys():
    type_to_data = {}
    type_to_ttl = {}
    for r in dns_records_config.RECORDS_BY_NAME[name]:
      if type_to_data.get(r.record_type) is not None:
        type_to_data[r.record_type].append(r.record_data)
      else:
        type_to_data[r.record_type] = [r.record_data]

      if type_to_ttl.get(r.record_type) is not None:
        assert type_to_ttl[r.record_type] == r.ttl
      type_to_ttl[r.record_type] = r.ttl

    for rt in type_to_data.keys():
      prefix = ('gcloud dns record-sets transaction add '
                '-z=%s --name=%s --type=%s --ttl=%s') % (dns_records_config.ZONE_NAME,
                                                         name,
                                                         rt,
                                                         type_to_ttl[rt])
      cmds.append(prefix.split(' ') + type_to_data[rt])

  cmds.append(('gcloud dns record-sets transaction describe -z=%s' % dns_records_config.ZONE_NAME).split(' '))
  cmds.append(('gcloud dns record-sets transaction execute -z=%s' % dns_records_config.ZONE_NAME).split(' '))
  cmds.append(('gcloud dns record-sets list -z=%s' % dns_records_config.ZONE_NAME).split(' '))

  if args.list_records:
    subprocess.call(('gcloud dns record-sets list -z=%s' % dns_records_config.ZONE_NAME).split(' '))
    return

  if args.dry_run:
    print('printing commands that would be run: (tokenizing may differ)')

  for c in cmds:
    if args.dry_run:
      print(' '.join(c))
    else:
      subprocess.call(c)

main()
