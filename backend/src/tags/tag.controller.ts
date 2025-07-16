// src/tags/tags.controller.ts
import { Controller, Get, Post, Put, Delete, Body, Param, Query, UseGuards } from '@nestjs/common';
import { TagsService } from './tag.service';
import { CreateTagDto, UpdateTagDto } from '../dto/tag.dto';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';

@Controller('tags')
export class TagsController {
  constructor(private readonly tagsService: TagsService) {}

  @Get()
  async findAll(@Query('search') search?: string) {
    return this.tagsService.findAll(search);
  }

  @Get(':id')
  async findOne(@Param('id') id: number) {
    return this.tagsService.findOne(id);
  }

  @Post()
  async create(@Body() createTagDto: CreateTagDto) {
    return this.tagsService.create(createTagDto);
  }

  @Put(':id')
  async update(@Param('id') id: number, @Body() updateTagDto: UpdateTagDto) {
    return this.tagsService.update(id, updateTagDto);
  }

  @Delete(':id')
  async remove(@Param('id') id: number) {
    return this.tagsService.remove(id);
  }
}