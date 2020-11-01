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
    if args.cmd == "clone":
        logging.info("Cloning VM")
        slave_vm = slavevm.SlaveVM(
            esx_hostname=args.esx_hostname,
            esx_port=args.esx_port,
            esx_connection=esx_connection,
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
            esx_port=args.esx_port,
            esx_connection=esx_connection,
            expected_slave_vm_name=args.clone_name,
            username=args.clone_username,
            password=args.clone_password)
        clone_slave_vm.wait_for_vm_tools_to_be_installed()
        logging.info("VM tools are online, VM cloned successfully")
    elif args.cmd == "bash":
        clone_slave_vm = slavevm.SlaveVM(
            esx_hostname=args.esx_hostname,
            esx_port=args.esx_port,
            esx_connection=esx_connection,
            expected_slave_vm_name=args.clone_name,
            username=args.clone_username,
            password=args.clone_password)
        clone_slave_vm.wait_for_vm_tools_to_be_installed()
        logging.info("VM tools are online, running script")
        output = bashinslave.execute_bash_script_in_slave_vm(
            clone_slave_vm, args.bash_script, verify_cert=not args.no_verify_cert)
        print("Output:")
        print(output)
    elif args.cmd == "run":
        clone_slave_vm = slavevm.SlaveVM(
            esx_hostname=args.esx_hostname,
            esx_port=args.esx_port,
            esx_connection=esx_connection,
            expected_slave_vm_name=args.clone_name,
            username=args.clone_username,
            password=args.clone_password)
        clone_slave_vm.wait_for_vm_tools_to_be_installed()
        logging.info("VM tools are online, running script")
        pid = clone_slave_vm.spawn_process_in_slave(args.executable, args.arguments)
        logging.info("Executable spawned. PID: %s. Waiting...", pid)
        exitcode = clone_slave_vm.wait_for_process_to_finish(pid=pid)
        logging.info("Executable finished with exitcode: %s", exitcode)
        if exitcode != 0:
            raise Exception("Failed, process exited with code %s", exitcode)
    elif args.cmd == "destroy":
        clone_slave_vm = slavevm.SlaveVM(
            esx_hostname=args.esx_hostname,
            esx_port=args.esx_port,
            esx_connection=esx_connection,
            expected_slave_vm_name=args.clone_name,
            username=args.clone_username,
            password=args.clone_password)
        clone_slave_vm.destroy()
    else:
        raise AssertionError(f"Unknown command {args.cmd}")


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


logging.basicConfig(level=logging.INFO)
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
subparsers = parser.add_subparsers(dest="cmd")
clone_cmd = subparsers.add_parser(
    "clone",
    help="Clone a VM and power on the clone")
clone_cmd.add_argument(
    "--cloner-vm-name",
    default="esxlocal",
    help="Name of ubuntu slave VM to use for cloning a VM (in ESX due to vCenter not being available)")
clone_cmd.add_argument(
    "--cloner-username",
    default="me",
    help="Cloner slave VM guest OS credentials to use for running ovftool")
clone_cmd.add_argument(
    "--cloner-password",
    default="env0rocks",
    help="Cloner slave VM guest OS credentials to use for running ovftool")
clone_cmd.add_argument(
    "--cloner-esx-username",
    default="root",
    help="Credentials for cloner accessing ESX (via ovftool)")
clone_cmd.add_argument(
    "--cloner-esx-password",
    required=True,
    help="Credentials for cloner accessing ESX (via ovftool)")
clone_cmd.add_argument(
    "--cloner-esx-hostname",
    default="185.141.60.50",
    help="ESX hostname / IP address from within the cloner (for ovftool)")
clone_cmd.add_argument("--cloner-esx-port", type=int, default=443)
clone_cmd.add_argument(
    "--vm-to-clone",
    default="to_clone",
    help="Name of VM to clone")
bash_cmd = subparsers.add_parser(
    "bash",
    help="Run a bash script inside a clone VM (linux guest only)")
bash_cmd.add_argument(
    "bash_script",
    help="contents of the bash script to execute")
run_cmd = subparsers.add_parser(
    "run",
    help="Run a program on clone VM (windows and linux guests compatible)")
run_cmd.add_argument(
    "executable",
    help="full path to an executable to run")
run_cmd.add_argument(
    "arguments",
    help="string of arguments to execute said executable with")
destroy_cmd = subparsers.add_parser(
    "destroy",
    help="Destroy the cloned VM")
args = parser.parse_args()
main(args)
