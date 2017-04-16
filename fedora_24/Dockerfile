FROM fedora:24
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN dnf update -y \
 && dnf install -y \
   python \
   libselinux-python \
   python-dnf \
   python-pip \
   python-crypto \
   python-cffi \
   python-yaml \
   python-jinja2 \
   python-paramiko \
   ca-certificates \
 && pip install --upgrade pip \
 && pip install ansible==2.3.0.0 \
 && dnf clean all

WORKDIR /etc/ansible
# configure ansible to target the localhost -- inside the container
ADD ansible.cfg ansible.cfg
ADD localhost hosts

RUN ansible --version \
 && ansible all --list-hosts \
 && ansible all -m ping
