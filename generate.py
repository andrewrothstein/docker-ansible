#!/usr/bin/env python

import argparse
from jinja2 import Environment
from subprocess import call
import os
import shutil

Dockerfile = """
FROM {{baseimage}}
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN {{pkg_update}} && {{python_and_pip_install}} && pip install --upgrade pip && pip install ansible==1.9.1
RUN ansible --version

# configure ansible to target the localhost -- inside the container
ADD ansible.cfg /etc/ansible/ansible.cfg
ADD localhost /etc/ansible/hosts
RUN ansible '*' -m ping

# embed roles
ONBUILD ADD requirements.yml requirements.yml
ONBUILD RUN ansible-galaxy install -r requirements.yml

# execute playbook to configure container to suit
ONBUILD ADD playbook.yml playbook.yml
ONBUILD RUN ansible-playbook playbook.yml
"""

def copy_file(tag, file) :
  shutil.copyfile(file, '{0}/{1}'.format(tag, file))

def copy_artifacts(tag) :
  copy_file(tag, 'ansible.cfg')
  copy_file(tag, 'localhost')
	
def write(params) :
  tag = params["tag"]
  if (not os.path.isdir(tag)) :
    os.mkdir(tag)
  fq_dockerfile = "{0}/Dockerfile".format(tag) 
  print "writing {0}...".format(fq_dockerfile)
  f = open(fq_dockerfile, 'w')
  f.write(Environment().from_string(Dockerfile).render(params))
  f.close()
  copy_artifacts(tag)
	
def build(params) :
  tag = params["tag"]
  container_name = 'andrewrothstein/docker-ansible'
  print "building the {0}:{1} container...".format(container_name, tag)
  cmd = ['docker', 'build', '-t', '{0}:{1}'.format(container_name, tag), tag]
  os.chdir
  call(cmd, shell=False)

def push(registry) :
  def pusher(params) :
    tag = params["tag"]
    container_name = 'andrewrothstein/docker-ansible'
    url = "{0}/{1}:{2}".format(registry, container_name, tag)
    print "pushing building to {0}...".format(url)
    cmd = ['docker', 'push', url]
    os.chdir
    call(cmd, shell=False)
  return pusher

def pull(params) :
  baseimg = params["baseimage"]
  print "pulling {0}...".format(baseimg)
  cmd = ['docker', 'pull', baseimg]
  call(cmd, shell=False)

if __name__ == '__main__' :

  parser = argparse.ArgumentParser(
    description='generates a bunch of Docker base containers for use with Ansible'
  )
  parser.add_argument(
    '-w',
    '--write',
    action='store_true',
    help='write the Dockerfiles'
  )
  parser.add_argument(
    '-b',
    '--build',
    action='store_true',
    help='build the Docker containers'
  )
  parser.add_argument(
    '-p',
    '---push',
    help='push to the given docker registry'
  )
  parser.add_argument(
    '-f',
    '--pull',
    action='store_true',
    help='pull base images'
  )
  
  args = parser.parse_args()
	
  apt_update = 'apt-get update -y'
  apt_python_and_pip_install = 'apt-get install -y python python-dev python-pip python-apt aptitude curl wget'
  
  yum_update = 'yum update -y'
  yum_fedora_python_and_pip_install = 'yum install -y python python-devel python-pip bzip2 file findutils git gzip mercurial procps subversion sudo tar debianutils unzip xz-utils zip wget curl && yum -y groupinstall "Development tools"'
  yum_centos_python_and_pip_install = 'yum install -y epel-release && yum install -y python python-devel python-pip bzip2 file findutils git gzip mercurial procps subversion sudo tar debianutils unzip xz-utils zip wget curl && yum -y groupinstall "Development tools"'

  dnf_update = 'dnf update -y'
  dnf_python_and_pip_install = 'dnf install -y python2 python2-dnf libselinux-python python-pip'
  
  configs = [
    { "baseimage" : "fedora:21",
      "tag" : "fedora_21",
      "pkg_update" : yum_update,
      "python_and_pip_install" : yum_fedora_python_and_pip_install
    },
    { "baseimage" : "fedora:22",
      "tag" : "fedora_22",
      "pkg_update" : dnf_update,
      "python_and_pip_install" : dnf_python_and_pip_install
    },
    { "baseimage" : "fedora:23",
      "tag" : "fedora_23",
      "pkg_update" : dnf_update,
      "python_and_pip_install" : dnf_python_and_pip_install
    },
    { "baseimage" : "centos:7",
      "tag" : "centos_7",
      "pkg_update" : yum_update,
      "python_and_pip_install" : yum_centos_python_and_pip_install,
    },
    { "baseimage" : "ubuntu:trusty",
      "tag" : "ubuntu_trusty",
      "pkg_update" : apt_update,
      "python_and_pip_install" : apt_python_and_pip_install
    },
    { "baseimage" : "ubuntu:vivid",
      "tag" : "ubuntu_vivid",
      "pkg_update" : apt_update,
      "python_and_pip_install" : apt_python_and_pip_install
    },
    { "baseimage" : "ubuntu:wily",
      "tag" : "ubuntu_wily",
      "pkg_update" : apt_update,
      "python_and_pip_install" : apt_python_and_pip_install
    },
    { "baseimage" : "ubuntu:xenial",
      "tag" : "ubuntu_xenial",
      "pkg_update" : apt_update,
      "python_and_pip_install" : apt_python_and_pip_install
    }
  ]

  if (args.pull) :
    map(pull, configs)
    
  if (args.write) :
    map(write, configs)

  if (args.build) :
    map(build, configs)

  if (args.push) :
    map(push(args.push), configs)
