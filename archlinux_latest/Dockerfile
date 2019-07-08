FROM archlinux/base:latest
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN pacman -S -y \
 && pacman -S --noconfirm \
   python \
   python-pip \
   ca-certificates \
 && pip install --upgrade pip \
 && pip install ansible==2.8.2

WORKDIR /etc/ansible
# configure ansible to target the localhost -- inside the container
ADD ansible.cfg ansible.cfg

RUN mkdir -p /etc/ansible/inventories
WORKDIR /etc/ansible/inventories
ADD localhost hosts

RUN ansible --version \
 && ansible all --list-hosts \
 && ansible all -m ping
