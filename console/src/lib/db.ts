import { Pool } from "pg";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL || "postgresql://authclaw:authclaw@localhost:5432/authclaw",
});

export async function query(text: string, params?: any[]) {
  return pool.query(text, params);
}
