#!/bin/sh
set -e
#set -x

target_registry=${TARGET_REGISTRY:-quay.io}
target_groupname=${TARGET_GROUPNAME:-andrewrothstein}
target_name=${TARGET_NAME:-docker-ansible}

os=$1
dotver=$2
dashver=$3

. ./ansible-install-lib

write_dockerfile_$os $dotver $dashver
sudo \
    buildah \
    bud \
    -f Dockerfile.${os}_${dotver} \
    --build-arg HTTP_PROXY --build-arg HTTPS_PROXY --build-arg NO_PROXY \
    --build-arg http_proxy --build-arg https_proxy --build-arg no_proxy \
    -t ${target_registry}/${target_groupname}/${target_name}:${os}_${dotver} \
    .
