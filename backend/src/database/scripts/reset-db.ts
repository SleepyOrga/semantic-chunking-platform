// run this D:\semantic-chunking-platform\backend\src\database> npx cross-env NODE_ENV=production npx ts-node scripts/reset-db.ts or drop the NODE_ENV=production if you want to run in dev mode
import { promises as fs } from 'fs';
import * as path from 'path';
import knex from 'knex';
import knexConfig from '../knexfile';

async function resetDatabase(mode: 'drop' | 'clean') {
  console.log(`Starting database ${mode} operation...`);

  const config = knexConfig.development; // becareful with knex.config.production in production
  const db = knex(config);

  try {
    const sqlFile =
      mode === 'drop'
        ? path.join(__dirname, 'drop_all_tables.sql')
        : path.join(__dirname, 'clean_all_tables.sql');

    console.log(`Reading SQL file: ${sqlFile}`);

    const sql = await fs.readFile(sqlFile, 'utf8');

    await db.raw(sql);
    console.log(`Database ${mode} completed successfully`);

    if (mode === 'drop') {
      console.log('Running migrations to recreate schema...');
      await db.migrate.latest();
      console.log('Migrations completed');
    }
  } catch (error) {
    console.error(`Error during database ${mode}:`, error);
  } finally {
    await db.destroy();
  }
}

// Get command line argument
const mode = process.argv[2] === 'clean' ? 'clean' : 'drop';
resetDatabase(mode);
