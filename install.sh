#!/bin/sh
set -x

# example: ./install.sh alpine 3_10

os=$1
dashver=$2

source ./ansible-install-lib

install_${os}_${dashver}
