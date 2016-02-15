#ps1
$strPassword = "Interactive2014"
$objUser = [ADSI]("WinNT://./Administrator, user")
$objUser.psbase.invoke("SetPassword",$strPassword)
$username = "administrator"
$password = ConvertTo-SecureString "Interactive2014" -AsPlainText -Force
$creds = New-Object System.Management.Automation.PSCredential( $username, $password )
add-computer -domainname caaspoc.com -credential $creds
shutdown /r /f

