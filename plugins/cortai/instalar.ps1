# Instalador do Cortaí para Windows. Não pede senha de administrador:
# o uv vai para %USERPROFILE%\.local\bin, o ffmpeg (se faltar) para %USERPROFILE%\.corta\bin
# e o resto fica dentro do plugin. No fim edita o vídeo de amostra e só diz "TUDO CERTO" se passar.
# Uso: powershell -ExecutionPolicy Bypass -File instalar.ps1
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"
$Raiz = Split-Path -Parent $MyInvocation.MyCommand.Path
$CortaHome = if ($env:CORTA_HOME) { $env:CORTA_HOME } else { Join-Path $env:USERPROFILE ".corta" }
$Bin = Join-Path $CortaHome "bin"
New-Item -ItemType Directory -Force -Path $Bin | Out-Null
function Passo($t) { Write-Host ""; Write-Host "== $t" }
function Erro($t) { Write-Host ""; Write-Host "X $t" -ForegroundColor Red; exit 1 }

Passo "1/6 uv (cuida do Python sem mexer no resto do computador)"
$uv = (Get-Command uv -ErrorAction SilentlyContinue).Source
$candidato = Join-Path $env:USERPROFILE ".local\bin\uv.exe"
if (-not $uv -and (Test-Path $candidato)) { $uv = $candidato }
if (-not $uv) {
    $env:UV_NO_MODIFY_PATH = "1"
    try { Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression } catch { Erro "Nao consegui baixar o uv. Confira a internet e rode de novo." }
    $uv = $candidato
}
& $uv --version

Passo "2/6 ffmpeg (corta e grava o video)"
function VersaoOk($exe) {
    try { $l = (& $exe -version 2>$null | Select-Object -First 1) } catch { return $false }
    if ($l -match 'version n?(\d+)\.') { return [int]$Matches[1] -ge 7 }
    return $false
}
$sis = (Get-Command ffmpeg -ErrorAction SilentlyContinue).Source
$local = Join-Path $Bin "ffmpeg.exe"
if ($sis -and (Get-Command ffprobe -ErrorAction SilentlyContinue) -and (VersaoOk $sis)) {
    Write-Host "usando o ffmpeg do sistema: $sis"
} elseif ((Test-Path $local) -and (VersaoOk $local)) {
    Write-Host "usando $local"
} else {
    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("corta-ffmpeg-" + [guid]::NewGuid())
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    $zip = Join-Path $tmp "ffmpeg.zip"
    Write-Host "baixando o ffmpeg (~110 MB)..."
    $ProgressPreference = "SilentlyContinue"
    try { Invoke-WebRequest "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile $zip -UseBasicParsing }
    catch { Erro "Nao consegui baixar o ffmpeg. Confira a internet e rode de novo." }
    Expand-Archive -Path $zip -DestinationPath $tmp -Force
    foreach ($p in @("ffmpeg.exe", "ffprobe.exe")) {
        $achado = Get-ChildItem -Path $tmp -Recurse -Filter $p | Select-Object -First 1
        if (-not $achado) { Erro "O pacote do ffmpeg veio sem $p." }
        Copy-Item $achado.FullName (Join-Path $Bin $p) -Force
    }
    Remove-Item $tmp -Recurse -Force
    if (-not (VersaoOk $local)) { Erro "O ffmpeg baixado nao abriu." }
}

Passo "3/6 bibliotecas do motor (Python 3.12, transcricao, detector de rosto)"
$extra = @()
if ($env:CORTA_FORTE -eq "1") { $extra = @("--extra", "forte") }
& $uv sync --project (Join-Path $Raiz "motor") --python 3.12 --frozen @extra
if ($LASTEXITCODE -ne 0) { Erro "A instalacao das bibliotecas falhou. Rode de novo; se repetir, rode /cortai:diagnostico." }

Passo "4/6 motion (Remotion: efeitos e animacoes)"
if ($env:CORTA_SEM_MOTION -eq "1") { Write-Host "pulado (CORTA_SEM_MOTION=1)" } else {
    $NodeVersao = "v22.23.3"
    function NodeOk($exe) {
        try { $v = (& $exe --version 2>$null) } catch { return $false }
        if ($v -match '^v(\d+)') { return [int]$Matches[1] -ge 18 }
        return $false
    }
    $nodeSis = (Get-Command node -ErrorAction SilentlyContinue).Source
    $nodeDir = Join-Path $CortaHome "node"
    if ($nodeSis -and (NodeOk $nodeSis)) { Write-Host "usando o Node do sistema: $nodeSis" }
    elseif (Test-Path (Join-Path $nodeDir "node.exe")) { Write-Host "usando $nodeDir" }
    else {
        Write-Host "baixando o Node $NodeVersao..."
        $ProgressPreference = "SilentlyContinue"
        $tmpn = Join-Path ([System.IO.Path]::GetTempPath()) ("corta-node-" + [guid]::NewGuid())
        New-Item -ItemType Directory -Force -Path $tmpn | Out-Null
        $zipn = Join-Path $tmpn "node.zip"
        try { Invoke-WebRequest "https://nodejs.org/dist/$NodeVersao/node-$NodeVersao-win-x64.zip" -OutFile $zipn -UseBasicParsing }
        catch { Erro "Nao consegui baixar o Node. Confira a internet e rode de novo." }
        Expand-Archive -Path $zipn -DestinationPath $tmpn -Force
        if (Test-Path $nodeDir) { Remove-Item $nodeDir -Recurse -Force }
        Move-Item (Join-Path $tmpn "node-$NodeVersao-win-x64") $nodeDir
        Remove-Item $tmpn -Recurse -Force
    }
    if (Test-Path (Join-Path $nodeDir "node.exe")) { $env:PATH = "$nodeDir;$env:PATH" }
    Push-Location (Join-Path $Raiz "motion")
    & npm.cmd ci --no-audit --no-fund --loglevel=error
    if ($LASTEXITCODE -ne 0) { Pop-Location; Erro "A instalacao do Remotion falhou. Rode de novo." }
    & npx.cmd remotion browser ensure | Out-Null
    if ($LASTEXITCODE -ne 0) { Pop-Location; Erro "Nao consegui preparar o navegador do Remotion. Rode de novo." }
    Pop-Location
    Write-Host "motion pronto"
}

$motor = Join-Path $Raiz "motor"

# atalho fixo para a pessoa usar no Prompt/PowerShell (ex.: conectar a ElevenLabs), sempre nesta versao
$atalho = "@echo off`r`ncall `"$Raiz\bin\corta.cmd`" %*`r`n"
Set-Content -Path (Join-Path $Bin "corta.cmd") -Value $atalho -Encoding ASCII -NoNewline

Passo "5/6 medindo este computador"
& $uv run --quiet --frozen --project $motor corta perfil --recalcular
if ($LASTEXITCODE -ne 0) { Erro "Nao consegui medir o computador." }

Passo "6/6 teste: editando o video de amostra (a 1a vez baixa o modelo de transcricao, 1-3 GB)"
& $uv run --quiet --frozen --project $motor corta amostra
exit $LASTEXITCODE
