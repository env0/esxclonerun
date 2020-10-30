# ESX Clone Run

* clone VM inside an ESX (without vCenter)
  * use pre installed ubuntu cloner VM
  * command over `pyvmomi`
* run a command and said clone

## Structure

* `main.py` - the cli entry point, and main function
* `slavevm.py` - lowest layer API to download / upload files and run processes on remote guest OS in slave VM
* `bashinslave.py` - middle layer API that bundles few lower API calls to invoke a bash script remotely, collect it's output, and fail with proper error reporting

## Terminology

* `main` - code that run on env0 side (or my devstation)
* `cloner` - the preinstalled ubuntu VM (must be running) to use for cloning (run ovftool)
* `cloned` - the vm to clone (`to_clone` by default)
* `clone` - the result of the clone (currently, cleanup is manual)
* `slave VM` - either the cloner VM or the clone VM
* `guest` - the OS running inside a `slave VM`. Currently assumed to be ubuntu

## Example CLI (that worked for me)

```
pipenv run python3 main.py --esx-password=<ESX ROOT PASSWORD> --no-verify-cert -cloner-esx-password=<ESX ROOT PASSWORD>
```

## Configuration

All configuration parameters are accessible from CLI. *please note some arguments must come before the command (e.g., "run", "clone) and some only come after it.* to get help:

```
pipenv run python3 main.py --help
```

output when this document is created:

```
$$ pipenv run python3 main.py --help
usage: main.py [-h] [--esx-username ESX_USERNAME] --esx-password ESX_PASSWORD [--esx-hostname ESX_HOSTNAME] [--esx-port ESX_PORT]
               [--no-verify-cert] [--clone-name CLONE_NAME] [--clone-username CLONE_USERNAME] [--clone-password CLONE_PASSWORD]
               {clone,bash,run,destroy} ...

positional arguments:
  {clone,bash,run,destroy}
    clone               Clone a VM and power on the clone
    bash                Run a bash script inside a clone VM (linux guest only)
    run                 Run a program on clone VM (windows and linux guests compatible)
    destroy             Destroy the cloned VM

optional arguments:
  -h, --help            show this help message and exit
  --esx-username ESX_USERNAME
                        Credentials for master accessing ESX
  --esx-password ESX_PASSWORD
                        Credentials for master accessing ESX
  --esx-hostname ESX_HOSTNAME
                        ESX hostname / IP address
  --esx-port ESX_PORT
  --no-verify-cert      Dont verify ESX certificate
  --clone-name CLONE_NAME
                        Name of the newly created cloned VM
  --clone-username CLONE_USERNAME
                        Clone slave VM guest OS credentials to use for running final script
  --clone-password CLONE_PASSWORD
                        Clone slave VM guest OS credentials to use for running final script



$$ pipenv run python3 main.py clone --help
usage: main.py clone [-h] [--cloner-vm-name CLONER_VM_NAME] [--cloner-username CLONER_USERNAME]
                     [--cloner-password CLONER_PASSWORD] [--cloner-esx-username CLONER_ESX_USERNAME] --cloner-esx-password
                     CLONER_ESX_PASSWORD [--cloner-esx-hostname CLONER_ESX_HOSTNAME] [--cloner-esx-port CLONER_ESX_PORT]
                     [--vm-to-clone VM_TO_CLONE]

optional arguments:
  -h, --help            show this help message and exit
  --cloner-vm-name CLONER_VM_NAME
                        Name of ubuntu slave VM to use for cloning a VM (in ESX due to vCenter not being available)
  --cloner-username CLONER_USERNAME
                        Cloner slave VM guest OS credentials to use for running ovftool
  --cloner-password CLONER_PASSWORD
                        Cloner slave VM guest OS credentials to use for running ovftool
  --cloner-esx-username CLONER_ESX_USERNAME
                        Credentials for cloner accessing ESX (via ovftool)
  --cloner-esx-password CLONER_ESX_PASSWORD
                        Credentials for cloner accessing ESX (via ovftool)
  --cloner-esx-hostname CLONER_ESX_HOSTNAME
                        ESX hostname / IP address from within the cloner (for ovftool)
  --cloner-esx-port CLONER_ESX_PORT
  --vm-to-clone VM_TO_CLONE
                        Name of VM to clone



$$ pipenv run python3 main.py run --help
usage: main.py run [-h] executable arguments

positional arguments:
  executable  full path to an executable to run
  arguments   string of arguments to execute said executable with

optional arguments:
  -h, --help  show this help message and exit



$$ pipenv run python3 main.py bash --help
usage: main.py bash [-h] bash_script

positional arguments:
  bash_script  contents of the bash script to execute

optional arguments:
  -h, --help   show this help message and exit



$$ pipenv run python3 main.py destroy --help
usage: main.py destroy [-h]

optional arguments:
  -h, --help  show this help message and exit
```

## Integrate POC into a real system

Probable steps:

* Install a cloner VM on the client's ESX
* Create a to_clone template VM on the client's ESX

*make sure to remove CDROM devices from to_clone template* and power it off
*make sure to install vmtools on to_clone template*


note: if master code does not run one off, but is part of a long living process, make sure to
add bit more fine grain control for calling "disconnect" on the ESX connection after use.

### Using pipenv

`pipenv` is modern `pip`, skip this if you are familiar with it.

Quick getting started to fetch pip dependencies:

```
sudo pip3 install pipenv
pipenv sync -d
```

### How the Ubuntu cloner vm was created:

* used iso from storage for ubuntu 20.04.1
* username: me password: env0rocks
* make sure to have enough space for the vmdk of the cloned VM (plus a spare of +- 8GB)
* no ssh, whole disk (16GB) formatting, static ip address
* sudo apt-get update ; sudo apt-get upgrade ; sudo apt-get install unattended-upgrades
* sudo apt-get install python3-pip ; sudo pip3 install pyvmomi
* install ovftool (copy in downloads folder) - i used file.io to transfer the file to the VM

### a possible way to create private routing:

define a private vlan / new vswitch for a new private network interface for the esxlocal VM and a new vmk.
private a in 192.168.x.x

