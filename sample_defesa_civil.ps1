$dest = "dados_chuvas_recife/dados/brutos/defesa_civil"
Write-Host "=" * 80
Write-Host "AMOSTRA DAS PRIMEIRAS 5 LINHAS DE CADA ARQUIVO"
Write-Host "=" * 80

Get-ChildItem $dest -Filter "*.csv" | Sort-Object Name | ForEach-Object {
    $file = $_
    Write-Host ""
    Write-Host ("[{0}] ({1:N2} KB)" -f $file.Name, ($file.Length / 1KB))
    Write-Host "-" * 70
    $lines = Get-Content $file.FullName -TotalCount 6 -Encoding UTF8
    $lines | ForEach-Object { Write-Host $_.Substring(0, [Math]::Min(200, $_.Length)) }
}
