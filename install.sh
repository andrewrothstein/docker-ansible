#!/bin/sh
set -e
#set -x

# example: ./install.sh alpine 3.15

os=$1
os_ver=$2

. ./ansible-install-lib

#export LC_CTYPE=en_US.UTF-8
#export LANG=en_US.UTF-8

install_${os} $os_ver
