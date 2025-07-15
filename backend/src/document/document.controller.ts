// src/document/document.controller.ts
import { Controller, Get, Post, Body, Delete, Param, UseGuards, Req, UploadedFile, UseInterceptors } from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { DocumentService } from './document.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';

@Controller()
export class DocumentController {
  constructor(private readonly documentService: DocumentService) {}

  @Get('documents')
  @UseGuards(JwtAuthGuard)
  async getUserDocuments(@Req() req) {
    const userId = req.user.id;
    return this.documentService.getDocumentsByUserId(userId);
  }

  // Add document deletion endpoint
  @Delete('documents/:id')
  @UseGuards(JwtAuthGuard)
  async deleteDocument(@Param('id') id: string, @Req() req) {
    const userId = req.user.id;
    return this.documentService.deleteDocument(id);
  }
}