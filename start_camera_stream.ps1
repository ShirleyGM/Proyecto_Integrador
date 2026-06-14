# Streaming de camara XWF-1080P hacia localhost:8080 (mpegts sobre TCP)
# Luego ejecutar: $env:VIDEO_SOURCE="tcp://localhost:8080"; python main.py

Write-Host "Iniciando streaming de camara XWF-1080P..." -ForegroundColor Green
Write-Host "Stream disponible en: tcp://localhost:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "En otra terminal, ejecuta:" -ForegroundColor Yellow
Write-Host '  $env:VIDEO_SOURCE="tcp://localhost:8080"; python main.py' -ForegroundColor White
Write-Host ""
Write-Host "Presiona Ctrl+C para detener el streaming." -ForegroundColor Yellow
Write-Host ""

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: ffmpeg no esta instalado o no esta en el PATH." -ForegroundColor Red
    Write-Host "Descargalo en: https://ffmpeg.org/download.html" -ForegroundColor Red
    exit 1
}

ffmpeg -f dshow -i video="XWF-1080P" -vcodec copy -f mpegts tcp://localhost:8080?listen

Write-Host "Streaming detenido." -ForegroundColor Red
