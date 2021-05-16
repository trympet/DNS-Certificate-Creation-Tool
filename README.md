# DNS-Certificate-Creation-Tool
This tool allows you to quickly create certificates for an entire DNS zone.   
The provided PowerShell automates the creation of zone files, and is intended for use with DNS Server for Windows Server 2016 or later.   

## Prerequisites
- Python 3   
- OpenSSL if using Linux or Mac. Windows binary included.

## Usage
```powershell
./Create-DNSCertificates.ps1
     [-ComputerName] <String>
     [-DNSZone] <String>
     [-IPAddresses] <String>
     [-Certificate] <String>
     [-PrivateKey] <String>
     [[-Credential] <PSCredential>]
     [[-Authentication] <AuthenticationMechanism>]
     [-O] <String>
     [-L] <String>
     [-ST] <String>
     [-C] <String>
     [-E] <String>
```

If you are using DNS Server for Windows Server, everything should work out of the box, no modification needed.   
Example:
```powershell
./Create-DNSCertificates.ps1 -ComputerName dc-01.corp.contoso.com -DNSZone corp.contoso.com -IPAddresses 10.0.10.0/23 -Certificate contosocorp-ca.crt -PrivateKey contosocorp-ca.key -C US -ST WA -L Redmond -O Contoso
```
   
The certificate and OpenSSL artifacts are placed in the `./out` directory. 
   
You can also call the python script directly if you are not using Windows DNS Server.   
Example:
```bash
python3 create-certificates.py <dns zone> <zone file name> <CIDR ip range> <rootCA.crt> <rootCA.key> <email address> <organization> <city / locality> <state / province> <country>
```
