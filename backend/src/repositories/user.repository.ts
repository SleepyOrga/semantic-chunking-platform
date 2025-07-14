import { Injectable, Inject } from '@nestjs/common';
import { Knex } from 'knex';
import * as bcrypt from 'bcrypt';

@Injectable()
export class UserRepository {
  constructor(@Inject('KNEX_CONNECTION') private readonly knex: Knex) {}

  async findOneByEmail(email: string): Promise<any> {
    return this.knex('users')
      .where('email', email.toLowerCase())
      .first();
  }

  async findOneById(id: string): Promise<any> {
    return this.knex('users')
      .where('id', id)
      .first();
  }

  async createUser(userData: { email: string; password: string; full_name: string }): Promise<any> {
    const { email, password, full_name } = userData;
    
    // Generate salt and hash the password
    const salt = await bcrypt.genSalt();
    const password_hash = await bcrypt.hash(password, salt);
    
    // Use the UUID generator from PostgreSQL
    const [user] = await this.knex('users')
      .insert({
        email: email.toLowerCase(),
        password_hash,
        full_name,
        // created_at will be auto-filled by the default value
      })
      .returning(['id', 'email', 'full_name', 'created_at']);
    
    return user;
  }

  async validatePassword(plainTextPassword: string, hashedPassword: string): Promise<boolean> {
    return bcrypt.compare(plainTextPassword, hashedPassword);
  }
}