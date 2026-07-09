Set-Location -Path $PSScriptRoot

docker run --rm --env-file .env `
  -v "$PSScriptRoot\data:C:\app\data" `
  -v "$PSScriptRoot\logs:C:\app\logs" `
  -v "$PSScriptRoot\reports:C:\app\reports" `
  -v "$PSScriptRoot\state:C:\app\state" `
  email-reminder:latest
