#!/bin/bash

# setup_db.sh

# Check if migration message was provided
if [ -z "$1" ]
then
    echo "Please provide a migration message"
    echo "Usage: ./setup_db.sh \"Your migration message\""
    exit 1
fi

# Store the migration message
MIGRATION_MESSAGE="$1"

# Print start message
echo "Starting database setup..."

# Remove old migrations and database
echo "Removing old migrations and database..."
rm -rf migrations
dropdb wedding_db

# Create new database
echo "Creating new database..."
createdb wedding_db

# Initialize and create new migrations
echo "Initializing Flask migrations..."
flask db init

echo "Creating new migration with message: $MIGRATION_MESSAGE"
flask db migrate -m "$MIGRATION_MESSAGE"

echo "Applying migrations..."
flask db upgrade

# Seed initial data
echo "Seeding initial data..."
python seed.py

echo "Setup completed successfully!"