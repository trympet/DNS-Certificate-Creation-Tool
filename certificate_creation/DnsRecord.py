
class DnsRecord:
    def __init__(self, record, zone_name: str):
        self._record = record
        self._zone_name = zone_name
        self._aliases = [self.get_alias()]

    def is_root(self):
        return self._record["name"] == "@"

    def get_alias(self) -> str:
        return self._record["name"]

    def get_aliases(self):
        return self._aliases

    def add_alias(self, other):
        self._aliases.append(other.get_alias())

    def any_alias(self) -> bool:
        return len(self._aliases) > 0

    def alias_count(self) -> int:
        return len(self._aliases)
