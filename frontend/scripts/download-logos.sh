#!/bin/bash

# Script to download MMA promotion logos
# Run from frontend directory: ./scripts/download-logos.sh

LOGOS_DIR="public/logos"
mkdir -p "$LOGOS_DIR"

echo "📥 Downloading MMA promotion logos..."

# UFC
curl -sL "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0d/UFC_logo.svg/320px-UFC_logo.svg.png" -o "$LOGOS_DIR/ufc.png"
echo "✓ UFC"

# Bellator (now part of PFL)
curl -sL "https://upload.wikimedia.org/wikipedia/en/thumb/4/4b/Bellator_MMA_logo.svg/320px-Bellator_MMA_logo.svg.png" -o "$LOGOS_DIR/bellator.png"
echo "✓ Bellator"

# ONE Championship
curl -sL "https://upload.wikimedia.org/wikipedia/en/thumb/1/1b/ONE_Championship_logo.svg/320px-ONE_Championship_logo.svg.png" -o "$LOGOS_DIR/one.png"
echo "✓ ONE Championship"

# PFL
curl -sL "https://upload.wikimedia.org/wikipedia/en/thumb/6/6a/Professional_Fighters_League_logo.svg/320px-Professional_Fighters_League_logo.svg.png" -o "$LOGOS_DIR/pfl.png"
echo "✓ PFL"

# KSW
curl -sL "https://upload.wikimedia.org/wikipedia/en/thumb/8/87/KSW_logo.svg/320px-KSW_logo.svg.png" -o "$LOGOS_DIR/ksw.png"
echo "✓ KSW"

# Cage Warriors
curl -sL "https://upload.wikimedia.org/wikipedia/en/thumb/4/4c/Cage_Warriors_logo.svg/320px-Cage_Warriors_logo.svg.png" -o "$LOGOS_DIR/cage-warriors.png"
echo "✓ Cage Warriors"

# LFA
curl -sL "https://upload.wikimedia.org/wikipedia/en/thumb/b/b4/Legacy_Fighting_Alliance_logo.svg/320px-Legacy_Fighting_Alliance_logo.svg.png" -o "$LOGOS_DIR/lfa.png"
echo "✓ LFA"

# BRAVE CF
curl -sL "https://upload.wikimedia.org/wikipedia/en/thumb/a/a4/Brave_CF_logo.svg/320px-Brave_CF_logo.svg.png" -o "$LOGOS_DIR/brave-cf.png"
echo "✓ BRAVE CF"

echo ""
echo "✅ All logos downloaded to $LOGOS_DIR"
echo ""
echo "Note: Some logos may need to be downloaded manually:"
echo "  - ACA: https://acaleague.com (get from official site)"
echo "  - OKTAGON: https://oktagonmma.com"
echo "  - UAE Warriors: https://uaewarriors.com"
echo "  - Ares FC: https://aresfc.com"

