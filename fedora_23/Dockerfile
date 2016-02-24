
FROM fedora:23
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN dnf update -y && dnf install -y python2 python2-devel python2-dnf libselinux-python python-pip make automake gcc gcc-c++ redhat-rpm-config bzip2 file findutils git gzip mercurial procps subversion sudo tar unzip zip wget curl ca-certificates && dnf -y groupinstall "Development tools" && dnf clean all && pip install --upgrade pip && pip install ansible==2.0.0.2
RUN ansible --version

# configure ansible to target the localhost -- inside the container
ADD ansible.cfg /etc/ansible/ansible.cfg
ADD localhost /etc/ansible/hosts
RUN ansible '*' -m ping
