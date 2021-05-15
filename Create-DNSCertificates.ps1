# (c) 2020 by Trym Lund Flogard
# https://github.com/trympet/
# The following code is licensed under MIT license (see LICENSE for details).
# Please read the license issued by The OpenSSL Project and SSLeay as well.

### parameters
 param (
    [Parameter(Mandatory=$true)]
    [string]$ComputerName,
    [Parameter(Mandatory=$true)]
    [string]$DNSZone,
    [Parameter(Mandatory=$true)]
    [string]$IPAddresses,
    [Parameter(Mandatory=$true)]
    [string]$Certificate,
    [Parameter(Mandatory=$true)]
    [string]$PrivateKey,

    # Remote execution parameters
    [PSCredential]$Credential = [PSCredential]::Empty,
    [System.Management.Automation.Runspaces.AuthenticationMechanism]$Authentication = [System.Management.Automation.Runspaces.AuthenticationMechanism]::Default,

    # Certificate info
    [string]$E,
    [string]$O,
    [string]$L,
    [string]$ST,
    [string]$C
 )

if (Test-Path "./out/") {
  $PreviousCertCount =  (Get-ChildItem ./out/ | Measure-Object).Count
  if ([int]$PreviousCertCount -gt 0) {
    $cont = Read-Host -Prompt "The './out' directory is not empty. Continuing will overwrite previous data. Continue? Y/N: "
    if ($cont -ne 'y'){
      Write-Host "Okay, exiting."
      exit
    } else {
      Write-Host "Removing previous export..."
      Remove-Item -Recurse "./out/"
    }
  }
}

$FileName = "dns-export-" + $DNSZone
$Location = "\Windows\System32\dns\" + $FileName


# create new zone export
Write-Host "Requesting zone export on remote machine..."
Invoke-command -ComputerName $ComputerName -Credential $Credential  -Authentication $Authentication -ScriptBlock {
  param($zone, $file)
  Export-DnsServerZone -Name $zone -FileName $file
} -ArgumentList $DNSZone, $FileName
if (!$?) {
  Write-Error "Failed to export DNS zone on $ComputerName." -ErrorAction Stop
}
Write-Host "Zone exported on remote machine. $Location"


Write-Host "Copying export to local computer..."
$RemoteExportDir = "\\" + $ComputerName + "\c$" + $Location
Copy-Item $RemoteExportDir $FileName
if (!$?) {
  Write-Error "Could not copy DNS zone file to local computer."
}
Write-Host "Export copied to ./$FileName"


Write-Host "Cleaning up export on remote machine..."
Invoke-command -ComputerName $ComputerName -Credential $Credential  -Authentication $Authentication -ScriptBlock {
  param($loc)
  if (Test-Path $loc) {
    Remove-Item $loc
  }
} -ArgumentList $Location

if (!$?) {
  Write-Error "Failed to connect to remote machine." -ErrorAction Stop
}
Write-Host "Export finished."


Write-Host "Starting python..."
$PythonScriptLocation = [string](Get-Location) + "\python_create_certs.py"
& (Get-Command python).Path $PythonScriptLocation $DNSZone $FileName $IPAddresses $Certificate $PrivateKey $E $O $L $ST $C

# clean up files
Write-Host "Cleaning up local export..."

if (Test-Path $FileName) {
  Remove-Item $FileName
}

Write-Host "DNS certificate creation completed."