import { IsNotEmpty, IsString, IsArray, IsNumber, IsOptional, IsUUID, Min, Max, ArrayMinSize, ArrayMaxSize } from 'class-validator';

export class CreateChunkComponentDto {
  @IsNotEmpty()
  @IsUUID()
  chunk_id: string;

  @IsNotEmpty()
  @IsNumber()
  @Min(0)
  component_index: number;

  @IsNotEmpty()
  @IsString()
  content: string;

  @IsOptional()
  @IsArray()
  @ArrayMinSize(1536)
  @ArrayMaxSize(1536)
  embedding?: number[];
}

export class UpdateChunkComponentDto {
  @IsOptional()
  @IsNumber()
  @Min(0)
  component_index?: number;

  @IsOptional()
  @IsString()
  content?: string;

  @IsOptional()
  @IsArray()
  @ArrayMinSize(1536)
  @ArrayMaxSize(1536)
  embedding?: number[];
}

export class SimilaritySearchDto {
  @IsNotEmpty()
  @IsArray()
  @ArrayMinSize(1536)
  @ArrayMaxSize(1536)
  embedding: number[];

  @IsOptional()
  @IsNumber()
  @Min(1)
  @Max(100)
  limit?: number;

  @IsOptional()
  @IsNumber()
  @Min(0)
  @Max(1)
  threshold?: number;
}