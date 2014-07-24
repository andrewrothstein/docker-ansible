docker-ansible
==============

Ubuntu container with ansible installed

build :
docker build -t andrewrothstein/docker-ansible .

run :
docker run --rm -v ${PWD}/inventories:/inventories -ti andrewrothstein/docker-ansible ansible '*' -i /inventories/empty -M ping
