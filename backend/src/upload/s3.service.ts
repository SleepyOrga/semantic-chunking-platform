import { Injectable, OnModuleInit } from '@nestjs/common';
import { S3Client, PutObjectCommand, GetObjectCommand } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class S3Service implements OnModuleInit {
  private s3Client: S3Client;
  private bucket: string;

  constructor(private configService: ConfigService) {}

  onModuleInit() {
    // Get configuration values
    const accessKeyId = this.configService.get<string>('AWS_ACCESS_KEY_ID');
    const secretAccessKey = this.configService.get<string>('AWS_SECRET_ACCESS_KEY');
    const region = this.configService.get<string>('AWS_REGION');
    this.bucket = this.configService.get<string>('AWS_S3_BUCKET') || '';

    // Validate required config
    if (!accessKeyId || !secretAccessKey || !region || !this.bucket) {
      console.warn('Missing AWS S3 configuration. File uploads will fail.');
    }

    // Initialize S3 client with non-null assertion
    this.s3Client = new S3Client({
      region,
      credentials: {
        accessKeyId: accessKeyId!,
        secretAccessKey: secretAccessKey!,
      },
    });
  }

  async uploadFile(file: Express.Multer.File, username: string): Promise<string> {
    if (!this.bucket) {
      throw new Error('AWS S3 bucket not configured');
    }

    const timestamp = new Date().toISOString().replace(/:/g, '-');
    const key = `uploads/${username}/${timestamp}-${file.originalname}`;
    
    const command = new PutObjectCommand({
      Bucket: this.bucket,
      Key: key,
      Body: file.buffer,
      ContentType: file.mimetype,
    });

    await this.s3Client.send(command);
    return key;
  }

  async getSignedUrl(key: string): Promise<string> {
    if (!this.bucket) {
      throw new Error('AWS S3 bucket not configured');
    }

    const command = new GetObjectCommand({
      Bucket: this.bucket,
      Key: key,
    });
    
    // URL expires in 1 hour
    return getSignedUrl(this.s3Client, command, { expiresIn: 3600 });
  }

  async getFileStream(key: string): Promise<NodeJS.ReadableStream> {
    if (!this.bucket) {
      throw new Error('AWS S3 bucket not configured');
    }

    const command = new GetObjectCommand({
      Bucket: this.bucket,
      Key: key,
    });

    const response = await this.s3Client.send(command);
    
    if (!response.Body) {
      throw new Error('No file content found');
    }

    return response.Body as NodeJS.ReadableStream;
  }

  async getFileContent(key: string): Promise<string> {
    if (!this.bucket) {
      throw new Error('AWS S3 bucket not configured');
    }

    const command = new GetObjectCommand({
      Bucket: this.bucket,
      Key: key,
    });

    const response = await this.s3Client.send(command);
    
    if (!response.Body) {
      throw new Error('No file content found');
    }

    const chunks: Buffer[] = [];
    const stream = response.Body as NodeJS.ReadableStream;
    
    return new Promise((resolve, reject) => {
      stream.on('data', (chunk: Buffer) => chunks.push(chunk));
      stream.on('error', reject);
      stream.on('end', () => resolve(Buffer.concat(chunks).toString('utf-8')));
    });
  }
}