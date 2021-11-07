#!/bin/sh
set -e
#set -x

target_registry=${TARGET_REGISTRY:-quay.io}
target_registry2=${TARGET_REGISTRY2:ghcr.io}
target_slug=${TARGET_SLUG:-"andrewrothstein/docker-ansible"}

target_image_name="${target_registry}/${target_slug}"
target_image_name2="${target_registry2}/${target_slug}"

os=$1
dotver=$2
dashver=$3
tag_underbar="${os}_${dotver}"

fq_image_name="${target_image_name}:${tag_underbar}"
fq_image_name2="${target_image_name2}:${tag_underbar}"

. ./ansible-install-lib

write_dockerfile_$os $dotver $dashver
sudo \
    buildah \
    bud \
    -f Dockerfile.${tag_underbar} \
    --build-arg HTTP_PROXY --build-arg HTTPS_PROXY --build-arg NO_PROXY \
    --build-arg http_proxy --build-arg https_proxy --build-arg no_proxy \
    -t ${fq_image_name} \
    .
sudo \
    buildah \
      tag \
      $fq_image_name \
      $fq_image_name2