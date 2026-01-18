import socket
from python_hosts import Hosts, HostsEntry

TARGET_DOMAIN = "webcast5-mate-lf.amemv.com"


class hostmgr:
    def __init__(self):
        self.hosts = Hosts()
        self.real_ip = None

    def resolve_real_ip(self):
        self.real_ip = socket.gethostbyname(TARGET_DOMAIN)
        return self.real_ip

    def apply(self):
        if not self.real_ip:
            self.resolve_real_ip()
        self.remove()
        entry = HostsEntry(
            entry_type="ipv4",
            address="127.0.0.1",
            names=[TARGET_DOMAIN],
        )
        self.hosts.add([entry])
        self.hosts.write()

    def remove(self):
        changed = False
        for entry in list(self.hosts.entries):
            if entry.names and TARGET_DOMAIN in entry.names:
                self.hosts.entries.remove(entry)
                changed = True
        if changed:
            self.hosts.write()
