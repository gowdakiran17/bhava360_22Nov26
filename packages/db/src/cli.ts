import { run } from './local.js';

const command = process.argv[2];
if (command !== 'up' && command !== 'down' && command !== 'seed') throw new Error('Expected up, down or seed');
run(command, process.env.DATABASE_URL, process.env.APP_ENV).catch(() => {
  console.error('Database operation failed. Check the loopback target, environment, permissions and migration state.');
  process.exitCode = 1;
});
