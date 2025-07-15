import {
  Controller,
  Post,
  Get,
  UseInterceptors,
  UploadedFile,
  Body,
  Param,
  BadRequestException,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { S3Service } from './s3.service';
import { RabbitMQService } from '../queue/rabbitmq.service';
import { DocumentService } from '../document/document.service';

@Controller('upload')
export class AppController {
  constructor(
    private readonly s3Service: S3Service,
    private readonly rabbit: RabbitMQService,
    private readonly documentService: DocumentService,
  ) {}

  @Post()
  @UseInterceptors(
    FileInterceptor('file', {
      limits: {
        fileSize: 10 * 1024 * 1024,
      },
    }),
  )
  async uploadFile(
    @UploadedFile() file: Express.Multer.File,
    @Body('username') username: string,
    @Body('user_id') userId: string,
  ) {
    console.log('🔥 DEBUG: Upload request received');
    console.log('📁 Uploaded file:', file);
    console.log('👤 username:', username);
    console.log('🆔 user_id:', userId);

    const allowedMimeTypes = [
      // Documents
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // docx
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // xlsx

      // Images
      'image/jpeg',
      'image/png',
      'image/gif',
      'image/webp',
      'image/tiff',
    ];

    if (!file) {
      throw new BadRequestException('No file uploaded');
    }

    if (!allowedMimeTypes.includes(file.mimetype)) {
      throw new BadRequestException(
        `Invalid file type. Only PDF, DOCX, XLSX, and common image formats are allowed. Received: ${file.mimetype}`,
      );
    }

    if (!userId) {
      throw new BadRequestException('User ID is required');
    }

    const key = await this.s3Service.uploadFile(file, username || 'anonymous');

    const documentId = await this.documentService.createDocument({
      user_id: userId,
      filename: file.originalname,
      mimetype: file.mimetype,
      size: file.size,
      path: key, // Use S3 key as the path
    });

    // 👉 Gửi message vào RabbitMQ
    await this.rabbit.sendToQueue({
      username: username || 'anonymous',
      filename: file.originalname,
      s3Key: key,
      uploadedAt: new Date().toISOString(),
    });

    return {
      filename: file.originalname,
      key,
      uploadedAt: new Date().toISOString(),
    };
  }
}
