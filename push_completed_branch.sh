#!/bin/bash
# Script to create completed-1 branch and push to GitHub
# Run this in WSL terminal

set -e

echo "=== Creating and Pushing completed-1 Branch ==="
echo ""

cd "$(dirname "$0")" || exit

# Step 1: Check if git is initialized
if [ ! -d .git ]; then
    echo "Initializing git repository..."
    git init
fi

# Step 2: Check current branch and status
echo "1. Checking git status..."
git status --short || true

# Step 3: Create or switch to completed-1 branch
echo ""
echo "2. Creating/switching to completed-1 branch..."
if git branch --list | grep -q "completed-1"; then
    echo "   Branch 'completed-1' already exists, switching to it..."
    git checkout completed-1
else
    echo "   Creating new branch 'completed-1'..."
    git checkout -b completed-1
fi

# Step 4: Clean up any remaining temporary files
echo ""
echo "3. Final cleanup..."
rm -f fix_*.sh upgrade_*.sh reset_*.sh check_*.sh clean_*.sh install_*.sh setup.sh 2>/dev/null || true
rm -f =*.0 2>/dev/null || true
rm -rf test_chroma_db chroma_db_backup_* 2>/dev/null || true

# Step 5: Stage all changes
echo ""
echo "4. Staging all changes..."
git add -A

# Step 6: Check what will be committed
echo ""
echo "5. Changes to be committed:"
git status --short

# Step 7: Commit changes
echo ""
echo "6. Committing changes..."
git commit -m "feat: Complete milestone 1 - Multi-modal RAG, Pathway streaming, React frontend

✅ Implemented Features:
- Multi-modal RAG system with text (Sentence-Transformers) and image (CLIP) embeddings
- GPT-4 Vision integration for satellite imagery analysis
- Pathway streaming pipeline with 3 data sources (GDACS, NewsAPI, NASA EONET)
- Real-time event processing with incremental vector store updates
- React frontend with modern UI (Vite, Tailwind CSS, Leaflet, Recharts)
- Markdown-formatted RAG responses with beautiful styling
- FastAPI backend with REST API and WebSocket real-time updates
- Interactive disaster map with live event visualization
- Statistics dashboard with risk assessment

🧹 Project Cleanup:
- Removed temporary fix scripts and error files
- Organized test files into tests/ directory
- Updated .gitignore with comprehensive patterns
- Created comprehensive README.md with full documentation

📚 Documentation:
- Complete README.md with installation, architecture, and API docs
- COMPLETED_1_SUMMARY.md with milestone details
- BRANCH_SETUP_INSTRUCTIONS.md for reference"

# Step 8: Configure remote if not exists
echo ""
echo "7. Configuring remote repository..."
if ! git remote | grep -q "origin"; then
    echo "   Adding remote origin..."
    git remote add origin https://github.com/Manoj-dj/DataQuest2026.git
else
    echo "   Remote origin already exists"
    git remote set-url origin https://github.com/Manoj-dj/DataQuest2026.git
fi

# Step 9: Push branch to GitHub
echo ""
echo "8. Pushing completed-1 branch to GitHub..."
git push -u origin completed-1

echo ""
echo "=== ✅ Successfully pushed completed-1 branch to GitHub ==="
echo ""
echo "Repository: https://github.com/Manoj-dj/DataQuest2026"
echo "Branch: completed-1"
echo ""
echo "You can view the branch at:"
echo "https://github.com/Manoj-dj/DataQuest2026/tree/completed-1"
echo ""
