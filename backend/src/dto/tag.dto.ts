import { IsNotEmpty, IsString, MinLength, MaxLength, IsOptional, IsNumber } from 'class-validator';

export class CreateTagDto {
  @IsNotEmpty()
  @IsString()
  @MinLength(1)
  @MaxLength(50)
  name: string;
}

export class UpdateTagDto {
  @IsOptional()
  @IsString()
  @MinLength(1)
  @MaxLength(50)
  name?: string;
}

export class TagResponseDto {
  @IsNumber()
  id: number;
  
  @IsString()
  name: string;
  
  @IsString()
  created_at: string;
}