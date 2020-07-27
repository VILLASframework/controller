#!/bin/bash

kubectl -n villas-demo port-forward svc/node 8080:80 > /dev/null & PF1=$!
kubectl -n villas-demo port-forward svc/broker 5672:5672 > /dev/null & PF2=$!

CONFIG="/villas/demo/etc/villas/controller/config.json"
BROKER="amqp://admin:Haegiethu0rohtee@host.docker.internal/%2F"

COMMAND="villas-ctl -c ${CONFIG} -b ${BROKER} daemon"

cat << EOF > setup.sh
#!/bin/sh

pip3 uninstall --yes villas-controller
pushd /villas/controller
python3 setup.py develop
popd

pip3 uninstall --yes villas-node
pushd /villas/node/python
python3 setup.py develop
popd
EOF

cat << EOF > start.sh
#!/bin/sh

${COMMAND}
EOF

sleep 2

DOCKER_OPTS="-w /villas/controller -tiv /Users/stv0g_local/workspace/rwth/acs/public/villas:/villas"

IMAGE="registry.git.rwth-aachen.de/acs/public/villas/controller:demo-v0.1"

docker run ${DOCKER_OPTS} ${IMAGE}

kill $PF1 $PF2
wait $PF1 $PF2
