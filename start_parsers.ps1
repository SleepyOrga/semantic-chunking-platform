# PowerShell script to start all parser workers

Write-Host "🚀 Starting Parser Workers..." -ForegroundColor Green

# Set environment variables
$env:RABBITMQ_URL = "amqp://admin:admin@52.65.216.159:5672/"
$env:AWS_REGION = "ap-southeast-2"
$env:AWS_S3_BUCKET_NAME = "semantic-chunking-bucket"

# Start DOCX Parser
Write-Host "📄 Starting DOCX Parser..." -ForegroundColor Yellow
Set-Location "ai-services\xlsx_docx_parser"
$docxProcess = Start-Process python -ArgumentList "docx_worker.py" -PassThru -NoNewWindow

# Start XLSX Parser
Write-Host "📊 Starting XLSX Parser..." -ForegroundColor Yellow
$xlsxProcess = Start-Process python -ArgumentList "xlsx_worker.py" -PassThru -NoNewWindow

# Start PDF/OCR Parser
Write-Host "📋 Starting PDF/OCR Parser..." -ForegroundColor Yellow
Set-Location "..\ocr_parser"
$pdfProcess = Start-Process python -ArgumentList "pdf_worker.py" -PassThru -NoNewWindow

Write-Host "✅ All parser workers started!" -ForegroundColor Green
Write-Host "DOCX Parser PID: $($docxProcess.Id)" -ForegroundColor Cyan
Write-Host "XLSX Parser PID: $($xlsxProcess.Id)" -ForegroundColor Cyan
Write-Host "PDF Parser PID: $($pdfProcess.Id)" -ForegroundColor Cyan

Write-Host "Press Ctrl+C to stop all parsers" -ForegroundColor Red

# Wait for user interrupt
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} catch {
    Write-Host "🛑 Stopping parser workers..." -ForegroundColor Red
    $docxProcess.Kill()
    $xlsxProcess.Kill()
    $pdfProcess.Kill()
    Write-Host "✅ All parser workers stopped." -ForegroundColor Green
}
