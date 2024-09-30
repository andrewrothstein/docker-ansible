variable "UPSTREAM_REGISTRY" {
  default = "docker.io"
}

variable "DEFAULT_UPSTREAM_ORG" {
  default = "library"
}
variable "UPSTREAM_ORG" {}

variable "TARGET_IMAGE_SEMVER" {
  default = "0.0.0"
}

variable "OS" {}
variable "OS_VER" {}
variable "SHA" {}

variable "UPSTREAM_OS" {}
variable "UPSTREAM_OS_VER" {}

function "dflt" {
  params=[o,v]
  result = o == "" ? v : o
}

variable "UPSTREAM_IMAGE" {
  default = "${UPSTREAM_REGISTRY}/${dflt(UPSTREAM_ORG,DEFAULT_UPSTREAM_ORG)}/${dflt(UPSTREAM_OS, OS)}:${dflt(UPSTREAM_OS_VER,OS_VER)}"
}

variable "TARGET_OS" {
  default = ""
}

variable "TARGET_OS_VER" {
  default = ""
}

variable "TARGET_IMAGE" {
  default = "docker-ansible:${TARGET_IMAGE_SEMVER}-${dflt(TARGET_OS,OS)}.${dflt(TARGET_OS_VER,OS_VER)}"
}

target "default" {
  context = "."
  dockerfile-inline = <<-EOF

  FROM ${UPSTREAM_IMAGE}
  COPY profile.d/* /etc/profile.d
  ENV WDIR=/docker-ansible${SHA}
  RUN mkdir -p $WDIR
  WORKDIR $WDIR
  ADD . $WDIR
  SHELL ["/bin/sh", "-lc"]
  RUN set -ex; ansible_install ${dflt(TARGET_OS,OS)} ${dflt(TARGET_OS_VER,OS_VER)}; rm -rf .git/
  EOF

  labels = {
    maintainer = "Andrew Rothstein andrew.rothstein@gmail.com"
  }
  platforms = [
    "linux/amd64",
  ]
  tags = [
    "docker.io/andrewrothstein/${TARGET_IMAGE}",
    "ghcr.io/andrewrothstein/${TARGET_IMAGE}",
  ]
}
