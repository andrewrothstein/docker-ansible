
FROM centos:7
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN yum update -y && yum install -y epel-release && yum install -y python python-devel python-pip debianutils xz-utils bzip2 file findutils git gzip mercurial procps subversion sudo tar unzip zip wget curl ca-certificates && yum -y groupinstall "Development tools" && yum clean all && pip install --upgrade pip && pip install ansible==2.0.0.2
RUN ansible --version

# configure ansible to target the localhost -- inside the container
ADD ansible.cfg /etc/ansible/ansible.cfg
ADD localhost /etc/ansible/hosts
RUN ansible '*' -m ping
