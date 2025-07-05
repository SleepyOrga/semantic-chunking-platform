import { Controller, Post, Get, UseInterceptors, UploadedFile, Body, Param } from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { S3Service } from './s3.service';
import { RabbitMQService } from './rabbitmq.service';

@Controller('upload')
export class AppController {
  constructor(
    private readonly s3Service: S3Service,
    private readonly rabbit: RabbitMQService
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
  ) {
    const key = await this.s3Service.uploadFile(file, username || 'anonymous');
    
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
      uploadedAt: new Date().toISOString()
    };
  }
}
