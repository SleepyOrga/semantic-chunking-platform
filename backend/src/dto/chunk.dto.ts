import { IsNotEmpty, IsString, IsArray, IsNumber, IsOptional, IsUUID, Min, ArrayMinSize, ArrayMaxSize, Max, IsBoolean} from 'class-validator';

export class AddChunkDto {
  @IsNotEmpty()
  @IsUUID()
  document_id: string;

  @IsNotEmpty()
  @IsNumber()
  @Min(0)
  chunk_index: number;

  @IsNotEmpty()
  @IsString()
  content: string;

  @IsOptional()
  @IsArray()
  @ArrayMinSize(1536)
  @ArrayMaxSize(1536)
  embedding?: number[];

  @IsOptional()
  @IsArray()
  @IsString({ each: true })
  tags?: string[];
}

export class UpdateChunkDto {
  @IsNotEmpty()
  @IsUUID()
  id: string;

  @IsOptional()
  @IsString()
  content?: string;

  @IsOptional()
  @IsArray()
  @ArrayMinSize(1536)
  @ArrayMaxSize(1536)
  embedding?: number[];

  @IsOptional()
  @IsArray()
  @IsString({ each: true })
  tags?: string[];
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
  limit?: number;

  @IsOptional()
  @IsNumber()
  @Min(0)
  @Max(1)
  threshold?: number;
}

export class TagSearchDto {
  @IsNotEmpty()
  @IsArray()
  @IsString({ each: true })
  @ArrayMinSize(1)
  tags: string[];

  @IsOptional()
  @IsBoolean()
  matchAll?: boolean;

  @IsOptional()
  @IsNumber()
  @Min(1)
  limit?: number;
}

export class ChunkTagsDto {
  @IsNotEmpty()
  @IsArray()
  @IsString({ each: true })
  @ArrayMinSize(1)
  tags: string[];
}