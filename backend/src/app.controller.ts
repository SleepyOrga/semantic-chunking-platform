import { Controller, Post, Get, UseInterceptors, UploadedFile, Body, Param } from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { S3Service } from './s3.service';

@Controller('upload')
export class AppController {
  constructor(private readonly s3Service: S3Service) {}

  @Post()
  @UseInterceptors(
    FileInterceptor('file', {
      limits: {
        fileSize: 10 * 1024 * 1024, // 10MB
      },
    }),
  )
  async uploadFile(
    @UploadedFile() file: Express.Multer.File,
    @Body('username') username: string,
  ) {
    const key = await this.s3Service.uploadFile(file, username || 'anonymous');
    return { 
      filename: file.originalname,
      key,
      uploadedAt: new Date().toISOString()
    };
  }

  @Get('view/:key')
  async getFileUrl(@Param('key') key: string) {
    const url = await this.s3Service.getSignedUrl(key);
    return { url };
  }
}