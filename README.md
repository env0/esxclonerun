# ESXLocal

Run a python function remotely on a Ubuntu slave VM hosted on an ESX, using `pyvmomi`.

## Structure

* `slave` folder - this folder contains the python source code files to run on the remote VM. currently:
  * `run.py` - contains a single function `run` which is the "entry point"
* `master` folder - the python library that should run on env0 side (tested from my linux devstation):
  * `main.py` - the cli entry point, and main function
  * `slavevm.py` - lowest layer API to download / upload files and run processes on remote guest OS in slave VM
  * `bashinslave.py` - middle layer API that bundles few lower API calls to invoke a bash script remotely, collect it's output, and fail with proper error reporting
  * `pythoninslave.py` - highest layer API that contains a class to package python source code folder and run it remotely.

## Terminology

* `master` - code that run on env0 side (or my devstation)
* `slave VM` - the slave VM in ESX runs Ubuntu as a `guest` OS, and inside it the `egg` runs
* `guest` - the OS running inside the `slave VM`. Currently assumed to be ubuntu
* `egg` - the python source code folder to run inside the `slave VM`

## Example CLI (that worked for me)

```
cd master
pipenv run python3 main.py --esx-password=<ESX ROOT PASSWORD> --no-verify-cert --egg-kwargs='{"esx_hostname":"185.141.60.50", "esx_username": "root", "esx_password": "<ESX ROOT PASSWORD>"}'
```

## Configuration

All configuration parameters are accessible from CLI. to get help:

```
cd master
pipenv run python3 main.py --help
```

output when this document is created:

```
usage: main.py [-h] [--esx-username ESX_USERNAME] --esx-password ESX_PASSWORD [--esx-hostname ESX_HOSTNAME] [--esx-port ESX_PORT]
               [--slave-vm-name SLAVE_VM_NAME] [--no-verify-cert] [--guest-username GUEST_USERNAME]
               [--guest-password GUEST_PASSWORD] [--egg-folder EGG_FOLDER] [--egg-entry-module EGG_ENTRY_MODULE]
               [--egg-entry-function EGG_ENTRY_FUNCTION] --egg-kwargs-json EGG_KWARGS_JSON

optional arguments:
  -h, --help            show this help message and exit
  --esx-username ESX_USERNAME
                        Credentials for master accessing ESX
  --esx-password ESX_PASSWORD
                        Credentials for master accessing ESX
  --esx-hostname ESX_HOSTNAME
                        ESX hostname / IP address
  --esx-port ESX_PORT
  --slave-vm-name SLAVE_VM_NAME
                        Name of ubuntu slave VM to invoke python code in
  --no-verify-cert      Dont verify ESX certificate
  --guest-username GUEST_USERNAME
                        The slave VM guest OS credentials to use for running the egg
  --guest-password GUEST_PASSWORD
                        The slave VM guest OS credentials to use for running the egg
  --egg-folder EGG_FOLDER
                        The egg is the python source code folder to run inside the slaveVM. This arguments is the path to the
                        folder
  --egg-entry-module EGG_ENTRY_MODULE
                        The entry point module of the egg (e.g., `run` if the filename is `run.py`). Will be used in an `import
                        <entry_module>` statement
  --egg-entry-function EGG_ENTRY_FUNCTION
                        The function in the entry point module to execute: <entry module>.<entry function>(**kwargs)
  --egg-kwargs-json EGG_KWARGS_JSON
                        A JSON object for the names arguments to the entry point. Example: --egg-kwargs-
                        json='{"hostname":"1.1.1.1"}'
```

## Integrate POC into a real system

Probable steps:

* Write what you really want in an egg folder
* Install a slave VM on the client's ESX
* ditch the CLI and `main` functions from `main.py`, keep all the rest of the functions
* call the API like main does. For referce, relevant lines below:

```
python_package = pythoninslave.PythonPackage(args.egg_folder, args.egg_entry_module, args.egg_entry_function)
esx_connection = connect(
    esx_hostname=args.esx_hostname,
    esx_username=args.esx_username,
    esx_password=args.esx_password,
    esx_port=args.esx_port,
    verify_cert=not args.no_verify_cert)
esx_content = esx_connection.RetrieveContent()
slave_vm = slavevm.SlaveVM(
    esx_hostname=args.esx_hostname,
    esx_content=esx_content,
    expected_slave_vm_name=args.slave_vm_name,
    username=args.guest_username,
    password=args.guest_password)
output = python_package.run_in_slave(slave_vm=slave_vm, kwargs=kwargs, verify_cert=not args.no_verify_cert)
```

note: if master code does not run one off, but is part of a long living process, make sure to
add bit more fine grain control for calling "disconnect" on the ESX connection after use.

### Using pipenv

`pipenv` is modern `pip`, skip this if you are familiar with it.

Quick getting started to fetch pip dependencies:

```
cd master
sudo pip3 install pipenv
pipenv sync -d
```

### How the Ubuntu slave vm was created:

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

