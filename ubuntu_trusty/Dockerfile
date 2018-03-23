FROM ubuntu:trusty
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN apt-get update -y \
 && apt-get upgrade -y \
 && apt-get install -y \
   aptitude \
   apt-transport-https \
   libffi-dev \
   libssl-dev \
   python \
   python-dev \
   python-apt \
   python-pip \
   python-crypto \
   python-yaml \
   python-jinja2 \
   python-paramiko \
   python-setuptools \
   python-urllib3 \
   python-openssl \
   python-pyasn1 \
   ca-certificates \
 && pip install --upgrade pip setuptools \
 && pip install ndg-httpsclient ansible==2.5.0.0 \
 && apt-get clean

WORKDIR /etc/ansible
# configure ansible to target the localhost -- inside the container
ADD ansible.cfg ansible.cfg
ADD localhost hosts

RUN ansible --version \
 && ansible all --list-hosts \
 && ansible all -m ping
