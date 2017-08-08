#!/bin/bash
#
# template generated by genshtest
python tools/run_tests/python_utils/dns_server.py &
sleep 0.5
pid=$(sudo netstat -tulpn | grep 15353 | awk '{ print $6 }' | cut -d'/' -f1)

dig $@ -p 15353 @localhost

kill $pid
sleep 1.1
if [[ $(sudo netstat -tulpn | grep 15353 | wc -l) != 0 ]]; then
  echo "server not killed!"
fi
