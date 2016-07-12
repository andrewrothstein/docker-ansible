#!/usr/bin/env python

import argparse
from jinja2 import Environment
from subprocess import call
import os
import shutil
from string import join

Dockerfile = """
FROM {{baseimage}}
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN {{pkg_update}} && {{python_and_pip_install}} && pip install --upgrade pip && pip install --upgrade ansible==2.1.0.0
WORKDIR /etc/ansible
# configure ansible to target the localhost -- inside the container
ADD ansible.cfg ansible.cfg
ADD localhost hosts
RUN ansible --version && ansible all --list-hosts && ansible all -m ping
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
  return call(cmd, shell=False)

def push(registry) :
  def pusher(params) :
    tag = params["tag"]
    container_name = 'andrewrothstein/docker-ansible'
    url = "{0}/{1}:{2}".format(registry, container_name, tag)
    print "pushing building to {0}...".format(url)
    cmd = ['docker', 'push', url]
    os.chdir
    return call(cmd, shell=False)
  return pusher

def pull(params) :
  baseimg = params["baseimage"]
  print "pulling {0}...".format(baseimg)
  cmd = ['docker', 'pull', baseimg]
  return call(cmd, shell=False)

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

  def update(pkg_mgr) :
    return join([pkg_mgr, 'update -y'], sep=' ')

  def install(pkg_mgr, pkgs) :
    return join([pkg_mgr, 'install -y'] + pkgs, sep=' ')

  def groupinstall(pkg_mgr) :
    return join([pkg_mgr, '-y groupinstall "Development tools"'], sep=' ')

  apt_update = update('apt-get')
  apt_pkgs = ['python', 'python-dev', 'python-pip', 'python-setuptools',
              'python-apt',
              'python-setuptools', 'aptitude', 'curl', 'wget',
              'ca-certificates', 'libffi-dev', 'libssl-dev']

  apt_python_and_pip_install = join(
    [ install('apt-get', apt_pkgs),
      'apt-get clean' ],
    sep=' && '
    )

  rh_common_pkgs = ['bzip2', 'file', 'findutils',
		    'git', 'gzip', 'mercurial', 'procps',
		    'subversion', 'sudo', 'tar', 'unzip',
		    'zip', 'wget', 'curl', 'ca-certificates',
                    'libffi-devel', 'openssl-devel']

  centos7_pkgs = ['python', 'python-devel',
                  'python-pip', 'python-setuptools',
                  'debianutils', 'xz-utils']

  yum_update = update('yum')
  centos7_python_and_pip_install = join(
    [ install('yum', ['epel-release']),
      install('yum', centos7_pkgs + rh_common_pkgs),
      groupinstall('yum'),
      'yum clean all'
    ],
    sep=' && '
  )

  dnf_update = update('dnf')
  f22_pkgs = ['python2', 'python2-devel',
              'libselinux-python', 'python-pip',
              'python2-setuptools',
	      'make', 'automake', 'gcc', 'gcc-c++',
              'redhat-rpm-config']
  f22_python_and_pip_install = join(
    [ install('dnf', f22_pkgs + rh_common_pkgs),
      groupinstall('dnf'),
      'dnf clean all'
    ],
    sep=' && '
  )

  f23_pkgs = ['python2', 'python2-devel', 'python2-dnf',
              'libselinux-python', 'python-pip',
              'python2-setuptools',
	      'make', 'automake', 'gcc', 'gcc-c++',
              'redhat-rpm-config']
  f23_python_and_pip_install = join(
    [ install('dnf', f23_pkgs + rh_common_pkgs),
      groupinstall('dnf'),
      'dnf clean all'
    ],
    sep=' && '
  )

  apk_python_and_pip_install = join(['apk', 'add',
                                     'python', 'python-dev', 'py-pip', 'build-base',
                                     'curl', 'wget', 'ca-certificates',
                                     'libffi-dev', 'openssl-dev'],
                                    sep=' ')
  
  configs = [
    { "baseimage" : "centos:7",
      "tag" : "centos_7",
      "pkg_update" : yum_update,
      "python_and_pip_install" : centos7_python_and_pip_install,
    },
    { "baseimage" : "ubuntu:trusty",
      "tag" : "ubuntu_trusty",
      "pkg_update" : apt_update,
      "python_and_pip_install" : apt_python_and_pip_install
    },
    { "baseimage" : "ubuntu:xenial",
      "tag" : "ubuntu_xenial",
      "pkg_update" : apt_update,
      "python_and_pip_install" : apt_python_and_pip_install
    },
    { "baseimage" : "alpine:3.3",
      "tag" : "alpine_3.3",
      "pkg_update" : "apk update && apk upgrade",
      "python_and_pip_install" : apk_python_and_pip_install
    },
    { "baseimage" : "alpine:3.4",
      "tag" : "alpine_3.4",
      "pkg_update" : "apk update && apk upgrade",
      "python_and_pip_install" : apk_python_and_pip_install
    },
    { "baseimage" : "alpine:edge",
      "tag" : "alpine_edge",
      "pkg_update" : "apk update && apk upgrade",
      "python_and_pip_install" : apk_python_and_pip_install
    },
    { "baseimage" : "debian:jessie",
      "tag" : "debian_jessie",
      "pkg_update" : apt_update,
      "python_and_pip_install" : apt_python_and_pip_install
    },
    { "baseimage" : "fedora:23",
      "tag" : "fedora_23",
      "pkg_update" : dnf_update,
      "python_and_pip_install" : f23_python_and_pip_install
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
