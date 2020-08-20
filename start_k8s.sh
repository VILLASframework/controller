#!/bin/bash

kubectl -n villas-demo port-forward svc/node 8080:80 & PF1=$!
kubectl -n villas-demo port-forward svc/broker 5672:5672 & PF2=$!

sleep 2

CONFIG="etc/config.json"

villas-ctl -c ${CONFIG} -b ${BROKER} daemon

kill $PF1 $PF2
wait $PF1 $PF2
