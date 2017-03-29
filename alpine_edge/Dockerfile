FROM alpine:edge
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN apk update \
 && apk upgrade \
 && apk add \
   python2 \
   py2-pip \
   py2-crypto \
   py2-cffi \
   py2-yaml \
   py2-jinja2 \
   py2-paramiko \
 && pip install --upgrade pip \
 && pip install ansible==2.2.1.0

WORKDIR /etc/ansible
# configure ansible to target the localhost -- inside the container
ADD ansible.cfg ansible.cfg
ADD localhost hosts

RUN ansible --version \
 && ansible all --list-hosts \
 && ansible all -m ping
