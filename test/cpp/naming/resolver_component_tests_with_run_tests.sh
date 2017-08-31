#!/bin/bash
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

# This file is auto-generated

set -ex

# change to grpc repo root
cd $(dirname $0)/../../..

# if we're using run_tests.py, then rely on the invoker of this
# shell script to tell where the other binaries are
RESOLVER_TEST_BINPATH="$1"
PICK_PORT_BINPATH="$2"
INVOKE_DNS_SERVER_CMD_WITHOUT_ARGS="python test/cpp/naming/dns_server.py"

DNS_PORT=`$PICK_PORT_BINPATH | grep "Got port" | awk '{print $3}'`
echo "dns port is $DNS_PORT"
if [[ $DNS_PORT == 0 ]]; then echo "failed to get port" && exit 1; fi

if [[ "$GRPC_DNS_RESOLVER" != "" && "$GRPC_DNS_RESOLVER" != ares ]]; then
  echo "This test only works under GRPC_DNS_RESOLVER=ares. Have GRPC_DNS_RESOLVER=$GRPC_DNS_RESOLVER" && exit 1
fi
export GRPC_DNS_RESOLVER=ares

echo "Start a local DNS server in the background on port $DNS_PORT"
$INVOKE_DNS_SERVER_CMD_WITHOUT_ARGS --dns_port="$DNS_PORT" 2>&1 > /dev/null &
DNS_SERVER_PID=$!
echo "Local DNS server started. PID: $DNS_SERVER_PID"

# Health check local DNS server TCP and UDP ports
for ((i=0;i<30;i++));
do
  echo "Retry health-check DNS query to local DNS server over tcp and udp"
  RETRY=0
  dig A health-check-local-dns-server-is-alive.resolver-tests.grpctestingexp. @localhost -p $DNS_PORT +tries=1 +timeout=1 | grep '123.123.123.123' || RETRY=1
  dig A health-check-local-dns-server-is-alive.resolver-tests.grpctestingexp. @localhost -p $DNS_PORT +tries=1 +timeout=1 +tcp | grep '123.123.123.123' || RETRY=1
  if [[ $RETRY == 0 ]]; then
    break
  fi;
  sleep 0.1
done

if [[ $RETRY == 1 ]]; then
  echo "FAILED TO START LOCAL DNS SERVER"
  kill -SIGTERM $DNS_SERVER_PID
  wait
  exit 1
fi

function terminate_all {
  kill -SIGTERM $!
  kill -SIGTERM $DNS_SERVER_PID
  wait
  exit 1
}

trap terminate_all SIGTERM
EXIT_CODE=0

$RESOLVER_TEST_BINPATH \
  --target_name='srv-ipv4-single-target.resolver-tests.grpctestingexp.' \
  --expected_addrs='1.2.3.4:1234,True' \
  --expected_chosen_service_config='' \
  --expected_lb_policy='' \
  --local_dns_server_address=127.0.0.1:$DNS_PORT &
wait $! || EXIT_CODE=1

$RESOLVER_TEST_BINPATH \
  --target_name='srv-ipv4-multi-target.resolver-tests.grpctestingexp.' \
  --expected_addrs='1.2.3.5:1234,True;1.2.3.6:1234,True;1.2.3.7:1234,True' \
  --expected_chosen_service_config='' \
  --expected_lb_policy='' \
  --local_dns_server_address=127.0.0.1:$DNS_PORT &
wait $! || EXIT_CODE=1

$RESOLVER_TEST_BINPATH \
  --target_name='srv-ipv6-single-target.resolver-tests.grpctestingexp.' \
  --expected_addrs='[2607:f8b0:400a:801::1001]:1234,True' \
  --expected_chosen_service_config='' \
  --expected_lb_policy='' \
  --local_dns_server_address=127.0.0.1:$DNS_PORT &
wait $! || EXIT_CODE=1

$RESOLVER_TEST_BINPATH \
  --target_name='srv-ipv6-multi-target.resolver-tests.grpctestingexp.' \
  --expected_addrs='[2607:f8b0:400a:801::1002]:1234,True;[2607:f8b0:400a:801::1003]:1234,True;[2607:f8b0:400a:801::1004]:1234,True' \
  --expected_chosen_service_config='' \
  --expected_lb_policy='' \
  --local_dns_server_address=127.0.0.1:$DNS_PORT &
wait $! || EXIT_CODE=1

$RESOLVER_TEST_BINPATH \
  --target_name='srv-ipv4-simple-service-config.resolver-tests.grpctestingexp.' \
  --expected_addrs='1.2.3.4:1234,True' \
  --expected_chosen_service_config='{"loadBalancingPolicy":"round_robin","methodConfig":[{"name":[{"method":"Foo","service":"SimpleService","waitForReady":true}]}]}' \
  --expected_lb_policy='round_robin' \
  --local_dns_server_address=127.0.0.1:$DNS_PORT &
wait $! || EXIT_CODE=1

$RESOLVER_TEST_BINPATH \
  --target_name='ipv4-no-srv-simple-service-config.resolver-tests.grpctestingexp.' \
  --expected_addrs='1.2.3.4:443,False' \
  --expected_chosen_service_config='{"loadBalancingPolicy":"round_robin","methodConfig":[{"name":[{"method":"Foo","service":"NoSrvSimpleService","waitForReady":true}]}]}' \
  --expected_lb_policy='round_robin' \
  --local_dns_server_address=127.0.0.1:$DNS_PORT &
wait $! || EXIT_CODE=1

$RESOLVER_TEST_BINPATH \
  --target_name='ipv4-no-config-for-cpp.resolver-tests.grpctestingexp.' \
  --expected_addrs='1.2.3.4:443,False' \
  --expected_chosen_service_config='' \
  --expected_lb_policy='' \
  --local_dns_server_address=127.0.0.1:$DNS_PORT &
wait $! || EXIT_CODE=1

$RESOLVER_TEST_BINPATH \
  --target_name='ipv4-cpp-config-has-zero-percentage.resolver-tests.grpctestingexp.' \
  --expected_addrs='1.2.3.4:443,False' \
  --expected_chosen_service_config='' \
  --expected_lb_policy='' \
  --local_dns_server_address=127.0.0.1:$DNS_PORT &
wait $! || EXIT_CODE=1

$RESOLVER_TEST_BINPATH \
  --target_name='ipv4-second-language-is-cpp.resolver-tests.grpctestingexp.' \
  --expected_addrs='1.2.3.4:443,False' \
  --expected_chosen_service_config='{"loadBalancingPolicy":"round_robin","methodConfig":[{"name":[{"method":"Foo","service":"CppService","waitForReady":true}]}]}' \
  --expected_lb_policy='round_robin' \
  --local_dns_server_address=127.0.0.1:$DNS_PORT &
wait $! || EXIT_CODE=1

$RESOLVER_TEST_BINPATH \
  --target_name='ipv4-config-with-percentages.resolver-tests.grpctestingexp.' \
  --expected_addrs='1.2.3.4:443,False' \
  --expected_chosen_service_config='{"loadBalancingPolicy":"round_robin","methodConfig":[{"name":[{"method":"Foo","service":"AlwaysPickedService","waitForReady":true}]}]}' \
  --expected_lb_policy='round_robin' \
  --local_dns_server_address=127.0.0.1:$DNS_PORT &
wait $! || EXIT_CODE=1

$RESOLVER_TEST_BINPATH \
  --target_name='srv-ipv4-target-has-backend-and-balancer.resolver-tests.grpctestingexp.' \
  --expected_addrs='1.2.3.4:1234,True;1.2.3.4:443,False' \
  --expected_chosen_service_config='' \
  --expected_lb_policy='' \
  --local_dns_server_address=127.0.0.1:$DNS_PORT &
wait $! || EXIT_CODE=1

$RESOLVER_TEST_BINPATH \
  --target_name='srv-ipv6-target-has-backend-and-balancer.resolver-tests.grpctestingexp.' \
  --expected_addrs='[2607:f8b0:400a:801::1002]:1234,True;[2607:f8b0:400a:801::1002]:443,False' \
  --expected_chosen_service_config='' \
  --expected_lb_policy='' \
  --local_dns_server_address=127.0.0.1:$DNS_PORT &
wait $! || EXIT_CODE=1

kill -SIGTERM $DNS_SERVER_PID
wait
# Give the port back to the port server
curl "localhost:32766/drop/$DNS_PORT"
exit $EXIT_CODE