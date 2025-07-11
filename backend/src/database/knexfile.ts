import { config } from 'dotenv';
import { Knex } from 'knex';
import * as path from 'path';

// Load environment variables from project root
const environment = process.env.NODE_ENV || 'development';
const envFile = environment === 'production' ? '.env.production' : '.env.development';

// Use process.cwd() to get the project root directory
const envPath = path.resolve(process.cwd(), envFile);
console.log('🔍 Looking for env file at:', envPath);
const result = config({ path: envPath });
console.log('📄 Env file loaded?', result.parsed ? 'Yes' : 'No');

console.log(`Loading knexfile for environment: ${environment}`);
console.log(`Loading env file: ${envFile}`);
console.log(`DB_HOST: ${process.env.DB_HOST}`);
console.log(`DB_USER: ${process.env.DB_USER}`);
console.log(`DB_PORT: ${process.env.DB_PORT}`);

const knexConfig: Record<string, Knex.Config> = {
  development: {
    client: 'postgresql',
    connection: {
      host: process.env.DB_HOST || 'localhost',
      port: parseInt(process.env.DB_PORT || '5433'),
      user: process.env.DB_USER || 'app_user',
      password: process.env.DB_PASSWORD || 'secret123',
      database: process.env.DB_NAME || 'app_db',
    },
    migrations: {
      directory: path.join(__dirname, 'migrations'),
      extension: 'ts',
      tableName: 'knex_migrations',
    },
    seeds: {
      directory: path.join(__dirname, 'seeds'),
      extension: 'ts',
    },
    pool: {
      min: 2,
      max: 10,
    },
  },
  
  test: {
    client: 'postgresql',
    connection: {
      host: process.env.DB_HOST || 'localhost',
      port: parseInt(process.env.DB_PORT || '5433'),
      user: process.env.DB_USER || 'app_user',
      password: process.env.DB_PASSWORD || 'secret123',
      database: (process.env.DB_NAME || 'app_db') + '_test',
    },
    migrations: {
      directory: path.join(__dirname, 'migrations'),
      extension: 'ts',
      tableName: 'knex_migrations',
    },
    pool: {
      min: 1,
      max: 2,
    },
  },
  
  production: {
    client: 'postgresql',
    connection: {
      host: process.env.DB_HOST,
      port: parseInt(process.env.DB_PORT || '5432'),
      user: process.env.DB_USER,
      password: process.env.DB_PASSWORD,
      database: process.env.DB_NAME,
      ssl: process.env.DB_SSL === 'true' ? { rejectUnauthorized: false } : false,
    },
    migrations: {
      directory: path.join(__dirname, 'migrations'),
      extension: 'ts',
      tableName: 'knex_migrations',
    },
    pool: {
      min: 2,
      max: 20,
    },
  },
};

export default knexConfig;