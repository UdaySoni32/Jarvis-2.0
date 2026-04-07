# 🚀 JARVIS 2.0 Quick Start

## For Your Ubuntu Machine

### Option 1: Automated Setup (Recommended)

```bash
# Clone and setup in one go
git clone https://github.com/UdaySoni32/Jarvis-2.0.git
cd Jarvis-2.0
bash quick_setup.sh
```

### Option 2: Manual Setup

```bash
# 1. Clone repository
git clone https://github.com/UdaySoni32/Jarvis-2.0.git
cd Jarvis-2.0

# 2. Install system dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-venv scrot tesseract-ocr xclip xsel

# 3. Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Run tests
python -m pytest tests/ -v
```

## Test Everything Works

```bash
# Activate environment
source venv/bin/activate

# Run all tests (70+ tests should pass)
python -m pytest tests/ -v

# Expected output:
# ====== 70+ passed in X.XXs ======
```

## Quick Test Individual Features

```bash
# Test Database Integration
python -m pytest tests/test_database_integration.py -v

# Test GitHub Integration  
python -m pytest tests/test_github_integration.py -v

# Test Docker Integration
python -m pytest tests/test_docker_integration.py -v

# Test Clipboard Manager
python -m pytest tests/test_clipboard_manager.py -v

# Test API Testing
python -m pytest tests/test_api_testing.py -v

# Test Screen Capture & OCR
python -m pytest tests/test_screen_capture_ocr.py -v
```

## Configure JARVIS

```bash
# Run setup wizard
python -m src.setup_wizard

# You'll need:
# - OpenAI API key (get from https://platform.openai.com)
# - Choose AI model (gpt-4, gpt-3.5-turbo, etc.)
# - Configure plugins
```

## Start JARVIS

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Start JARVIS
python main.py
```

## First Commands to Try

Once JARVIS is running:

```
> Hello JARVIS, introduce yourself
> What's my system information?
> List all available plugins
> Show me what you can do
> Create a task to test all features tomorrow
```

## ✅ Success Indicators

- [ ] Repository cloned
- [ ] 70+ tests passing
- [ ] JARVIS starts without errors
- [ ] Can interact with JARVIS
- [ ] Plugins respond correctly

## 📚 Need More Details?

- **Setup Guide**: See `SETUP_GUIDE.md`
- **Test Commands**: See `TEST_COMMANDS.md`
- **Full Plan**: See `PROJECT_PLAN.md`
- **README**: See `README.md`

## 🆘 Troubleshooting

### Tests fail?
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Permission errors?
```bash
# Use --user flag
pip install -r requirements.txt --user
```

### Docker tests fail?
```bash
# Install Docker
sudo apt install -y docker.io
sudo usermod -aG docker $USER
newgrp docker
```

## 🎉 That's It!

You're ready to test JARVIS 2.0 on your Ubuntu machine!

---

**Repository**: https://github.com/UdaySoni32/Jarvis-2.0.git  
**Total Tests**: 70+  
**Plugins**: 8 advanced integrations  
**Status**: Production ready ✅
