import { Module } from '@nestjs/common';
import { ParserGatewayService } from './parser-gateway.service';
import { QueueModule } from '../queue/queue.module';

@Module({
  imports: [QueueModule],
  providers: [ParserGatewayService],
  exports: [ParserGatewayService],
})
export class ParserGatewayModule {}
