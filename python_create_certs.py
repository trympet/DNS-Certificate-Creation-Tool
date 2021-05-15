# (c) 2020 by Trym Lund Flogard
# https://github.com/trympet/
# The following code is licensed under MIT license (see LICENSE for details).
# Please read the license issued by The OpenSSL Project and SSLeay as well.

import pprint
import sys
import re
import os
from ipaddress import ip_network
from blockstackzones import parse_zone_file
from pathlib import Path

ADD_SUFFIX_TO_SAN = True
CERTIFICATE_DAYS_VALID = 720
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

# openssl env variables
pwd = os.path.dirname(os.path.realpath(__file__))

def configure_openssl():
  os.environ['RANDFILE'] = f"{pwd}\\.rnd"
  os.environ['OPENSSL_CONF'] = f"{pwd}\\openssl\\openssl.cfg"

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

certificate_key = input("Root CA KEY: ")
ip_range = ip_network(ip_range_string, False)

zone_file_content = open(zone_export_path, "r").read()
zone_file_parsed = parse_zone_file(zone_file_content)

ip_aliases = {}


a_records = zone_file_parsed['a']
subnet_ips = []
for record in a_records:
  record_name = record['name']
  if (record['name'] != "@"):
    ip = record['ip']
    addr = ip_network(ip + "/32")
    if (addr.subnet_of(ip_range)):
      if (addr in subnet_ips):
        # ip is already in list. Add record name instead
        if (record_name not in ip_aliases[ip]):
          # no duplicates
          ip_aliases[ip].append(record_name)
      else:
        # ip is not in list. Add ip and record to list
        subnet_ips.append(addr)
        ip_aliases[ip] = [record_name]
        ip_aliases[ip].append(ip)

# associate cname with ip
cname_records = zone_file_parsed['cname']
for cName in cname_records:
  name = cName['name']
  alias = cName['alias'] 
  regex = '^(.*)[.]' + zone_name.replace('.', '[.]') + '[.]$'
  non_fqdn_alias = re.search(regex, alias).group(1)
  for ip in dict(ip_aliases):
    if (non_fqdn_alias in ip_aliases[ip]):
       ip_aliases[ip].append(name)

# output directory
Path("out").mkdir(exist_ok=True)

i = 0
# generate cert
print("======== STARTING OPENSSL CERTIFICATE GENERATION ========")
configure_openssl()
for ip in dict(ip_aliases):
  i=i+1
  print("\n\n======== Creating certificate ({}/{}) for {} ========".format(str(i), len(ip_aliases), ip))
  ip_aliases_2 = ip_aliases[ip]
  if len(ip_aliases_2) != 0:
    # set appropriate subjectAltName
    subject_alt_name_config = ""
    if len(ip_aliases_2) > 1:
      j = 1
      for alias in ip_aliases_2:
        subject_alt_name_config += "DNS." + str(j) + " = " + alias + "\n"
        j=j+1
        if (ADD_SUFFIX_TO_SAN):
          subject_alt_name_config += "DNS." + str(j) + " = " + alias + "." + zone_name + "\n"
          j=j+1
    else:
      if (ADD_SUFFIX_TO_SAN):
        subject_alt_name_config += "DNS.1 = " + ip_aliases_2[0] + "\n"
        subject_alt_name_config += "DNS.2 = " + ip_aliases_2[0] + "." + zone_name
      else:
        subject_alt_name_config += "DNS = " + ip_aliases_2[0]

    print("\nSAN: " + subject_alt_name_config + "\n")
    # generate the config file for the certificate
    config = CERTIFICATE_CONFIG_FORMAT_STRING.format(
      certificate_information['C'],
      certificate_information['ST'],
      certificate_information['L'],
      certificate_information['O'],
      certificate_information['E'],
      ip,
      subject_alt_name_config)

    # directory for host
    Path("out\\{}".format(ip)).mkdir(exist_ok=True)

    # conf
    with open("out\\{}\\{}.cfg".format(ip,ip), "w") as out:
      out.write(config)
    # key
    os.system("openssl\\openssl genrsa -out out\\{}\\{}.key 2048".format(ip,ip))
    # csr
    os.system("openssl\\openssl req -new -key out\\{}\\{}.key -out out\\{}\\{}.csr -config out\\{}\\{}.cfg".format(ip,ip,ip,ip,ip,ip))
    # crt
    os.system("openssl\\openssl x509 -req -in out\\{}\\{}.csr -CA {} -CAkey {} -CAcreateserial -out out\\{}\\{}.crt -days {} -sha256 -extfile out\\{}\\{}.cfg -extensions req_ext -passin pass:{}".format(ip,ip,certificate_path,private_key_path,ip,ip,CERTIFICATE_DAYS_VALID,ip,ip,certificate_key))
    pem = open("out\\{}\\{}.crt".format(ip,ip), "r").read() + open("out\\{}\\{}.key".format(ip,ip), "r").read() 
    with open("out\\{}\\{}.pem".format(ip,ip), "w") as out:
      out.write(pem)
print("======== OPENSSL CERTIFICATE GENERATION FINISHED ========")
print("\n\nFinished! Your certificates are located in the out/ directory.")
if os.path.exists(".rnd"): os.remove(".rnd") 
exit(0)