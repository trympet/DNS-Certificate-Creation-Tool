from certificate_creation import DnsRecord
import re


class CNameRecord(DnsRecord):
    def get_alias(self):
        regex = '^(.*)[.]' + self._zone_name.replace('.', '[.]') + '[.]$'
        return re.search(regex, self.get_fqdn_alias()).group(1)

    def get_fqdn_alias(self):
        return self._record['alias']

    def points_to(self, other: DnsRecord):
        return self.get_alias() == other.get_alias()
