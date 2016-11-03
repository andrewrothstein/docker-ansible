
FROM fedora:23
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN dnf update -y && dnf install -y python2 python2-devel python2-dnf libselinux-python python-pip python2-setuptools make automake gcc gcc-c++ redhat-rpm-config bzip2 file findutils git gzip mercurial procps subversion sudo tar unzip zip wget curl ca-certificates libffi-devel openssl-devel && dnf -y groupinstall "Development tools" && dnf clean packages && pip install --upgrade pip && pip install --upgrade setuptools && pip install --upgrade ansible==2.2.0.0
WORKDIR /etc/ansible
# configure ansible to target the localhost -- inside the container
ADD ansible.cfg ansible.cfg
ADD localhost hosts
RUN ansible --version && ansible all --list-hosts && ansible all -m ping