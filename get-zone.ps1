# (c) 2020 by Trym Lund Flogard
# https://github.com/trympet/
# The following code is licensed under MIT license (see LICENSE for details).
# Please read the license issued by The OpenSSL Project and SSLeay as well.

function Exit-Error {
  Write-Host($args[0])
  Write-Host("Usage: get-zone.ps1 <computername> <dns zone> <CIDR ip range> <rootCA.crt> <rootCA.key>")
  exit(1)
}

if (Test-Path ".\out\") {
  $previous_cert_count =  (Get-ChildItem .\out\ | Measure-Object).Count
  if ([int]$previous_cert_count -gt 0) {
    $cont = Read-Host -Prompt "The 'out\' directory is not empty. Continuing will overwrite previous data. Continue? Y/N: "
    if ($cont -ne 'y'){
      Exit-Error "Okay, exiting."
    } else {
      Remove-Item -Recurse ".\out\"
    }
  }
}

# check vars or arguments
if (Test-Path ".\vars.ps1") {
  # load vars from external file
  . ".\vars.ps1"

} elseif (
  [string]::IsNullOrEmpty($args[0]) -or # computername
  [string]::IsNullOrEmpty($args[1]) -or # dns zone
  [string]::IsNullOrEmpty($args[2]) -or # ip range string
  [string]::IsNullOrEmpty($args[3]) -or # rootCA.crt
  [string]::IsNullOrEmpty($args[4]) # rootCA.key
  ) {
  # missing args
  Exit-Error "Missing computername or dns zone arguments"
} else {
  # set vars and args
  $computer_name = $args[0]
  $dns_zone = $args[1]
  $ip_range = $args[2]
  $rootca_crt = $args[3]
  $rootca_key = $args[4]
}



# request zone export on remote machine
$file_name = "dns-export-" + $dns_zone
$location = "\Windows\System32\dns\" + $file_name

# remove previous export
Invoke-command -ComputerName $computer_name -ScriptBlock {
  param($loc)
  if (Test-Path $loc) {
    Remove-Item $loc
  }
} -ArgumentList $location

# create new zone export
Invoke-command -ComputerName $computer_name -ScriptBlock {
  param($zone, $file)
  Export-DnsServerZone -Name $zone -FileName $file
} -ArgumentList $dns_zone, $file_name

if (!$?) {
  Exit-Error "Error on DNS zone export."
}

# copy export to local machine via administrative SMB share
$remote_computer_export_location = "\\" + $computer_name + "\c$" + $location
Copy-Item $remote_computer_export_location $file_name
if (!$?) {
  Exit-Error "Could not copy DNS zone file to local computer."
}

# check vars or arguments
if (!(Test-Path ".\vars.ps1")) {
  # get certificate props
  $C = Read-Host -Prompt '[C]'
  $ST = Read-Host -Prompt '[ST]'
  $L = Read-Host -Prompt '[L]'
  $O = Read-Host -Prompt '[O]'
  $E = Read-Host -Prompt '[emailAddress]'
}

# parse zone, then generate certificates
$pwd = Get-Location
$python = (Get-Command python).Path
$python_file_location = [string]$pwd + "\create-certificates.py"

# start python
& $python $python_file_location $dns_zone $file_name $ip_range $rootca_crt $rootca_key $E $O $L $ST $C

# clean up files
Write-Host "Cleaning up files"

if (Test-Path $file_name) {
  Remove-Item $file_name
}