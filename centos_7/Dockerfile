FROM centos:7
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN yum update -y \
 && yum install -y epel-release \
 && yum install -y \
   ca-certificates \
   tar \
   unzip \
   gzip \
   bzip2 \
   python \
   python-pip \
   python-crypto \
   python-cffi \
   python-yaml \
   python-jinja2 \
   python-paramiko \
 && pip install --upgrade pip \
 && pip install ansible==2.2.1.0 \
 && yum clean all

WORKDIR /etc/ansible
# configure ansible to target the localhost -- inside the container
ADD ansible.cfg ansible.cfg
ADD localhost hosts

RUN ansible --version \
 && ansible all --list-hosts \
 && ansible all -m ping
