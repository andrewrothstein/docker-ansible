#!/bin/bash
set -xe

DOCKERUSER=andrewrothstein
DOCKERCONTAINER=docker-ansible

i=0
files=()
for os in $(find . -name Dockeffile -printf '%h\n' | sort); do
    if [ $(($i % $CIRCLE_NODE_TOTAL)) -eq $CIRCLE_NODE_INDEX ]
    then
	docker build -t $DOCKERUSER/$DOCKERCONTAINER $os
    fi
    ((i=i+1))
done
