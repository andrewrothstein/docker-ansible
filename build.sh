#!/bin/sh
set -x

TARGET_REGISTRY=quay.io
TARGET_GROUPNAME=andrewrothstein
TARGET_NAME=docker-ansible

os=$1
dotver=$2
dashver=$3

printf "os: %s\n" $os
printf "dotver: %s\n" $dotver
printf "dashver: %s\n" $dashver

. ./ansible-install-lib

write_dockerfile $os $dotver $dashver
docker build \
       --build-arg HTTP_PROXY --build-arg HTTPS_PROXY --build-arg NO_PROXY \
       --build-arg http_proxy --build-arg https_proxy --build-arg no_proxy \
       -t $TARGET_REGISTRY/$TARGET_GROUPNAME/$TARGET_NAME:${os}_${dotver} \
       -f Dockerfile.${os}_${dotver} \
       .
