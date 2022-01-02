#!/bin/sh
set -e
#set -x

target_registry=${TARGET_REGISTRY:-quay.io}
target_registry2=${TARGET_REGISTRY2:-ghcr.io}
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
buildah_build_and_tag Dockerfile.${tag_underbar} ${fq_image_name} ${fq_image_name2}
#docker_build_and_tag Dockerfile.${tag_underbar} ${fq_image_name} ${fq_image_name2}
