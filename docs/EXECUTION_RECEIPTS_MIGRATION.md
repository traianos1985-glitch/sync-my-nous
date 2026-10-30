# Execution receipts database migration

The web application's Drizzle schema now includes `nous_execution_receipts`.
The table must exist before deploying code that writes or lists receipts.

## Apply to the intended PostgreSQL database

1. Take or verify a restorable database backup.
2. Confirm that `DATABASE_URL` points to the intended environment. Do not paste
   the connection string into logs, issues or pull requests.
3. From a trusted shell with PostgreSQL client tools installed, run:

   ```sh
   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f src/lib/db/migrations/0001_execution_receipts.sql
   ```

4. Verify the table and index exist:

   ```sql
   SELECT to_regclass('public.nous_execution_receipts');
   SELECT indexname
   FROM pg_indexes
   WHERE tablename = 'nous_execution_receipts';
   ```

The migration uses `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS`;
re-running it is safe. It does not alter or delete existing application data.

## Rollback

Do not automatically drop this table during an application rollback. Receipts
are operational audit evidence. If rollback is required, deploy the previous
application version and retain the table and its data. A destructive drop
requires an explicit backup and owner approval.
