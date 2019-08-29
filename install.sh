#!/bin/sh
set -x

os=$1
dashver=$2

. ansible-install-lib

install_${os}_${dashver}
