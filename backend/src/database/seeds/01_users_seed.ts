import { Knex } from 'knex';
import * as bcrypt from 'bcrypt';

export async function seed(knex: Knex): Promise<void> {
  // Deletes ALL existing entries
  await knex('users').del();

  // Generate hashed passwords
  const passwordHash = await bcrypt.hash('password123', 10);
  
  // Create test users with hardcoded UUIDs
  const users = [
    {
      id: "05b207af-8ea7-4a72-8c37-f5723303d01e",
      email: 'admin@example.com',
      password_hash: passwordHash,
      full_name: 'Admin User',
      created_at: new Date()
    },
    {
      id: "7c11e1ce-1144-42bf-92d8-59392314e0c0",
      email: 'user1@example.com',
      password_hash: passwordHash,
      full_name: 'Test User One',
      created_at: new Date()
    },
    {
      id: "3b9ad953-7245-42e8-a8c8-8ff1a5986f89",
      email: 'user2@example.com',
      password_hash: passwordHash,
      full_name: 'Test User Two',
      created_at: new Date()
    },
    {
      id: "d4f25424-7b17-4b88-b9c4-20ea66655a05",
      email: 'demo@example.com',
      password_hash: passwordHash,
      full_name: 'Demo Account',
      created_at: new Date()
    }
  ];

  // Log the generated users for reference
  console.log('Seeded users:');
  users.forEach(user => {
    console.log(`- ${user.full_name} (${user.email}): ${user.id}`);
  });

  // Insert users
  await knex('users').insert(users);
  
  console.log(`✅ Successfully inserted ${users.length} users`);
}