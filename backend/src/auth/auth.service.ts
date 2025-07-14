import { Injectable, UnauthorizedException, ConflictException, InternalServerErrorException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { UserRepository } from '../repositories/user.repository';
import { LoginDto, RegisterDto, AuthResponseDto } from '../dto/auth.dto';

@Injectable()
export class AuthService {
  constructor(
    private userRepository: UserRepository,
    private jwtService: JwtService,
  ) {}

  async login(loginDto: LoginDto): Promise<AuthResponseDto> {
    const { email, password } = loginDto;
    
    // Find user by email
    const user = await this.userRepository.findOneByEmail(email);
    if (!user) {
      throw new UnauthorizedException('Invalid credentials');
    }
    
    // Validate password
    const isPasswordValid = await this.userRepository.validatePassword(
      password,
      user.password_hash,
    );
    
    if (!isPasswordValid) {
      throw new UnauthorizedException('Invalid credentials');
    }
    
    // Generate JWT token
    const payload = { sub: user.id, email: user.email };
    const token = this.jwtService.sign(payload);
    
    return {
      id: user.id,
      email: user.email,
      full_name: user.full_name,
      token,
    };
  }

  async register(registerDto: RegisterDto): Promise<AuthResponseDto> {
    const { email, password, full_name } = registerDto;
    
    // Check if user exists
    const existingUser = await this.userRepository.findOneByEmail(email);
    if (existingUser) {
      throw new ConflictException('Email already in use');
    }
    
    try {
      // Create user
      const user = await this.userRepository.createUser({
        email,
        password,
        full_name,
      });
      
      // Generate JWT token
      const payload = { sub: user.id, email: user.email };
      const token = this.jwtService.sign(payload);
      
      return {
        id: user.id,
        email: user.email,
        full_name: user.full_name,
        token,
      };
    } catch (error) {
      console.error('Registration error:', error);
      throw new InternalServerErrorException('Failed to create user');
    }
  }

  async validateUser(id: string): Promise<any> {
    const user = await this.userRepository.findOneById(id);
    if (!user) {
      throw new UnauthorizedException('User not found');
    }
    
    // Remove sensitive information
    delete user.password_hash;
    
    return user;
  }
}