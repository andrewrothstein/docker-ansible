
FROM fedora:22
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN dnf update -y && dnf install -y python2 python2-devel libselinux-python python-pip make automake gcc gcc-c++ redhat-rpm-config bzip2 file findutils git gzip mercurial procps subversion sudo tar unzip zip wget curl ca-certificates && dnf -y groupinstall "Development tools" && dnf clean all && pip install --upgrade pip && pip install ansible==2.0.0.2
WORKDIR /etc/ansible
# configure ansible to target the localhost -- inside the container
ADD ansible.cfg ansible.cfg
ADD localhost hosts
RUN ansible --version && ansible all --list-hosts && ansible all -m ping