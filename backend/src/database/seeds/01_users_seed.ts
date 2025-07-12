import { Knex } from 'knex';
import { v4 as uuidv4 } from 'uuid';
import * as bcrypt from 'bcrypt';

export async function seed(knex: Knex): Promise<void> {
  // Deletes ALL existing entries
  await knex('users').del();

  // Generate hashed passwords
  const passwordHash = await bcrypt.hash('password123', 10);
  
  // Create test users with UUIDs
  const users = [
    {
      id: uuidv4(),
      email: 'admin@example.com',
      password_hash: passwordHash,
      full_name: 'Admin User',
      created_at: new Date()
    },
    {
      id: uuidv4(),
      email: 'user1@example.com',
      password_hash: passwordHash,
      full_name: 'Test User One',
      created_at: new Date()
    },
    {
      id: uuidv4(),
      email: 'user2@example.com',
      password_hash: passwordHash,
      full_name: 'Test User Two',
      created_at: new Date()
    },
    {
      id: uuidv4(),
      email: 'demo@example.com',
      password_hash: passwordHash,
      full_name: 'Demo Account',
      created_at: new Date()
    }
  ];

  // Log the generated users for reference (especially in tests)
  console.log('Seeded users:');
  users.forEach(user => {
    console.log(`- ${user.full_name} (${user.email}): ${user.id}`);
  });

  // Insert users
  await knex('users').insert(users);
  
  console.log(`✅ Successfully inserted ${users.length} users`);
}