FROM centos:7
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN yum update -y \
 && yum install -y epel-release \
 && yum install -y \
   python \
   python-pip \
   python-crypto \
   python-cffi \
   python-yaml \
   python-jinja2 \
   python-paramiko \
   ca-certificates \
 && pip install --upgrade pip \
 && pip install ansible==2.5.3.0 \
 && yum clean all

WORKDIR /etc/ansible
# configure ansible to target the localhost -- inside the container
ADD ansible.cfg ansible.cfg

RUN mkdir -p /etc/ansible/inventories
WORKDIR /etc/ansible/inventories
ADD localhost hosts

RUN ansible --version \
 && ansible all --list-hosts \
 && ansible all -m ping
