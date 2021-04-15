#!/bin/bash

function exit_handler() {
	echo "Stopping port-forwards"

	kill $PF1 $PF2
	wait $PF1 $PF2
}

trap exit_handler EXIT

kubectl -n villas port-forward svc/villas-relay 8081:80 & PF1=$!
kubectl -n villas port-forward svc/villas-node 8080:80 & PF1=$!
kubectl -n villas port-forward svc/villas-broker 5672:5672 & PF2=$!

sleep 2

CONFIG=${CONFIG:-"etc/config.yaml"}

echo "Using config: ${CONFIG}"

villas-controller -c ${CONFIG} daemon
