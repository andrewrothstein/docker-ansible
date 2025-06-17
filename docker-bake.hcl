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

variable "TARGET_IMAGE" {
  default = "docker-ansible:${TARGET_IMAGE_SEMVER}-${OS}.${OS_VER}"
}

variable "UV_VERSION" {
  default = "latest"
}

target "default" {
  context = "."
  dockerfile-inline = <<-EOF
  # Stage 1: Get uv from official image
  FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

  # Stage 2: Build final image
  FROM ${UPSTREAM_IMAGE}

  # Copy uv from the official image
  COPY --from=uv /uv /usr/local/bin/uv

  COPY profile.d/* /etc/profile.d
  ENV WDIR=/docker-ansible${SHA}
  RUN mkdir -p $WDIR
  WORKDIR $WDIR
  ADD . $WDIR
  SHELL ["/bin/sh", "-lc"]
  RUN set -ex; ansible_install; rm -rf .git/
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
