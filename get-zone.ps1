# (c) 2020 by Trym Lund Flogard
# https://github.com/trympet/
# The following code is licensed under MIT license (see LICENSE for details).
# Please read the license issued by The OpenSSL Project and SSLeay as well.

### parameters
 param (
    [Parameter(Mandatory=$true)]
    [string]$ComputerName,
    [Parameter(Mandatory=$true)]
    [string]$DnsZone,
    [Parameter(Mandatory=$true)]
    [string]$IPAddresses,
    [Parameter(Mandatory=$true)]
    [string]$Certificate,
    [Parameter(Mandatory=$true)]
    [string]$PrivateKey,

    # Certificate info
    [string]$E,
    [string]$O,
    [string]$L,
    [string]$ST,
    [string]$C
 )

function Exit-Error {
  Write-Host($args[0])
  Write-Host("Usage: get-zone.ps1 <computername> <dns zone> <CIDR ip range> <rootCA.crt> <rootCA.key>")
  exit(1)
}

if (Test-Path "./out/") {
  $previous_cert_count =  (Get-ChildItem .\out\ | Measure-Object).Count
  if ([int]$previous_cert_count -gt 0) {
    $cont = Read-Host -Prompt "The './out' directory is not empty. Continuing will overwrite previous data. Continue? Y/N: "
    if ($cont -ne 'y'){
      Exit-Error "Okay, exiting."
    } else {
      Remove-Item -Recurse ".\out\"
    }
  }
}

# request zone export on remote machine
$file_name = "dns-export-" + $DnsZone
$location = "\Windows\System32\dns\" + $file_name

# remove previous export
Invoke-command -ComputerName $ComputerName -ScriptBlock {
  param($loc)
  if (Test-Path $loc) {
    Remove-Item $loc
  }
} -ArgumentList $location

# create new zone export
Invoke-command -ComputerName $ComputerName -ScriptBlock {
  param($zone, $file)
  Export-DnsServerZone -Name $zone -FileName $file
} -ArgumentList $DnsZone, $file_name

if (!$?) {
  Exit-Error "Error on DNS zone export."
}

# copy export to local machine via administrative SMB share
$remote_computer_export_location = "\\" + $ComputerName + "\c$" + $location
Copy-Item $remote_computer_export_location $file_name
if (!$?) {
  Exit-Error "Could not copy DNS zone file to local computer."
}

# parse zone, then generate certificates
$pwd = Get-Location
$python = (Get-Command python).Path
$python_file_location = [string]$pwd + "\create-certificates.py"

# start python
& $python $python_file_location $DnsZone $file_name $IPAddresses $Certificate $PrivateKey $E $O $L $ST $C

# clean up files
Write-Host "Cleaning up files"

if (Test-Path $file_name) {
  Remove-Item $file_name
}