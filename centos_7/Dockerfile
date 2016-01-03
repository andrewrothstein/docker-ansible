
FROM centos:7
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

RUN yum update -y && yum install -y epel-release && yum install -y python python-devel python-pip bzip2 file findutils git gzip mercurial procps subversion sudo tar debianutils unzip xz-utils zip wget curl && yum -y groupinstall "Development tools" && pip install --upgrade pip && pip install ansible==1.9.1
ADD ansible.cfg /etc/ansible/ansible.cfg
ADD localhost /etc/ansible/hosts
RUN ansible '*' -m ping
RUN ansible --version