
FROM centos:7
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN yum update -y && yum install -y epel-release && yum install -y python python-devel python-pip python-setuptools debianutils xz-utils bzip2 file findutils git gzip mercurial procps subversion sudo tar unzip zip wget curl ca-certificates libffi-devel openssl-devel && yum -y groupinstall "Development tools" && yum clean all && pip install --upgrade pip && pip install --upgrade ansible==2.0.2.0
WORKDIR /etc/ansible
# configure ansible to target the localhost -- inside the container
ADD ansible.cfg ansible.cfg
ADD localhost hosts
RUN ansible --version && ansible all --list-hosts && ansible all -m ping