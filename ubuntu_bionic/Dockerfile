FROM ubuntu:bionic
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN apt-get update -y \
 && apt-get upgrade -y \
 && apt-get install -y wget software-properties-common ca-certificates libffi-dev libssl-dev python3 python3-dev \
 && wget https://bootstrap.pypa.io/get-pip.py -O /usr/local/bin/get-pip.py \
 && python3 /usr/local/bin/get-pip.py \
 && pip install urllib3 ansible==2.5.4.0 \
 && apt-get clean -y

WORKDIR /etc/ansible
# configure ansible to target the localhost -- inside the container
ADD ansible.cfg ansible.cfg

RUN mkdir -p /etc/ansible/inventories
WORKDIR /etc/ansible/inventories
ADD localhost hosts

RUN ansible --version \
 && ansible all --list-hosts \
 && ansible all -m ping
