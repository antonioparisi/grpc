import json
import yaml

class DnsRecord(object):
  def __init__(self, record_type, record_name, record_data):
    self.record_type = record_type
    self.record_name = record_name
    self.record_data = record_data
    self.record_class = 'IN'
    self.ttl = TTL

  def uploadable_data(self):
    return self.record_data.split(',')

ZONE_DNS = 'grpc.com.'
SRV_PORT = '1234'

def a_record(ip):
  return {
      'A': ip,
  }

def aaaa_record(ip):
  return {
      'AAAA': ip,
  }

def srv_record(target):
  return {
      'SRV': '0 0 %s %s' % (SRV_PORT, target),
  }

def txt_record(grpc_config):
  return {
      'TXT': 'grpc_config=%s' % json.dumps(grpc_config, separators=(',', ':')),
  }

def _test_group(record_to_resolve, records, expected_addrs, expected_config):
  return {
      'record_to_resolve': record_to_resolve,
      'records': records,
      'expected_addrs': expected_addrs,
      'expected_config_index': expected_config,
  }

def _full_srv_record_name(name):
  return '_grpclb._tcp.srv-%s.%s' % (name, ZONE_DNS)

def _full_a_record_name(name):
  return '%s.%s' % (name, ZONE_DNS)

def _full_txt_record_name(name):
  return '%s.%s' % (name, ZONE_DNS)

def push(records, name, val):
  if name in records.keys():
    records[name].append(val)
    return
  records[name] = [val]

def _create_ipv4_and_srv_record_group(ip_name, ip_addrs):
  records = {}
  for ip in ip_addrs:
    push(records, _full_a_record_name(ip_name), a_record(ip))
  push(records, _full_srv_record_name(ip_name), srv_record(ip_name))

  expected_addrs = []
  for ip in ip_addrs:
    expected_addrs.append('%s:%s' % (ip, SRV_PORT))
  return _test_group('%s.%s' % (ip_name, ZONE_DNS), records, expected_addrs, None)

def _create_ipv6_and_srv_record_group(ip_name, ip_addrs):
  records = {}
  for ip in ip_addrs:
    push(records, _full_a_record_name(ip_name), aaaa_record(ip))
  push(records, _full_srv_record_name(ip_name), srv_record(ip_name))

  expected_addrs = []
  for ip in ip_addrs:
    expected_addrs.append('[%s]:%s' % (ip, SRV_PORT))
  return _test_group('%s.%s' % (ip_name, ZONE_DNS), records, expected_addrs, None)

def _create_ipv4_and_srv_and_txt_record_group(ip_name, ip_addrs, grpc_config, expected_config):
  records = {}
  for ip in ip_addrs:
    push(records, _full_a_record_name(ip_name), a_record(ip))
  push(records, _full_srv_record_name(ip_name), srv_record(ip_addrs))
  push(records, _full_txt_record_name(ip_name), txt_record(grpc_config))

  expected_addrs = []
  for ip in ip_addrs:
    expected_addrs.append('%s:443' % ip)
  return _test_group('srv-%s.%s' % (ip_name, ZONE_DNS), records, expected_addrs, expected_config)

def _create_ipv4_and_txt_record_group(ip_name, ip_addrs, grpc_config, expected_config):
  records = {}
  for ip in ip_addrs:
    push(records, _full_a_record_name(ip_name), aaaa_record(ip))
  push(records, _full_txt_record_name(ip_name), txt_record(grpc_config))

  expected_addrs = []
  for ip in ip_addrs:
    expected_addrs.append('%s:443' % ip)
  return _test_group('%s.%s' % (ip_name, ZONE_DNS), records, expected_addrs, expected_config)

def _create_method_config(service_name):
  return [{
    'name': [{
      'service': service_name,
      'method': 'Foo',
      'waitForReady': True,
    }],
  }]

def _create_service_config(method_config=[], percentage=None, client_language=None):
  config = {
    'loadBalancingPolicy': 'round_robin',
    'methodConfig': method_config,
  }
  if percentage is not None:
    config['percentage'] = percentage
  if client_language is not None:
    config['clientLanguage'] = client_language

  return config

def _create_records_for_testing():
  records = []
  records.append(_create_ipv4_and_srv_record_group('ipv4-single-target', ['1.2.3.4']))
  records.append(_create_ipv4_and_srv_record_group('ipv4-multi-target', ['1.2.3.5',
                                                                         '1.2.3.6',
                                                                         '1.2.3.7']))
  records.append(_create_ipv6_and_srv_record_group('ipv6-single-target', ['2607:f8b0:400a:801::1001']))
  records.append(_create_ipv6_and_srv_record_group('ipv6-multi-target', ['2607:f8b0:400a:801::1002',
                                                                         '2607:f8b0:400a:801::1003',
                                                                         '2607:f8b0:400a:801::1004']))

  records.append(_create_ipv4_and_srv_and_txt_record_group('ipv4-simple-service-config', ['1.2.3.4'],
                                                           [_create_service_config(_create_method_config('SimpleService'))],
                                                           0))

  records.append(_create_ipv4_and_txt_record_group('ipv4-no-srv-simple-service-config', ['1.2.3.4'],
                                                   [_create_service_config(_create_method_config('NoSrvSimpleService'))],
                                                   0))

  records.append(_create_ipv4_and_txt_record_group('ipv4-second-language-is-cpp', ['1.2.3.4'],
                                                   [_create_service_config(
                                                     _create_method_config('GoService'),
                                                     client_language=['go']),
                                                    _create_service_config(
                                                      _create_method_config('CppService'),
                                                      client_language=['c++'])],
                                                   None))

  records.append(_create_ipv4_and_txt_record_group('ipv4-no-config-for-cpp', ['1.2.3.4'],
                                                   [_create_service_config(
                                                     _create_method_config('PythonService'),
                                                     client_language=['python'])],
                                                   None))

  records.append(_create_ipv4_and_txt_record_group('ipv4-config-with-percentages', ['1.2.3.4'],
                                                   [_create_service_config(
                                                      _create_method_config('NeverPickedService'),
                                                      percentage=0),
                                                    _create_service_config(
                                                      _create_method_config('AlwaysPickedService'),
                                                      percentage=100)],
                                                   1))

  records.append(_create_ipv4_and_txt_record_group('ipv4-cpp-config-has-zero-percentage', ['1.2.3.4'],
                                                   [_create_service_config(
                                                      _create_method_config('CppService'),
                                                      percentage=0)],
                                                   None))

  return records

test_groups = _create_records_for_testing()
#for group in test_groups:
#  print json.dumps(group)
  #if record_to_resolve in ['A', 'AAAA']:
    # make test based on name of record to resolve, expected IP addr(s) with
    # ports, and expected service config, if any
  #if record_to_resolve == 'SRV':
    # make test based on name of record to resolve, expected IP addr(s) with
    # ports, and expected service config, if any

#print ========

print(yaml.dump(test_groups))
