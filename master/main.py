import argparse
import atexit
import logging
import json
import pprint
import pyVim.connect
import slavevm
import bashinslave


def main(args):
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
        expected_slave_vm_name=args.cloner_vm_name,
        username=args.cloner_username,
        password=args.cloner_password)
    slave_vm.verify_vm_tools_are_installed()
    logging.info("Cloning VM")
    script = _CLONING_SCRIPT % dict(
        username=args.cloner_esx_username,
        password=args.cloner_esx_password,
        hostname=args.cloner_esx_hostname,
        port=args.cloner_esx_port,
        to_clone_vm_name=args.vm_to_clone,
        new_clone_vm_name=args.clone_name)
    bashinslave.execute_bash_script_in_slave_vm(
        slave_vm, script, verify_cert=not args.no_verify_cert, interval=1, timeout=600)
    logging.info("VM Cloned successfully, waiting to be able to run on it...")
    clone_slave_vm = slavevm.SlaveVM(
        esx_hostname=args.esx_hostname,
        esx_content=esx_content,
        expected_slave_vm_name=args.clone_name,
        username=args.clone_username,
        password=args.clone_password)
    clone_slave_vm.wait_for_vm_tools_to_be_installed()
    logging.info("VM tools are online")
    bashinslave.wait_for_slave_vm_to_wake_up(clone_slave_vm, verify_cert=not args.no_verify_cert)
    logging.info("VM Cloned successfully, woke up successfully")
    output = bashinslave.execute_bash_script_in_slave_vm(
        clone_slave_vm, "ls /", verify_cert=not args.no_verify_cert)
    print("Output:")
    print(output)
    # lower level API:
    # output = bashinslave.execute_bash_script_in_slave_vm(slave_vm, "echo hello\ndate\n", verify_cert=not args.no_verify_cert)
    # pid = slave_vm.spawn_process_in_slave(
    #     executable_path="/bin/date",
    #     arguments="")
    # slave_vm.wait_for_process_to_finish(pid)
    # slave_vm.put_file("/tmp/pash", b"yuvu", verify_cert=False)
    # contents = slave_vm.get_file("/tmp/pash", verify_cert=False)


_CLONING_SCRIPT = """
set -x
set -e
cd /tmp
rm -fr clone*
ovftool vi://%(username)s:%(password)s@%(hostname)s:%(port)d/%(to_clone_vm_name)s clone.ova
ovftool --powerOn --name=%(new_clone_vm_name)s clone.ova vi://%(username)s:%(password)s@%(hostname)s:%(port)d/
rm -fr clone*
"""


def connect(esx_hostname, esx_username, esx_password, esx_port, verify_cert):
    connection_method = pyVim.connect.SmartConnect if verify_cert else pyVim.connect.SmartConnectNoSSL
    connection = connection_method(
        host=esx_hostname,
        user=esx_username,
        pwd=esx_password,
        port=esx_port)
    atexit.register(pyVim.connect.Disconnect, connection)
    logging.info("Successfully connected to ESX")
    return connection


logging.basicConfig(level=logging.DEBUG)
parser = argparse.ArgumentParser()
parser.add_argument(
    "--esx-username",
    default="root",
    help="Credentials for master accessing ESX")
parser.add_argument(
    "--esx-password",
    required=True,
    help="Credentials for master accessing ESX")
parser.add_argument(
    "--esx-hostname",
    default="185.141.60.50",
    help="ESX hostname / IP address")
parser.add_argument("--esx-port", type=int, default=443)
parser.add_argument(
    "--no-verify-cert",
    action="store_true",
    help="Dont verify ESX certificate")
parser.add_argument(
    "--cloner-vm-name",
    default="esxlocal",
    help="Name of ubuntu slave VM to use for cloning a VM (in ESX due to vCenter not being available)")
parser.add_argument(
    "--cloner-username",
    default="me",
    help="Cloner slave VM guest OS credentials to use for running ovftool")
parser.add_argument(
    "--cloner-password",
    default="env0rocks",
    help="Cloner slave VM guest OS credentials to use for running ovftool")
parser.add_argument(
    "--cloner-esx-username",
    default="root",
    help="Credentials for cloner accessing ESX (via ovftool)")
parser.add_argument(
    "--cloner-esx-password",
    required=True,
    help="Credentials for cloner accessing ESX (via ovftool)")
parser.add_argument(
    "--cloner-esx-hostname",
    default="185.141.60.50",
    help="ESX hostname / IP address from within the cloner (for ovftool)")
parser.add_argument("--cloner-esx-port", type=int, default=443)
parser.add_argument(
    "--vm-to-clone",
    default="to_clone",
    help="Name of VM to clone")
parser.add_argument(
    "--clone-name",
    default="clone",
    help="Name of the newly created cloned VM")
parser.add_argument(
    "--clone-username",
    default="me",
    help="Clone slave VM guest OS credentials to use for running final script")
parser.add_argument(
    "--clone-password",
    default="env0rocks",
    help="Clone slave VM guest OS credentials to use for running final script")
args = parser.parse_args()
main(args)
