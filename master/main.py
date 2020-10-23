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
        esx_port=args.port,
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
parser.add_argument("--esx-username", default="root")
parser.add_argument("--esx-password", required=True)
parser.add_argument("--esx-hostname", default="185.141.60.50")
parser.add_argument("--slave-vm-name", default="esxlocal")
parser.add_argument("--port", type=int, default=443)
parser.add_argument("--no-verify-cert", action="store_true")
parser.add_argument("--guest-username", default="me")
parser.add_argument("--guest-password", default="env0rocks")
parser.add_argument("--egg-folder", default="../slave")
parser.add_argument("--egg-entry-module", default="run")
parser.add_argument("--egg-entry-function", default="run")
parser.add_argument("--egg-kwargs-json", required=True)
args = parser.parse_args()
main(args)
