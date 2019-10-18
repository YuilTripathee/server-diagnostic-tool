import os
import optparse
import json
import datetime
import psutil
import socket
import platform
import uuid
import re
from multiprocessing import cpu_count
from requests import get
from pathlib import Path
from termcolor import colored
# initiating cross platform terminal coloring
import colorama
colorama.init()

# returns thank you message


def msg_farewell():
    print("\n################################")
    print("#       Thanks for using       #")
    print("#    Server Diagnostics Tool   #")
    print("#        -Yuil Tripathee-      #")
    print("################################")


# class for Displayable Path
class DisplayablePath(object):
    display_filename_prefix_middle = '├──'
    display_filename_prefix_last = '└──'
    display_parent_prefix_middle = '    '
    display_parent_prefix_last = '│   '

    def __init__(self, path, parent_path, is_last):
        self.path = Path(str(path))
        self.parent = parent_path
        self.is_last = is_last
        if self.parent:
            self.depth = self.parent.depth + 1
        else:
            self.depth = 0

    @property
    def displayname(self):
        if self.path.is_dir():
            return self.path.name + '/'
        return self.path.name

    @classmethod
    def make_tree(cls, root, gitTree=True, parent=None, is_last=False, criteria=None):
        root = Path(str(root))
        criteria = criteria or cls._default_criteria

        displayable_root = cls(root, parent, is_last)
        yield displayable_root

        if not gitTree:
            children = sorted(list(path
                                   for path in root.iterdir()
                                   if criteria(path) and path.stem != '.git'),
                              key=lambda s: str(s).lower())
        else:
            children = sorted(list(path
                                   for path in root.iterdir()
                                   if criteria(path)),
                              key=lambda s: str(s).lower())

        count = 1

        for path in children:
            is_last = count == len(children)
            if path.is_dir():
                yield from cls.make_tree(path,
                                         parent=displayable_root,
                                         is_last=is_last,
                                         criteria=criteria)
            else:
                yield cls(path, displayable_root, is_last)
            count += 1

    @classmethod
    def _default_criteria(cls, path):
        return True

    def displayable(self):
        if self.parent is None:
            return self.displayname

        _filename_prefix = (self.display_filename_prefix_last
                            if self.is_last
                            else self.display_filename_prefix_middle)

        parts = ['{!s} {!s}'.format(_filename_prefix,
                                    self.displayname)]

        parent = self.parent
        while parent and parent.parent is not None:
            parts.append(self.display_parent_prefix_middle
                         if parent.is_last
                         else self.display_parent_prefix_last)
            parent = parent.parent

        return ''.join(reversed(parts))


def secs2hours(secs):
    mm, ss = divmod(secs, 60)
    hh, mm = divmod(mm, 60)
    return "%d:%02d:%02d (H:M:S)" % (hh, mm, ss)

# checks if the port in system is active for listening


def check_port(port, rais=True):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', port))
        sock.listen(5)
        sock.close()
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.bind(('::1', port))
        sock.listen(5)
        sock.close()
    except socket.error:
        if rais:
            raise RuntimeError(
                "The server is already running on port {0}".format(port))
        return True
    return False


def getTimeInfo():
    print('Gathering system date and time')
    time = datetime.datetime.now().strftime("%I:%M:%S %p")
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    return time, date


def getBatteryInfo():
    print('Gathering battery information...')
    batt = psutil.sensors_battery()
    if batt is None:
        print(colored("no battery installed", 'red'))
        return None, None, None

    if not batt.power_plugged:
        batt_left = secs2hours(batt.secsleft)
    else:
        batt_left = 'Unlimited'

    return batt.power_plugged, batt.percent, batt_left


def getMemoryInfo():
    print('Gathering memory information')
    totalRAM = 1.0
    totalRAM = psutil.virtual_memory()[0] * totalRAM
    totalRAM = str("{:.4f}".format(totalRAM / (1024 * 1024 * 1024))) + ' GB'

    avalRAM = 1.0
    avalRAM = psutil.virtual_memory()[1] * avalRAM
    avalRAM = str("{:.4f}".format(avalRAM / (1024 * 1024 * 1024))) + ' GB'

    usedRAM = 1.0
    usedRAM = psutil.virtual_memory()[3] * usedRAM
    usedRAM = str("{:.4f}".format(usedRAM / (1024 * 1024 * 1024))) + ' GB'

    freeRAM = 1.0
    freeRAM = psutil.virtual_memory()[4] * freeRAM
    freeRAM = str("{:.4f}".format(freeRAM / (1024 * 1024 * 1024))) + ' GB'

    return totalRAM, avalRAM, usedRAM, freeRAM


def getCPUInfo():
    print('Gathering CPU information...')
    core = cpu_count()
    ramUsages = str(psutil.virtual_memory()[2]) + '%'
    cpuPer = str(psutil.cpu_percent()) + '%'
    cpuMainCore = psutil.cpu_count(logical=False)

    return core, ramUsages, cpuPer, cpuMainCore


def getNetworkInfo():
    print('Gathering networking information...')
    networkInfoObj = psutil.net_if_addrs()
    indices = socket.if_nameindex()
    networkInfo = []
    for index in indices:
        networkAddr = {}
        key = index[1]
        networkAddr['key'] = key
        networkAddr['address'] = networkInfoObj[key][0][1]
        networkAddr['netmask'] = networkInfoObj[key][0][2]
        networkAddr['broadcast'] = networkInfoObj[key][0][3]

        networkInfo.append(networkAddr)
    return networkInfo


def getInterfaceInfo():
    print('Gathering interfacing information...')
    print("Checking for open ports in this machine.")
    ports_open = []
    for i in range(1024, 10000):
        if check_port(i, rais=False):
            ports_open.append(i)
    # public IP address
    print('Determining public IPv4 address...')
    try:
        ip = get('https://api.ipify.org').text
    except Exception:
        print(colored('Public IP unavailable!', 'red'))
        ip = 'unavailable'
    return ports_open, ip


def getSystemInfo():
    print('Gathering platform information...')
    platform_OS = platform.system()
    platform_release = platform.release()
    platform_version = platform.version()
    platform_arch = platform.machine()
    platform_hostname = socket.gethostname()
    platform_ip = socket.gethostbyname(socket.gethostname())
    platform_mac = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
    platform_cpu = platform.processor()
    if platform_cpu == '':
        print(colored('CPU info unavailable!'))
    return platform_OS, platform_release, platform_version, platform_arch, platform_hostname, platform_ip, platform_mac, platform_cpu


def getTargetDIRInfo():
    return os.getcwd()


def diagnose_file(treeType):
    print("Starting file diagnosis...\n")
    if treeType is None:
        treeType = 'min'

    if treeType == 'full':
        gitTree = True
    else:
        gitTree = False
    print("Selected tree type\t:" + colored(treeType, 'cyan'))
    print("File structure for\t:" + colored(getTargetDIRInfo(), 'cyan') + "\n")
    # gitTree excludes git directory
    paths = DisplayablePath.make_tree(Path('.'), gitTree=gitTree)
    path_string = ''''''
    for path in paths:
        path_string += path.displayable() + '\n'
    # with open('output_tree.txt', 'w', encoding='utf-8') as fp:
    #     fp.write(path_string)
    #     fp.close()
    print("Directory tree diagnosis report completed sucessfully!\n")
    return path_string



def diagnose_sys():
    print("Starting system diagnostics...\n")
    # getting information
    timeData = getTimeInfo()
    batteryData = getBatteryInfo()
    memoryData = getMemoryInfo()
    cpuData = getCPUInfo()
    networkData = getNetworkInfo()
    systemData = getSystemInfo()
    interfaceData = getInterfaceInfo()
    dirData = getTargetDIRInfo()
    targetDir = dirData.split('/')[-1]

    # diagnostics result
    result = {}
    result['name'] = "Diagnostic results by server-diagnostic tools"
    result['developer'] = 'Yuil Tripathee'
    result['version'] = '0.0.1'

    print("\nGenerating report")
    print("=================\n")
    print('\nBasic Information')
    # gathering folder name and location
    print('Project\t:' + colored(targetDir, 'cyan'))
    print('Address\t:' + colored(dirData, 'cyan'))
    result['project'] = targetDir
    result['location'] = dirData
    # gathering date and time results
    result['time'] = timeData[0]
    result['date'] = timeData[1]
    print('Time\t:' + colored(timeData[0], 'cyan'))
    print('Date\t:' + colored(timeData[1], 'cyan'))

    # starting to gather vital system details
    result['data'] = {}  # target where all info are to be recorded
    display_sys_info = lambda info: colored(json.dumps(info, indent=4), 'cyan')
    # gathering battery info
    batteryInfo = {}
    batteryInfo['ac_plug_in'] = batteryData[0]
    batteryInfo['percentage'] = batteryData[1]
    batteryInfo['remaining_time'] = batteryData[2]
    print('Battery\t:' + display_sys_info(batteryInfo))
    result['data']['battery'] = batteryInfo
    # gathering memory info
    memInfo = {}
    memInfo['total'] = memoryData[0]
    memInfo['available'] = memoryData[1]
    memInfo['used'] = memoryData[2]
    memInfo['free'] = memoryData[3]
    print('Memory\t:' + display_sys_info(memInfo))
    result['data']['memory'] = memInfo
    # gathering CPU info
    cpuInfo = {}
    cpuInfo['core'] = cpuData[0]
    cpuInfo['ramUsage'] = cpuData[1]
    cpuInfo['percentage'] = cpuData[2]
    cpuInfo['main_core'] = cpuData[3]
    print('CPU\t:' + display_sys_info(cpuInfo))
    result['data']['cpu'] = cpuInfo
    # gathering network information
    print('Network\t:' + display_sys_info(networkData))
    result['data']['networks'] = networkData
    # gathering system info
    sysInfo = {}
    sysInfo['OS'] = systemData[0]
    sysInfo['release'] = systemData[1]
    sysInfo['version'] = systemData[2]
    sysInfo['arch'] = systemData[3]
    sysInfo['host'] = systemData[4]
    sysInfo['host_ip'] = systemData[5]
    sysInfo['mac_address'] = systemData[6]
    sysInfo['cpu'] = systemData[7]
    print('System\t:' + display_sys_info(sysInfo))
    result['data']['system'] = sysInfo
    # gathering connectivity info
    interInfo = {}
    interInfo['ports_open'] = interfaceData[0]
    interInfo['ip_public'] = interfaceData[1]
    print('Interface\t:' + display_sys_info(interInfo))
    result['data']['interface'] = interInfo

    print('System diagnosics operation completed sucessfully!')
    return result


def start_diagnosis(treeType):
    print("Starting diagnosis...\n")
    
    # file diagnosis
    file_diagnostic_report = diagnose_file(treeType)
    print(file_diagnostic_report)
    # system diagnostics
    sys_diagnostic_report = diagnose_sys()
    
    # saving generated reports
    target_folder_name = 'test/' + str(datetime.datetime.now()) + '/'
    if not os.path.exists(target_folder_name):
        os.makedirs(target_folder_name)
        
    # saving tree structure
    output_file = target_folder_name + 'file_tree.txt'
    with open(output_file, 'w+', encoding='utf-8') as fp:
        fp.write(file_diagnostic_report)
        fp.close()

    # saving system diagnostics report
    output_file = target_folder_name + 'sys_info.json'
    with open(output_file, 'w+', encoding='utf-8') as fp:
        json.dump(sys_diagnostic_report, fp, indent=4)
        fp.close()

    print("\nDiagnostic operation completed sucessfully!")
    msg_farewell()


if __name__ == "__main__":
    print("\n" + __file__ + "\n")

    parser = optparse.OptionParser(
        'python3 app.py ' + '-t <tree type> -h')
    parser.add_option('-t', dest='tree_type', type='string',
                      help='Specify file structure tree type (for example: "min" (default - without .git/ directory tree) for file structure tree and "full" for extended one)')
    (options, args) = parser.parse_args()
    tree_type = options.tree_type

    start_diagnosis(treeType=tree_type)
