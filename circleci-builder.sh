#!/bin/bash
set -xe

DOCKERUSER=andrewrothstein
DOCKERCONTAINER=docker-ansible

i=0
files=()
for os in $(find . -name Dockerfile -printf '%h\n' | sed 's/^\.\///' | sort); do
    if [ $(($i % $CIRCLE_NODE_TOTAL)) -eq $CIRCLE_NODE_INDEX ]
    then
	CONTAINERNAME=$DOCKERUSER/${DOCKERCONTAINER}_$os
	docker build -t $CONTAINERNAME $os
	docker run -ti $CONTAINERNAME ansible localhost -m ping
    fi
    ((i=i+1))
done
