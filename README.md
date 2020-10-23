

### a possible way to create private routing:

define a private vlan / new vswitch for a new private network interface for the esxlocal VM and a new vmk.
private a in 192.168.x.x

### How the Ubuntu slave vm was created:

* used iso from storage for ubuntu 20.04.1
* username: me password: env0rocks
* no ssh, whole disk (16GB) formatting, static ip address
* sudo apt-get update ; sudo apt-get install unattended-upgrades ; sudo apt-get install python3-pip
* sudo pip3 install pyvmomi
