param(
  [string]$OutDir = ".\.secrets"
)
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$priv = Join-Path $OutDir "dev_rsa.pem"
$pub = Join-Path $OutDir "dev_rsa.pub"
# Attempt to call openssl if exists; otherwise generate using Python
if (Get-Command openssl -ErrorAction SilentlyContinue) {
  openssl genpkey -algorithm RSA -out $priv -pkeyopt rsa_keygen_bits:2048
  openssl rsa -in $priv -pubout -out $pub
  Write-Output "Generated keys: $priv and $pub"
} else {
  Write-Output "OpenSSL not found. Use `python -c` approach or generate keys from Python."
}
