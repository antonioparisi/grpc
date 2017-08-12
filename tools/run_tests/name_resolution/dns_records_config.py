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

# Source of truth for DNS records used in testing on GCE

ZONE_DNS = 'test.grpctestingexp.'
ZONE_NAME = 'exp-grpc-testing'
TTL = '2100'

SRV_PORT='1234'


class DnsRecord(object):
  def __init__(self, record_type, record_name, record_data):
    self.record_type = record_type
    self.record_name = record_name
    self.record_data = record_data
    self.record_class = 'IN'
    self.ttl = TTL

  def uploadable_data(self):
    return self.record_data.split(',')

def _create_records_for_testing():
  with open('tools/run_tests/name_resolution/resolver_test_record_groups.yaml', 'r') as config:
    test_groups = yaml.load(config)
  all_records = []
  for group in test_groups:
    for name in group['records'].keys():
      for record in group['records'][name]:
        assert(len(record.keys()) == 1)
        r_type = record.keys()[0]
        r_data = record[r_type]
        print('record Name is |%s|' % name)
        print('R_type is |%s|' % r_type)
        print('R_data is |%s|' % r_data)
        all_records.append(DnsRecord(r_type, name, r_data))
  return records

def srv_record_target_name(srv_record):
  # extract host from "priority weight port host" srv data
  return srv_record.record_data.split(' ')[3]

def srv_record_target_port(srv_record):
  # extract port from "priority weight port host" srv data
  return srv_record.record_data.split(' ')[2]

def a_record_target_ip(ip_record_name, dns_records):
  for r in dns_records:
    if r.record_name == ip_record_name:
      return r.record_data
  raise(Exception('no A/AAAA record found for target of srv record: %s' % srv_record.record_name))

def a_record_type(ip_record_name, dns_records):
  for r in dns_records:
    if r.record_name == ip_record_name:
      return r.record_type
  raise(Exception('no A/AAAA record found matching: %s' % ip_record_name))

def expected_result_for_a_record(a_record, expected_port=443):
  with_ports = []
  for ip in a_record.record_data.split(','):
    if a_record.record_type == 'A':
      with_ports.append('%s:%s' % (ip, expected_port))
    else:
      assert a_record.record_type == 'AAAA'
      with_ports.append('[%s]:%s' % (ip, expected_port))

  return ','.join(with_ports)

def expected_result_for_srv_record(srv_record, dns_records):
  srv_target_name = srv_record_target_name(srv_record)
  srv_target_port = srv_record_target_port(srv_record)

  for r in dns_records:
    if r.record_name == srv_target_name:
      return expected_result_for_a_record(r,
                                          expected_port=srv_target_port)
  raise Exception('target %s for srv record %s not found' %
    (srv_record_target_name, srv_record.record_name))

DNS_RECORDS = _create_records_for_testing()