import argparse
import atexit
import logging
import json
import pprint
import pyVim.connect
import slavevm
import pythoninslave


def main(args):
    kwargs = json.loads(args.egg_kwargs_json)
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
    print("Output:")
    pprint.pprint(output)
    # lower level API:
    # output = bashinslave.execute_bash_script_in_slave_vm(slave_vm, "echo hello\ndate\n", verify_cert=not args.no_verify_cert)
    # pid = slave_vm.spawn_process_in_slave(
    #     executable_path="/bin/date",
    #     arguments="")
    # slave_vm.wait_for_process_to_finish(pid)
    # slave_vm.put_file("/tmp/pash", b"yuvu", verify_cert=False)
    # contents = slave_vm.get_file("/tmp/pash", verify_cert=False)

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
    "--slave-vm-name",
    default="esxlocal",
    help="Name of ubuntu slave VM to invoke python code in")
parser.add_argument(
    "--no-verify-cert",
    action="store_true",
    help="Dont verify ESX certificate")
parser.add_argument(
    "--guest-username",
    default="me",
    help="The slave VM guest OS credentials to use for running the egg")
parser.add_argument(
    "--guest-password",
    default="env0rocks",
    help="The slave VM guest OS credentials to use for running the egg")
parser.add_argument(
    "--egg-folder",
    default="../slave",
    help=("The egg is the python source code folder to run inside the slaveVM. "
          "This arguments is the path to the folder"))
parser.add_argument(
    "--egg-entry-module",
    default="run",
    help="The entry point module of the egg (e.g., `run` if the filename is `run.py`). Will be used in an `import <entry_module>` statement")
parser.add_argument(
    "--egg-entry-function",
    default="run",
    help="The function in the entry point module to execute: <entry module>.<entry function>(**kwargs)")
parser.add_argument(
    "--egg-kwargs-json",
    required=True,
    help="""A JSON object for the names arguments to the entry point. Example: --egg-kwargs-json='{"hostname":"1.1.1.1"}'""")
args = parser.parse_args()
main(args)
