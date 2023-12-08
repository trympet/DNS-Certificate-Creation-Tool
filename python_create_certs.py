# (c) 2020 by Trym Lund Flogard
# https://github.com/trympet/
# The following code is licensed under MIT license (see LICENSE for details).
# Please read the license issued by The OpenSSL Project and SSLeay as well.

import sys
import os
import subprocess
from certificate_creation import *
from typing import Any, List
from blockstackzones import parse_zone_file
from pathlib import Path

ADD_FQDN_TO_SAN = True
CERTIFICATE_DAYS_VALID = 3650
CERTIFICATE_CONFIG_FORMAT_STRING = """
[req]
default_bits = 2048
prompt = no
default_md = sha256
req_extensions = req_ext
distinguished_name = dn
[dn]
C = {}
ST = {}
L = {}
O = {}
emailAddress = {}
CN = {}
[req_ext]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @SAN
[SAN]
{}
"""
# set vars and args
zone_name = sys.argv[1]
zone_export_path = sys.argv[2]
ip_range_string = sys.argv[3]
certificate_path = sys.argv[4]
private_key_path = sys.argv[5]
certificate_information = {
    'C': sys.argv[10] if len(sys.argv) > 10 else "",
    'ST': sys.argv[9] if len(sys.argv) > 9 else "",
    'L': sys.argv[8] if len(sys.argv) > 8 else "",
    'O': sys.argv[7] if len(sys.argv) > 7 else "",
    'E': sys.argv[6] if len(sys.argv) > 6 else ""
}

certificate_password = input("Certificate password: ")


def get_zone_data(file_path):
    content = ""
    with open(file_path, "r") as f:
        content = f.read()
    return parse_zone_file(content)


def process_a_records(data, ip_filter) -> List[ARecord]:
    records = data['a']
    processed: dict[str, ARecord] = {}
    for r in records:
        record = ARecord(r, zone_name)
        if (record.is_root() or not record.in_subnet(ip_filter)):
            continue

        if (record.get_ip() in processed):
            processed[record.get_ip()].add_alias(record)
        else:
            processed[record.get_ip()] = record

    return list(processed.values())


def process_cname_records(data, a_records: List[ARecord]) -> List[DnsRecord]:
    records = data["cname"]
    for r in records:
        record = CNameRecord(r, zone_name)
        a_record = [a for a in a_records if record.points_to(a)]
        if (a_record):
            a_record[0].add_alias(record)
    return a_records


def create_pem(path: Path):
    pem = ""
    with open(f"{path}/certificate.crt", "r") as cert:
        pem += cert.read()
    with open(f"{path}/certificate.key", "r") as key:
        pem += key.read()
    with open(f"{path}/certificate.pem", "w") as out:
        out.write(pem)


def openssl_create(base_path: Path, config_path: Path, cert_path, cert_key_path, days, password):
    # key
    openssl = Path("./openssl/openssl")
    private_key = Path(f"{base_path}/certificate.key")
    csr = Path(f"{base_path}/request.csr")
    cert = Path(f"{base_path}/certificate.crt")
    print("Creating private key")
    subprocess.Popen(f"{openssl} genrsa -out {private_key} 2048").wait()
    # csr
    print("Creating CSR")
    subprocess.Popen(f"{openssl} req -new -key {private_key} "
                     f"-out {csr} -config {config_path}").wait()
    # crt
    print("Creating certificate")
    subprocess.Popen(f"{openssl} x509 -req -in {csr} "
                     f"-CA {cert_path} -CAkey {cert_key_path} -CAcreateserial "
                     f"-out {cert} -days {days} -sha256 "
                     f"-extfile {config_path} "
                     f"-extensions req_ext -passin pass:{password}").wait()
    create_pem(base_path)


def get_certificate_create_config(record: DnsRecord, san_config):
    return CERTIFICATE_CONFIG_FORMAT_STRING.format(
        certificate_information['C'],
        certificate_information['ST'],
        certificate_information['L'],
        certificate_information['O'],
        certificate_information['E'],
        record.get_ip(),
        san_config)


def get_subject_alt_name_config(record: DnsRecord) -> str:
    result = ""
    if (record.alias_count() > 1 or ADD_FQDN_TO_SAN):
        alias_index = 1
        for alias in record.get_aliases():
            result += f"DNS.{alias_index} = {alias}\n"
            alias_index += 1
            if ADD_FQDN_TO_SAN:
                result += f"DNS.{alias_index} = {alias}.{zone_name}\n"
                alias_index += 1
    else:
        result += f"DNS = {record.get_aliases()[0]}\n"
    return result


def create_certificate(record: DnsRecord):
    san_config = get_subject_alt_name_config(record)
    cert_config = get_certificate_create_config(record, san_config)
    path = Path(f"./out/{record.get_ip()}")
    path.mkdir(exist_ok=True, parents=True)
    config_path = Path(f"{path}/certificate_config.cfg")
    with open(config_path, "w") as out:
        out.write(cert_config)
    openssl_create(path, config_path, certificate_path, private_key_path,
                   CERTIFICATE_DAYS_VALID, certificate_password)


def configure_openssl():
    pwd = os.path.dirname(os.path.realpath(__file__))
    os.environ['RANDFILE'] = f"{pwd}\\.rnd"
    os.environ['OPENSSL_CONF'] = f"{pwd}\\openssl\\openssl.cfg"


def create_certificates(records: List[DnsRecord]):
    print("======== STARTING OPENSSL CERTIFICATE GENERATION ========")
    configure_openssl()
    progress = 1
    for record in records:
        if record.any_alias():
            print(
                f"\n\n======== Creating certificate ({progress}/{len(records)}) for {record.get_alias()} ========")
            create_certificate(record)
        else:
            print(
                f"\n\n======== Skipping {record.get_ip()}. No aliases found. ========")
        progress += 1

    if os.path.exists(".rnd"):
        os.remove(".rnd")
    print("======== OPENSSL CERTIFICATE GENERATION FINISHED ========")


zone_data = get_zone_data(zone_export_path)
ip_filter = ip_network(ip_range_string, False)
a_records = process_a_records(zone_data, ip_filter)
records = process_cname_records(zone_data, a_records)
create_certificates(records)
