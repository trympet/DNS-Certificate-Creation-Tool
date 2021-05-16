from certificate_creation import DnsRecord
from ipaddress import IPv4Network, ip_network


class ARecord(DnsRecord):
    def __init__(self, record, zone_name: str):
        DnsRecord.__init__(self, record, zone_name)
        self._ip: IPv4Network = ip_network(f"{record['ip']}/32")

    def __eq__(self, other):
        if (isinstance(other, DnsRecord)):
            return self._ip == other._ip
        return False

    def get_ip(self) -> str:
        return self._record['ip']

    def in_subnet(self, ip_network) -> bool:
        return self._ip.subnet_of(ip_network)
