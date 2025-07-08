import { Module, Global } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import knex from 'knex';
import knexConfig from './knexfile';
import { KnexService } from './knex.service';

@Global()
@Module({
  imports: [ConfigModule],
  providers: [
    {
      provide: 'KNEX_CONNECTION',
      useFactory: () => {
        const environment = process.env.NODE_ENV || 'development';
        const config = knexConfig[environment];
        
        if (!config) {
          throw new Error(`No Knex configuration found for environment: ${environment}`);
        }
        
        return knex(config);
      },
    },
    KnexService,
  ],
  exports: ['KNEX_CONNECTION', KnexService],
})
export class KnexModule {}