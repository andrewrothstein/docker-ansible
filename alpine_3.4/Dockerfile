FROM alpine:3.4
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN apk update \
 && apk upgrade \
 && apk add \
   libffi \
   python \
   py-pip \
   py-cryptography \
   py-cffi \
   py-yaml \
   py-jinja2 \
   py-ecdsa \
   py-paramiko \
   ca-certificates \
 && pip install --upgrade pip \
 && pip install ansible==2.5.0.0 \
 && rm -rf /var/cache/apk/*

WORKDIR /etc/ansible
# configure ansible to target the localhost -- inside the container
ADD ansible.cfg ansible.cfg
ADD localhost hosts

RUN ansible --version \
 && ansible all --list-hosts \
 && ansible all -m ping
