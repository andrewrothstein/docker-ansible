FROM centos:7
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN yum update -y \
 && yum install -y python wget \
 && wget https://bootstrap.pypa.io/get-pip.py -O /usr/local/bin/get-pip.py \
 && python /usr/local/bin/get-pip.py \
 && pip install urllib3 ansible==2.7.10 \
 && yum clean all \
 && rm -rf /var/cache/yum

WORKDIR /etc/ansible
# configure ansible to target the localhost -- inside the container
ADD ansible.cfg ansible.cfg

RUN mkdir -p /etc/ansible/inventories
WORKDIR /etc/ansible/inventories
ADD localhost hosts

RUN ansible --version \
 && ansible all --list-hosts \
 && ansible all -m ping
