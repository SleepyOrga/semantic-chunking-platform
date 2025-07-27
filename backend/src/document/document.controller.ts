import { Controller, Get, Post, Body, Delete, Param, UseGuards, Req, UploadedFile, UseInterceptors, Res, HttpException, HttpStatus, Put } from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { DocumentService } from './document.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { Response } from 'express';

@Controller()
export class DocumentController {
  constructor(private readonly documentService: DocumentService) {}

  @Get('documents')
  @UseGuards(JwtAuthGuard)
  async getUserDocuments(@Req() req) {
    const userId = req.user.id;
    return this.documentService.getDocumentsByUserId(userId);
  }

  @Get('documents/:id')
  @UseGuards(JwtAuthGuard)
  async getDocumentById(@Param('id') id: string, @Req() req) {
    const userId = req.user.id;
    return this.documentService.getDocumentById(id, userId);
  }

  @Get('documents/:id/raw')
  @UseGuards(JwtAuthGuard)
  async getRawFile(@Param('id') id: string, @Req() req, @Res() res: Response) {
    const userId = req.user.id;
    try {
      const { stream, filename, mimetype } = await this.documentService.getRawFile(id, userId);
      
      res.setHeader('Content-Type', mimetype);
      res.setHeader('Content-Disposition', `inline; filename="${filename}"`);
      
      stream.pipe(res);
    } catch (error) {
      throw new HttpException('Failed to fetch raw file', HttpStatus.INTERNAL_SERVER_ERROR);
    }
  }

  @Get('documents/:id/markdown')
  @UseGuards(JwtAuthGuard)
  async getParsedMarkdown(@Param('id') id: string, @Req() req) {
    const userId = req.user.id;
    return this.documentService.getParsedMarkdown(id, userId);
  }

  @Get('documents/:id/chunks')
  @UseGuards(JwtAuthGuard)
  async getDocumentChunks(@Param('id') id: string, @Req() req) {
    const userId = req.user.id;
    return this.documentService.getDocumentChunks(id, userId);
  }

  @Put('documents/:id')
  async updateDocument(@Param('id') id: string, @Body() updateData: any) {
    return this.documentService.updateDocument({ id, ...updateData });
  }

  // Add document deletion endpoint
  @Delete('documents/:id')
  @UseGuards(JwtAuthGuard)
  async deleteDocument(@Param('id') id: string, @Req() req) {
    const userId = req.user.id;
    return this.documentService.deleteDocument(id);
  }
}