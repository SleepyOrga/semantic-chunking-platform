import { Injectable, UnauthorizedException } from '@nestjs/common';
import { PassportStrategy } from '@nestjs/passport';
import { ExtractJwt, Strategy } from 'passport-jwt';
import { ConfigService } from '@nestjs/config';
import { UserRepository } from '../../repositories/user.repository';

@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy) {
  constructor(
    private configService: ConfigService,
    private userRepository: UserRepository,
  ) {
    super({
      jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
      secretOrKey: configService.get<string>('JWT_SECRET') || 'semantic-chunking-platform-secret',
    });
  }

  async validate(payload: { sub: string; email: string }): Promise<any> {
    const { sub: id } = payload;
    const user = await this.userRepository.findOneById(id);
    
    if (!user) {
      throw new UnauthorizedException('Invalid token');
    }
    
    // Remove sensitive information
    delete user.password_hash;
    
    return user;
  }
}