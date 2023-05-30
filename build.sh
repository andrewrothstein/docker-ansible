#!/bin/sh
set -e
#set -x

target_registry=${TARGET_REGISTRY:-quay.io}
target_registry2=${TARGET_REGISTRY2:-ghcr.io}
target_slug=${TARGET_SLUG:-"andrewrothstein/docker-ansible"}

target_image_name="${target_registry}/${target_slug}"
target_image_name2="${target_registry2}/${target_slug}"

os=$1
os_ver=$2
tag_underbar="${os}_${os_ver}"

fq_image_name="${target_image_name}:${tag_underbar}"
fq_image_name2="${target_image_name2}:${tag_underbar}"

docker build \
       --build-arg "OS=${os}" \
       --build-arg "OS_VER=${os_ver}" \
       -t $fq_image_name \
       -t $fq_image_name2 \
       -f Dockerfile \
       .
