#!/bin/bash

echo "Starting Setup..."

# 1. Check for .env
if [ ! -f .env ]; then
    echo "⚠️  .env file not found! Copying from .env.example..."
    cp .env.example .env
    echo "✅ Created .env"
else
    echo "✅ .env already exists"
fi

# 2. Create data directories (Local only)
mkdir -p data/postgres data/mongo data/qdrant
echo "✅ Created local data directories"

# 3. Start Docker
echo "🐳 Spinning up containers..."
docker-compose up -d

echo "-----------------------------------"
echo "✅ Setup Complete!"
echo "📡 PostgreSQL running on port 5433"
echo "📡 MongoDB running on port 27017"
echo "📡 Qdrant running on port 6333"
echo "-----------------------------------"