#!/bin/bash

# FreshRoute Setup Verification Script
# Checks if all prerequisites and configurations are in place

echo "🔍 FreshRoute Setup Verification"
echo "=================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

errors=0
warnings=0

# Check Python
echo "📦 Checking Python..."
if command -v python3 &> /dev/null; then
    version=$(python3 --version 2>&1)
    if [[ $version == *"3.13"* ]] || [[ $version == *"3.12"* ]] || [[ $version == *"3.11"* ]]; then
        echo -e "${GREEN}✓${NC} Python: $version"
    else
        echo -e "${YELLOW}⚠${NC} Python: $version (3.13+ recommended)"
        ((warnings++))
    fi
else
    echo -e "${RED}✗${NC} Python not found"
    ((errors++))
fi

# Check Node.js
echo ""
echo "📦 Checking Node.js..."
if command -v node &> /dev/null; then
    version=$(node --version)
    echo -e "${GREEN}✓${NC} Node.js: $version"
else
    echo -e "${RED}✗${NC} Node.js not found"
    ((errors++))
fi

# Check npm
echo ""
echo "📦 Checking npm..."
if command -v npm &> /dev/null; then
    version=$(npm --version)
    echo -e "${GREEN}✓${NC} npm: $version"
else
    echo -e "${RED}✗${NC} npm not found"
    ((errors++))
fi

# Check uv (optional)
echo ""
echo "📦 Checking uv (optional)..."
if command -v uv &> /dev/null; then
    version=$(uv --version)
    echo -e "${GREEN}✓${NC} uv: $version"
else
    echo -e "${YELLOW}⚠${NC} uv not found (pip install uv to use)"
    ((warnings++))
fi

# Check Docker (optional)
echo ""
echo "📦 Checking Docker (optional)..."
if command -v docker &> /dev/null; then
    version=$(docker --version)
    echo -e "${GREEN}✓${NC} Docker: $version"
else
    echo -e "${YELLOW}⚠${NC} Docker not found (needed for containerized deployment)"
    ((warnings++))
fi

# Check backend files
echo ""
echo "📁 Checking backend files..."
if [ -f "app/main.py" ]; then
    echo -e "${GREEN}✓${NC} app/main.py found"
else
    echo -e "${RED}✗${NC} app/main.py not found"
    ((errors++))
fi

if [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
    echo -e "${GREEN}✓${NC} Backend dependencies file found"
else
    echo -e "${RED}✗${NC} No requirements.txt or pyproject.toml found"
    ((errors++))
fi

if [ -f ".env.example" ]; then
    echo -e "${GREEN}✓${NC} .env.example found"
else
    echo -e "${YELLOW}⚠${NC} .env.example not found"
    ((warnings++))
fi

if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env configured"
else
    echo -e "${YELLOW}⚠${NC} .env not configured (copy from .env.example)"
    ((warnings++))
fi

# Check frontend files
echo ""
echo "📁 Checking frontend files..."
if [ -d "frontend" ]; then
    echo -e "${GREEN}✓${NC} frontend/ directory found"

    if [ -f "frontend/package.json" ]; then
        echo -e "${GREEN}✓${NC} frontend/package.json found"
    else
        echo -e "${RED}✗${NC} frontend/package.json not found"
        ((errors++))
    fi

    if [ -f "frontend/.env.local" ]; then
        echo -e "${GREEN}✓${NC} frontend/.env.local configured"
    else
        echo -e "${YELLOW}⚠${NC} frontend/.env.local not configured"
        ((warnings++))
    fi
else
    echo -e "${RED}✗${NC} frontend/ directory not found"
    ((errors++))
fi

# Check documentation
echo ""
echo "📚 Checking documentation..."
if [ -f "README.md" ]; then
    echo -e "${GREEN}✓${NC} README.md found"
else
    echo -e "${YELLOW}⚠${NC} README.md not found"
    ((warnings++))
fi

if [ -f "DEPLOYMENT.md" ]; then
    echo -e "${GREEN}✓${NC} DEPLOYMENT.md found"
else
    echo -e "${YELLOW}⚠${NC} DEPLOYMENT.md not found"
    ((warnings++))
fi

if [ -f "TECHNICAL_REPORT.md" ]; then
    echo -e "${GREEN}✓${NC} TECHNICAL_REPORT.md found"
else
    echo -e "${YELLOW}⚠${NC} TECHNICAL_REPORT.md not found"
    ((warnings++))
fi

# Summary
echo ""
echo "=================================="
if [ $errors -eq 0 ] && [ $warnings -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Backend:  cd . && uvicorn app.main:app --reload"
    echo "2. Frontend: cd frontend && npm run dev"
    echo "3. Visit:    http://localhost:3000"
else
    echo -e "${YELLOW}Setup verification complete${NC}"
    echo "Errors: $errors | Warnings: $warnings"
    echo ""
    if [ $errors -gt 0 ]; then
        echo -e "${RED}Please fix errors before proceeding${NC}"
    fi
    if [ $warnings -gt 0 ]; then
        echo -e "${YELLOW}Some optional components are missing${NC}"
    fi
fi
