# DNS-Certificate-Creation-Tool
This tool allows you to quickly create certificates for an entire DNS zone.   
The provided PowerShell automates the creation of zone files, and is intended for usage with DNS Server for Windows Server 2016 or later.   

the Python script is server independent, and can be used as long as you can get your hands on the [zone file](https://en.wikipedia.org/wiki/Zone_file#File_format). The python script is currently referencing the OpenSSL Windows binary that is distributed with the release, but any OpenSSL binary for any platform would do. Please see the license.
## Prerequisites
- Python 3   
- OpenSSL (Windows binary included)
## Usage
If you are using DNS Server for Windows Server, everything should work out of the box, no modification needed.   
Usage: `powershell get-zone.ps1 <computername> <dns zone> <CIDR ip range> <rootCA.crt> <rootCA.key>`   
Example: `powershell get-zone.ps1 alice bob.local.example 192.168.43.64/26 rootCA.crt rootCA.key`   
   
If you are NOT using DNS Server for Windows Server, you can call the Python script with appropriate arguments, or create your own shell script that does it for you.   
Currently, the Python script takes the following arguments: `python3 create-certificates.py <dns zone> <zone file name> <CIDR ip range> <rootCA.crt> <rootCA.key> <email address> <organization> <city / locality> <state / province> <country>`   

## Notes
I have modified blockstack_zones to work with Python 3. Therefore, it is included with this distribution. Please see the license.
