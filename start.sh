#!/bin/bash

function exit_handler() {
	echo "Stopping port-forwards"

	kill $PF1 $PF2
	wait $PF1 $PF2
}

trap exit_handler EXIT


kubectl -n villas-demo port-forward svc/node 8080:80 & PF1=$!
kubectl -n villas-demo port-forward svc/broker 5672:5672 & PF2=$!

sleep 2

CONFIG=${CONFIG:-"etc/config.yaml"}

echo "Using config: ${CONFIG}"

villas-controller -c ${CONFIG} daemon
