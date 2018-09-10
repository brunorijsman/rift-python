# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version
VAGRANTFILE_API_VERSION = "2"

Vagrant.require_version ">= 1.5.0"

$install_reqs = <<SCRIPT
  apt update
  apt-get install -y python3-venv
SCRIPT

$prepare_venv = <<SCRIPT
  cd
  python3 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r /vagrant/requirements.txt
SCRIPT

$venv_on_login = <<SCRIPT
  cat <<EOT >> ~/.profile

# activate venv by default
if [ -f ~/venv/bin/activate ]; then
    . ~/venv/bin/activate
fi
EOT
  # make a symlink to conveniently get to top level
  [ -e ~/rift-python ] || ln -s /vagrant ~/rift-python
SCRIPT


Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.define "ubuntu" do |ubuntu|
    ubuntu.vm.box = "ubuntu/xenial64"
    ubuntu.vm.box_check_update = false
    ubuntu.vm.hostname = "xenialvm"

    ubuntu.vm.provider :virtualbox do |vb|
      vb.cpus = 2
      vb.customize ["modifyvm", :id, "--memory", "1024"]
      vb.customize ["modifyvm", :id, "--nictype1", "virtio"]
    end

    ubuntu.vm.provision "install_reqs", type: "shell", inline: $install_reqs
    ubuntu.vm.provision "prepare_venv", type: "shell", inline: $prepare_venv, privileged: false
    ubuntu.vm.provision "venv_on_login", type: "shell", inline: $venv_on_login, privileged: false
  end
end
