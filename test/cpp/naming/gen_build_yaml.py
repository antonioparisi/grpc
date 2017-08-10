#!/usr/bin/env python2.7
# Copyright 2015 gRPC authors.
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


"""Generates the appropriate build.json data for all the end2end tests."""


import yaml
import collections
import hashlib

def main():
  json = {
      '#': 'generated with test/cpp/naming/gen_build_json.py',
      'core_naming_end2end_tests': [
          { 'name': 'test1', 'record_type_to_resolve': 'SRV' },
          { 'name': 'test2', 'record_type_to_resolve': 'SRV' },
      ]
          #(t, END2END_TESTS[t].secure)
          #for t in END2END_TESTS.keys()
      #)
  }
  print yaml.dump(json)


if __name__ == '__main__':
  main()
