#!/bin/sh
set -e
#set -x

# example: ./install.sh alpine 3_10

os=$1
dashver=$2

. ./ansible-install-lib

install_${os}_${dashver}
