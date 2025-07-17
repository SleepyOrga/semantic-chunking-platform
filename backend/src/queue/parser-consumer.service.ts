import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import { RabbitMQService } from './rabbitmq.service';
import { spawn } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import { S3Service } from 'src/upload/s3.service';

@Injectable()
export class ParserConsumerService implements OnModuleInit {
  private readonly logger = new Logger(ParserConsumerService.name);

  constructor(
    private readonly rabbitMQService: RabbitMQService,
    private readonly s3Service: S3Service,
  ) {}

  async onModuleInit() {
    this.logger.log('🔁 Waiting for RabbitMQ channel to be ready...');
    await this.rabbitMQService.awaitConnection();
    this.logger.log('✅ RabbitMQ channel ready. Starting consumer...');

    await this.rabbitMQService.consume(
      'file-process-queue',
      this.handleMessage.bind(this),
    );
  }

  async handleMessage(msg: any) {
    this.logger.log('📩 New message received from file-process-queue');
  
    try {
      const payload = JSON.parse(msg.content.toString());
      const { fileType, s3Key, filename, documentId } = payload;
  
      this.logger.debug(`📦 Raw Payload: ${JSON.stringify(payload)}`);
  
      const inputUrl = await this.s3Service.getSignedUrl(s3Key);
      const s3Bucket = process.env.S3_BUCKET_NAME || 'semantic-chunking-bucket';
  
      const safeDocumentId = documentId || (filename ? filename.replace(/\W+/g, "_") : `file_${Date.now()}`);
      const outputS3Prefix = `parsed/${safeDocumentId}/`;
  
      this.logger.log(`🚀 Start processing file: ${filename}`);
      this.logger.log(`🔍 File Type: ${fileType}`);
      this.logger.log(`🌐 Input URL: ${inputUrl}`);
      this.logger.log(`📁 Output Directory (S3): ${outputS3Prefix}`);
  
      const normalizedInputUrl = inputUrl.replace(/\\/g, '/');
      let mdS3Key: string | undefined;
  
      switch (fileType) {
        case 'docx':
          this.logger.log('⚙️ Launching DOCX parser...');
          mdS3Key = await this.runPythonScript(
            '../ai-services/xlsx_docx_parser/parser_docx.py',
            [normalizedInputUrl, '--s3-bucket', s3Bucket, '--s3-prefix', outputS3Prefix]
          );
          break;
  
        case 'pdf':
          this.logger.log('⚙️ Launching OCR PDF parser...');
          mdS3Key = await this.runPythonScript(
            '../ai-services/ocr_parser/main.py',
            [normalizedInputUrl, '--s3-bucket', s3Bucket, '--s3-prefix', outputS3Prefix]
          );
          break;
  
        case 'xlsx':
          this.logger.log('⚙️ Launching XLSX parser...');
          mdS3Key = await this.runPythonScript(
            '../ai-services/xlsx_docx_parser/parser_xlsx.py',
            [normalizedInputUrl, '--s3-bucket', s3Bucket, '--s3-prefix', outputS3Prefix]
          );
          break;
  
        default:
          this.logger.warn(`❌ Unsupported file type: ${fileType}`);
          return;
      }
  
      if (!mdS3Key) {
        this.logger.error('❌ Markdown S3 key not found from parser output');
        return;
      }
  
      this.logger.log(`✅ Markdown uploaded to: ${mdS3Key}`);
  
      await this.rabbitMQService.sendToQueue({
        s3Bucket,
        s3Key: mdS3Key,
        documentId: safeDocumentId,
        fileType,
      }, 'chunking-queue');
  
      this.logger.log(`📤 Pushed job to chunking-queue for: ${safeDocumentId}`);
      this.logger.log(`🎉 Finished processing: ${filename}`);
    } catch (error) {
      this.logger.error('🔥 Error while handling message:', error);
    }
  }
  

  private async runPythonScript(scriptPath: string, args: string[]): Promise<string> {
    return new Promise((resolve, reject) => {
      const fullPath = path.resolve(scriptPath);
      const pythonPath = path.resolve(__dirname, '../../../ai-services/.venv/Scripts/python.exe');
  
      if (!fs.existsSync(pythonPath)) {
        this.logger.error(`❌ Python not found at ${pythonPath}`);
        return reject(new Error(`Python executable not found`));
      }
  
      const quotedArgs = args.map((arg) => `"${arg}"`);
      const child = spawn(pythonPath, [fullPath, ...quotedArgs], { shell: true });
  
      let stdoutBuffer = '';
  
      child.stdout.on('data', (data) => {
        const str = data.toString();
        stdoutBuffer += str;
        this.logger.log(`🟢 [stdout] ${str.trim()}`);
      });
  
      child.stderr.on('data', (data) => {
        this.logger.error(`🔴 [stderr] ${data.toString().trim()}`);
      });
  
      child.on('close', (code) => {
        if (code === 0) {
          try {
            const json = JSON.parse(stdoutBuffer.trim().split('\n').pop()!);
            resolve(json.md_s3_key); // Trả về md_s3_key
          } catch (err) {
            this.logger.error(`❌ Failed to parse parser output: ${stdoutBuffer}`);
            reject(err);
          }
        } else {
          this.logger.error(`❌ Python script exited with code ${code}`);
          reject(new Error(`Python script failed with exit code ${code}`));
        }
      });
    });
  }  
}
