#!/bin/bash

set -e

# Remote DB credentials
REMOTE_HOST="34.47.219.225"
REMOTE_PORT="5432"
REMOTE_DB="unitedb"
REMOTE_USER="unitedb_user"
REMOTE_PASSWORD="password123"

# Local container DB credentials
LOCAL_CONTAINER_NAME="postgres-clone"
LOCAL_DB="unitedb"
LOCAL_USER="jalaj"
LOCAL_PASSWORD="password123"
LOCAL_PORT="5433"  # Avoid conflict if port 5432 is in use

# Dump file name
DUMP_FILE="unitedb_backup.dump"

echo "🛑 Stopping and removing existing container if it exists..."
docker rm -f $LOCAL_CONTAINER_NAME 2>/dev/null || true

echo "🗃️ Creating Docker volume for persistence..."
docker volume create pgdata_clone

echo "🐳 Starting new PostgreSQL container: $LOCAL_CONTAINER_NAME..."
docker run -d \
  --name $LOCAL_CONTAINER_NAME \
  -e POSTGRES_USER=$LOCAL_USER \
  -e POSTGRES_PASSWORD=$LOCAL_PASSWORD \
  -e POSTGRES_DB=$LOCAL_DB \
  -v pgdata_clone:/var/lib/postgresql/data \
  -p $LOCAL_PORT:5432 \
  postgres

echo "⏳ Waiting for the new PostgreSQL container to be ready..."
sleep 10  # crude wait; use healthchecks for production

echo "📦 Dumping remote database: $REMOTE_DB from $REMOTE_HOST..."
PGPASSWORD=$REMOTE_PASSWORD pg_dump -h $REMOTE_HOST -p $REMOTE_PORT -U $REMOTE_USER -d $REMOTE_DB -F c -f $DUMP_FILE

echo "🛠️ Creating target database in container..."
PGPASSWORD=$LOCAL_PASSWORD createdb -h localhost -p $LOCAL_PORT -U $LOCAL_USER $LOCAL_DB || true

echo "📥 Restoring dump into new container..."
PGPASSWORD=$LOCAL_PASSWORD pg_restore -h localhost -p $LOCAL_PORT -U $LOCAL_USER -d $LOCAL_DB -c $DUMP_FILE

echo "✅ Done! New DB is running in container '$LOCAL_CONTAINER_NAME' on port $LOCAL_PORT"
