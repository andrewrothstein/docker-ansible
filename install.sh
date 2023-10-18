#!/bin/sh
set -e
#set -x

# example: ./install.sh alpine 3.15

os=$1
os_ver=$2

. ./ansible-install-lib

install_${os} $os_ver
