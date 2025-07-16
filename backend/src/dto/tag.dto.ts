import { IsNotEmpty, IsString, MinLength, MaxLength, IsOptional, IsNumber } from 'class-validator';

export class CreateTagDto {
  @IsNotEmpty()
  @IsString()
  @MinLength(2)
  @MaxLength(255)
  name: string;
}

export class UpdateTagDto {
  @IsNotEmpty()
  @IsString()
  @MinLength(2)
  @MaxLength(255)
  name: string;
}

export class TagResponseDto {
  @IsNumber()
  id: number;
  
  @IsString()
  name: string;
  
  @IsString()
  created_at: string;
}