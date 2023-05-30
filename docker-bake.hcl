variable "OS" {}
variable "OS_VER" {}

target "base" {
  context = "."
  dockerfile = "Dockerfile"
  labels = {
    maintainer = "Andrew Rothstein andrew.rothstein@gmail.com"
  }
  platforms = [
    "linux/amd64",
    "linux/arm64"
  ]
  tags = [
    "quay.io/andrewrothstein/docker-ansible:${OS}_${OS_VER}",
    "ghcr.io/andrewrothstein/docker-ansible:${OS}_${OS_VER}"
  ]
}

target "alpine" {
  inherits = [
    "base"
  ]
  args = {
    OS = "alpine"
  }
}

target "alpine_317" {
  inherits = [
    "alpine"
  ]
  args = {
    OS_VER = "3.17"
  }
}

target "alpine_318" {
  inherits = [
    "alpine"
  ]
  args = {
    OS_VER = "3.18"
  }
}

target "alpine_edge" {
  inherits = [
    "alpine"
  ]
  args = {
    OS_VER = "edge"
  }
}

target "archlinux_latest" {
  inherits = [
    "base"
  ]
  platforms = [
    "linux/amd64"
  ]
  args = {
    OS = "archlinux"
    OS_VER = "latest"
  }
}

target "debian" {
  inherits = [
    "base"
  ]
  args = {
    OS = "debian"
  }
}

target "debian_bookworm" {
  inherits = [
    "debian"
  ]
  args = {
    OS_VER = "bookworm"
  }
}

target "debian_bullseye" {
  inherits = [
    "debian"
  ]
  args = {
    OS_VER = "bullseye"
  }
}

target "fedora" {
  inherits = [
    "base"
  ]
  args = {
    OS = "fedora"
  }
}

target "fedora_37" {
  inherits = [
    "fedora"
  ]
  args = {
    OS_VER = "37"
  }
}

target "fedora_38" {
  inherits = [
    "fedora"
  ]
  args = {
    OS_VER = "38"
  }
}

target "rockylinux" {
  inherits = [
    "base"
  ]
  args = {
    OS = "rockylinux"
  }
}

target "rockylinux_8" {
  inherits = [
    "rockylinux"
  ]
  args = {
    OS_VER = "8"
  }
}

target "rockylinux_9" {
  inherits = [
    "rockylinux"
  ]
  args = {
    OS_VER = "9"
  }
}

target "ubuntu" {
  inherits = [
    "base"
  ]
  args = {
    OS = "ubuntu"
  }
}

target "ubuntu_focal" {
  inherits = [
    "ubuntu"
  ]
  args = {
    OS_VER = "focal"
  }
}

target "ubuntu_jammy" {
  inherits = [
    "ubuntu"
  ]
  args = {
    OS_VER = "jammy"
  }
}

group "default" {
  targets = [
    "alpine_317",
    "alpine_318",
    "alpine_edge",
    "archlinux_latest",
    "debian_bookworm",
    "debian_bullseye",
    "fedora_37",
    "fedora_38",
    "rockylinux_8",
    "rockylinux_9",
    "ubuntu_focal",
    "ubuntu_jammy"
  ]
}
