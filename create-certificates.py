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

# openssl env variables
pwd = os.path.dirname(os.path.realpath(__file__))
os.environ['RANDFILE'] = pwd + "\\.rnd"
os.environ['OPENSSL_CONF'] = pwd + "\\openssl\\openssl.cfg"

# set vars and args
dnsZoneName = sys.argv[1]
dnsExportFileName = sys.argv[2]
ipRangeString = sys.argv[3]
rootCA = sys.argv[4]
rootCAKey = sys.argv[5]
CERTIFICATE_DAYS_VALID = 720
openSSLConf = {
  'C': sys.argv[10] if len(sys.argv) > 10 else "",
  'ST': sys.argv[9] if len(sys.argv) > 9 else "",
  'L': sys.argv[8] if len(sys.argv) > 8 else "",
  'O': sys.argv[7] if len(sys.argv) > 7 else "",
  'E': sys.argv[6] if len(sys.argv) > 6 else ""
}

rootCAPW = input("Root CA KEY: ")
ipRangeParsed = ip_network(ipRangeString, False)

zoneFile = open(dnsExportFileName, "r").read()
zoneParsed = parse_zone_file(zoneFile)

ipHasNames = {}

aRecords = zoneParsed['a']

ipsInSubnet = []
for record in aRecords:
  recordName = record['name']
  if (record['name'] != "@"):
    ip = record['ip']
    addr = ip_network(ip + "/32")
    if (addr.subnet_of(ipRangeParsed)):
      if (addr in ipsInSubnet):
        # ip is already in list. Add record name instead
        if (recordName not in ipHasNames[ip]):
          # no duplicates
          ipHasNames[ip].append(recordName)
      else:
        # ip is not in list. Add ip and record to list
        ipsInSubnet.append(addr)
        ipHasNames[ip] = [recordName]

cNames = zoneParsed['cname']

# associate cname with ip
for cName in cNames:
  name = cName['name']
  alias = cName['alias'] 
  regex = '^(.*)[.]' + dnsZoneName.replace('.', '[.]') + '[.]$'
  aliasNonFQDN = re.search(regex, alias).group(1)
  for ip in dict(ipHasNames):
    nameList = ipHasNames[ip]
    if (aliasNonFQDN in nameList):
      nameList.append(name)

# output directory
Path("out").mkdir(exist_ok=True)

i = 0
# generate cert
print("======== STARTING OPENSSL CERTIFICATE GENERATION ========")
for ip in dict(ipHasNames):
  i=i+1
  print("\n\n======== Creating certificate ({}/{}) for {} ========".format(str(i), len(ipHasNames), ip))
  aliasesAccociatedWithIp = ipHasNames[ip]
  if len(aliasesAccociatedWithIp) != 0:
    # set appropriate subjectAltName
    SAN = ""
    if len(aliasesAccociatedWithIp) > 1:
      j = 1
      for alias in aliasesAccociatedWithIp:
        SAN += "DNS." + str(j) + " = " + alias + "\n"
        j=j+1
        if (ADD_SUFFIX_TO_SAN):
          SAN += "DNS." + str(j) + " = " + alias + "." + dnsZoneName + "\n"
          j=j+1
    else:
      if (ADD_SUFFIX_TO_SAN):
        SAN += "DNS.1 = " + aliasesAccociatedWithIp[0] + "\n"
        SAN += "DNS.2 = " + aliasesAccociatedWithIp[0] + "." + dnsZoneName
      else:
        SAN += "DNS = " + aliasesAccociatedWithIp[0]

    print("\nSAN: " + SAN + "\n")
    # generate the config file for the certificate
    config = """
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
""".format(
  openSSLConf['C'],
  openSSLConf['ST'],
  openSSLConf['L'],
  openSSLConf['O'],
  openSSLConf['E'],
  ip,
  SAN
)

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
    os.system("openssl\\openssl x509 -req -in out\\{}\\{}.csr -CA {} -CAkey {} -CAcreateserial -out out\\{}\\{}.crt -days {} -sha256 -extfile out\\{}\\{}.cfg -extensions req_ext -passin pass:{}".format(ip,ip,rootCA,rootCAKey,ip,ip,CERTIFICATE_DAYS_VALID,ip,ip,rootCAPW))
    pem = open("out\\{}\\{}.crt".format(ip,ip), "r").read() + open("out\\{}\\{}.key".format(ip,ip), "r").read() 
    with open("out\\{}\\{}.pem".format(ip,ip), "w") as out:
      out.write(pem)
print("======== OPENSSL CERTIFICATE GENERATION FINISHED ========")
print("\n\nFinished! Your certificates are located in the out/ directory.")
if os.path.exists(".rnd"): os.remove(".rnd") 
exit(0)