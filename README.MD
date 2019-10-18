# SERVER-DIAGNOSTIC TOOL

This tool is made to gather information for the purpose of fault identification, especially in the servers.

The tool is capable of performing following things:

1. Generating file structure tree.
2. Generating important system information from low-level (cpu, memory, power, etc) up to connectivity information like open ports, public IP address, entire network connection made by the server.

## Sample operational output:

File structure tree:

```bash
/
├── .gitignore
├── app.py
├── LICENSE
├── README.MD
├── sample.json
└── test/
    └── 2019-10-18 15:11:28.702810/
        ├── file_tree.txt
        └── sys_info.json
```

System information:

```json
{
    "name": "Diagnostic results by server-diagnostic tools",
    "developer": "Yuil Tripathee",
    "version": "0.0.1",
    "project": "foldername",
    "location": "folder location",
    "time": "03:11:27 PM",
    "date": "2019-10-18",
    "data": {
        "battery": {
            "ac_plug_in": true,
            "percentage": 97.40082079343365,
            "remaining_time": "Unlimited"
        },
        "memory": {
            "total": "3.7562 GB",
            "available": "0.8199 GB",
            "used": "2.5434 GB",
            "free": "0.1892 GB"
        },
        "cpu": {
            "core": 4,
            "ramUsage": "78.2%",
            "percentage": "41.1%",
            "main_core": 2
        },
        "networks": [
            {
                "key": "lo",
                "address": "127.0.0.1",
                "netmask": "255.0.0.0",
                "broadcast": null
            },
            {
                "key": "eth0",
                "address": "ipv6 address",
                "netmask": null,
                "broadcast": "broadcast"
            }
        ],
        "system": {
            "OS": "Linux",
            "release": "19.0",
            "version": "10",
            "arch": "x86_64",
            "host": "ubuntu",
            "ip_internal": "127.0.xx.xx",
            "mac_address": "xx:xx:xx:xx:xx:xx",
            "cpu": ""
        },
        "interface": {
            "ports_open": [],
            "ip_public": "xxx.xxx.xxx.xxx"
        }
    }
}
```
