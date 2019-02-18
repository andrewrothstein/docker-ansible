FROM base/archlinux:latest
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN pacman -S -y \
 && pacman -S --noconfirm \
   python2 \
   python2-appdirs \
   python2-asn1crypto \
   python2-bcrypt \
   python2-cffi \
   python2-crypto \
   python2-cryptography \
   python2-enum34 \
   python2-idna \
   python2-jinja \
   python2-markupsafe \
   python2-packaging \
   python2-pip \
   python2-pyasn1 \
   python2-pyparsing \
   python2-yaml \
   python2-paramiko \
   ca-certificates \
 && pip2 install --upgrade pip \
 && pip2 install ansible==2.7.7 \
 && pacman -S -c --noconfirm

WORKDIR /etc/ansible
# configure ansible to target the localhost -- inside the container
ADD ansible.cfg ansible.cfg

RUN mkdir -p /etc/ansible/inventories
WORKDIR /etc/ansible/inventories
ADD localhost hosts

RUN ansible --version \
 && ansible all --list-hosts \
 && ansible all -m ping
