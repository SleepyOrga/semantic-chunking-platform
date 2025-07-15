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
      const { fileType, s3Key, filename } = payload;

      this.logger.debug(`📦 Raw Payload: ${JSON.stringify(payload)}`);

      const inputUrl = await this.s3Service.getSignedUrl(s3Key);
      this.logger.debug(`✅ Signed URL: ${inputUrl}`);

      const outputDir = path.resolve(
        `/tmp/output-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
      );

      this.logger.log(`🚀 Start processing file: ${filename}`);
      this.logger.log(`🔍 File Type: ${fileType}`);
      this.logger.log(`🌐 Input URL: ${inputUrl}`);
      this.logger.log(`📁 Output Directory: ${outputDir}`);
      const normalizedInputUrl = inputUrl.replace(/\\/g, '/');
      switch (fileType) {
        case 'docx':
          this.logger.log('⚙️ Launching DOCX parser...');
          await this.runPythonScript(
            '../ai-services/xlsx_docx_parser/parser_docx.py',
            [normalizedInputUrl, '--output', outputDir],
          );
          break;

        case 'pdf':
          this.logger.log('⚙️ Launching OCR PDF parser...');
          await this.runPythonScript('../ai-services/ocr_parser/main.py', [
            normalizedInputUrl,
            '--output',
            outputDir,
          ]);
          break;

        case 'xlsx':
          this.logger.log('⚙️ Launching XLSX parser...');
          await this.runPythonScript(
            '../ai-services/xlsx_docx_parser/parser_xlsx.py',
            [normalizedInputUrl, '--output', outputDir],
          );
          break;

        default:
          this.logger.warn(`❌ Unsupported file type: ${fileType}`);
          return;
      }

      this.logger.log(`✅ Successfully finished processing: ${filename}`);
    } catch (error) {
      this.logger.error('🔥 Error while handling message:', error);
    }
  }

  private async runPythonScript(
    scriptPath: string,
    args: string[],
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      const fullPath = path.resolve(scriptPath);

      const pythonPath = path.resolve(
        __dirname,
        '../../../ai-services/.venv/Scripts/python.exe',
      );

      if (!fs.existsSync(pythonPath)) {
        this.logger.error(`❌ Python not found at ${pythonPath}`);
        return reject(new Error(`Python executable not found`));
      }

      this.logger.log(`📤 Spawning Python script: ${fullPath}`);
      this.logger.debug(`🧪 Args: ${args.join(' ')}`);
      const quotedArgs = args.map((arg) => `"${arg}"`);
      this.logger.debug(`🧪 Args: ${quotedArgs.join(' ')}`);

      const child = spawn(pythonPath, [fullPath, ...quotedArgs], {
        shell: true,
      });

      child.stdout.on('data', (data) => {
        this.logger.log(`🟢 [stdout] ${data.toString().trim()}`);
      });

      child.stderr.on('data', (data) => {
        this.logger.error(`🔴 [stderr] ${data.toString().trim()}`);
      });

      child.on('close', (code) => {
        if (code === 0) {
          this.logger.log('✅ Python script completed successfully.');
          resolve();
        } else {
          this.logger.error(`❌ Python script exited with code ${code}`);
          reject(
            new Error(
              `Python script failed with exit code ${code}: ${fullPath}`,
            ),
          );
        }
      });
    });
  }
}
