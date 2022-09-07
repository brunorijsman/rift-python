# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version
VAGRANTFILE_API_VERSION = "2"

Vagrant.require_version ">= 1.5.0"

$install_reqs = <<SCRIPT
  apt update
  apt-get install -y build-essential
  apt-get install -y python3-dev
  apt-get install -y python3-venv
  apt-get install -y virtualenv
  apt-get install -y traceroute
  setcap cap_net_admin+ep /usr/bin/python3.10
SCRIPT

$mount_rift_python = <<SCRIPT
  [ -e ~/rift-python ] || ln -s /vagrant ~/rift-python
SCRIPT

$prepare_venv = <<SCRIPT
  cd ~/rift-python
  python3 -m venv vagrant_env
  source vagrant_env/bin/activate
  pip install --upgrade pip
  pip install -r requirements-3-10.txt
SCRIPT

$venv_on_login = <<SCRIPT
  cat <<EOT >> ~/.profile
if [ -f ~/rift-python/vagrant_env/bin/activate ]; then
  . ~/rift-python/vagrant_env/bin/activate
fi
EOT
SCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.define "ubuntu" do |ubuntu|
    ubuntu.vm.box = "ubuntu/jammy64"
    ubuntu.vm.box_check_update = false
    ubuntu.vm.hostname = "jammyvm"

    ubuntu.vm.provider :virtualbox do |vb|
      vb.cpus = 2
      vb.customize ["modifyvm", :id, "--memory", "1024"]
      vb.customize ["modifyvm", :id, "--nictype1", "virtio"]
    end

    ubuntu.vm.provision "install_reqs", type: "shell", inline: $install_reqs
    ubuntu.vm.provision "mount_rift_python", type: "shell", inline: $mount_rift_python, privileged: false
    ubuntu.vm.provision "prepare_venv", type: "shell", inline: $prepare_venv, privileged: false
    ubuntu.vm.provision "venv_on_login", type: "shell", inline: $venv_on_login, privileged: false
  end
end
