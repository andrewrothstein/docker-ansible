FROM fedora:29
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN dnf update -y \
 && dnf install -y python3 wget \
 && wget https://bootstrap.pypa.io/get-pip.py -O /usr/local/bin/get-pip.py \
 && python3 /usr/local/bin/get-pip.py \
 && pip3 install urllib3 ansible==2.8.3 \
 && dnf clean all

WORKDIR /etc/ansible
# configure ansible to target the localhost -- inside the container
ADD ansible.cfg ansible.cfg

RUN mkdir -p /etc/ansible/inventories
WORKDIR /etc/ansible/inventories
ADD localhost hosts

RUN ansible --version \
 && ansible all --list-hosts \
 && ansible all -m ping
