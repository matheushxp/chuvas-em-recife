$urls = @{
    '2025' = 'https://dados.recife.pe.gov.br/dataset/ebda936c-f15a-4e0d-b8b6-5a9e270b0b67/resource/f907decb-0fb6-491b-8b6c-0f53f277f413/download/atendimentos-2025.csv'
    '2024' = 'https://dados.recife.pe.gov.br/dataset/ebda936c-f15a-4e0d-b8b6-5a9e270b0b67/resource/7c7bb871-3906-4d82-8993-857c9e6f137b/download/atendimentos-2024.csv'
    '2023' = 'https://dados.recife.pe.gov.br/dataset/ebda936c-f15a-4e0d-b8b6-5a9e270b0b67/resource/921d87c7-5ace-4856-9e3f-c31521259c36/download/atendimentos-2023.csv'
    '2022' = 'https://dados.recife.pe.gov.br/dataset/ebda936c-f15a-4e0d-b8b6-5a9e270b0b67/resource/10203dd4-9052-4a76-95eb-fd858aa053d4/download/atendimentos-2022.csv'
    '2021' = 'https://dados.recife.pe.gov.br/dataset/ebda936c-f15a-4e0d-b8b6-5a9e270b0b67/resource/bf6f5af8-3556-425c-bfec-0eddccdeeb73/download/atendimentos-2021.csv'
    '2020' = 'https://dados.recife.pe.gov.br/dataset/ebda936c-f15a-4e0d-b8b6-5a9e270b0b67/resource/559ce500-deab-467d-862e-cf50332a9c26/download/atendimentos-2020.csv'
    '2019' = 'https://dados.recife.pe.gov.br/dataset/ebda936c-f15a-4e0d-b8b6-5a9e270b0b67/resource/9bb859e1-19ae-4b95-9246-139b9273846f/download/atendimentos-2019.csv'
    '2018' = 'https://dados.recife.pe.gov.br/dataset/ebda936c-f15a-4e0d-b8b6-5a9e270b0b67/resource/a3a25520-de12-4f56-ae05-6dc1ec4c6207/download/atendimentos-2018.csv'
    '2017' = 'https://dados.recife.pe.gov.br/dataset/ebda936c-f15a-4e0d-b8b6-5a9e270b0b67/resource/40e0558f-dc49-4ec7-b5e6-5a791703ae34/download/atendimentos-2017.csv'
    '2016' = 'https://dados.recife.pe.gov.br/dataset/ebda936c-f15a-4e0d-b8b6-5a9e270b0b67/resource/932fee1e-80fd-49f8-9ae3-6e8dd96e33a3/download/atendimentos-2016.csv'
    '2015' = 'https://dados.recife.pe.gov.br/dataset/ebda936c-f15a-4e0d-b8b6-5a9e270b0b67/resource/9a5103f7-6bd0-4694-90d6-7e776b1e372d/download/atendimentos-2015.csv'
    '2014' = 'https://dados.recife.pe.gov.br/dataset/ebda936c-f15a-4e0d-b8b6-5a9e270b0b67/resource/b81bf4cc-ae19-4a43-94a7-f11b3e0b662b/download/atendimentos-2014.csv'
}
$dest = "dados_chuvas_recife/dados/brutos/defesa_civil"
$errors = @()
foreach ($ano in $urls.Keys | Sort-Object) {
    $url = $urls[$ano]
    $outFile = "$dest/atendimentos_$ano.csv"
    Write-Host "Baixando $ano..."
    try {
        Invoke-WebRequest -Uri $url -OutFile $outFile -UseBasicParsing -TimeoutSec 120
        $fileInfo = Get-Item $outFile
        $sizeKB = [math]::Round($fileInfo.Length / 1KB, 2)
        Write-Host "  -> OK: $outFile ($sizeKB KB)"
    } catch {
        Write-Host "  -> ERRO em $ano : $_"
        $errors += $ano
    }
}
Write-Host ""
Write-Host "=== RESUMO ==="
Get-ChildItem $dest -Filter "*.csv" | ForEach-Object {
    $sizeKB = [math]::Round($_.Length / 1KB, 2)
    Write-Host ("  {0}  ->  {1:N2} KB" -f $_.Name, $sizeKB)
}
if ($errors.Count -gt 0) {
    Write-Host "Erros: $($errors -join ', ')"
} else {
    Write-Host "Nenhum erro!"
}
