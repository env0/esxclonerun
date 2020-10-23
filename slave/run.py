import atexit
import pyVim.connect
import pyVmomi


def run(esx_hostname, esx_username, esx_password, esx_port=443):
    esx_connection = pyVim.connect.SmartConnectNoSSL(
        host=esx_hostname,
        user=esx_username,
        pwd=esx_password,
        port=esx_port)
    atexit.register(pyVim.connect.Disconnect, esx_connection)
    esx_content = esx_connection.RetrieveContent()
    children = esx_content.rootFolder.childEntity
    result = []
    for child in children:
        if not hasattr(child, 'vmFolder'):
            continue
        vm_list = child.vmFolder.childEntity
        for vm in vm_list:
            print("Found VM:", vm.name)
            result.append(vm.name)
    return result
