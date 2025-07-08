#!/bin/bash

echo "🔧 Bio-Info pip 환경 구축 시작 (Python 3.10)..."

# 2. Python 3.10 설치 확인
echo "🐍 Python 3.10 확인 중..."
if ! command -v python3.10 &> /dev/null; then
    echo "📥 Python 3.10 설치 중..."
    sudo apt update
    sudo apt install -y python3.10 python3.10-venv python3.10-dev
fi

# 3. Python 3.10 가상환경 생성
echo "🏗️ Python 3.10 가상환경 생성 중..."
python3.10 -m venv bio-info-pip
source bio-info-pip/bin/activate

# 4. pip 업그레이드
echo "⬆️ pip 업그레이드 중..."
pip install --upgrade pip setuptools wheel

# 5. NumPy 1.26 먼저 설치
echo "🔢 NumPy 1.26 설치 중..."
pip install numpy==1.26.4

# 6. PyTorch CUDA 12.1 설치
echo "🔥 PyTorch CUDA 12.1 설치 중..."
pip install torch==2.2.0+cu121 torchvision==0.17.0+cu121 --extra-index-url https://download.pytorch.org/whl/cu121

# 7. 기본 과학 패키지들 설치
echo "📊 기본 과학 패키지들 설치 중..."
pip install pandas matplotlib seaborn

# 8. 나머지 패키지들 설치
echo "📚 나머지 패키지들 설치 중..."
pip install -r requirements.txt

# 9. OmegaFold 설치 (Python 3.10 지원)
echo "🧬 OmegaFold 설치 중..."
pip install git+https://github.com/HeliXonProtein/OmegaFold.git

# 10. 모델 가중치 다운로드
echo "📦 OmegaFold 모델 다운로드 중..."
mkdir -p ~/.cache/omegafold_ckpt
cd ~/.cache/omegafold_ckpt
wget -O model.pt https://helixon.s3.amazonaws.com/release1.pt

# 11. 실행 스크립트 생성
echo "📝 실행 스크립트 생성 중..."
cd ~/projects/Bio-Info
mkdir -p ~/bin
cat > ~/bin/omegafold << 'EOF'
#!/bin/bash
source ~/projects/Bio-Info/bio-info-pip/bin/activate
python -m omegafold "$@"
EOF

chmod +x ~/bin/omegafold

# 12. PATH 설정
echo "🔗 PATH 설정 중..."
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
export PATH="$HOME/bin:$PATH"

# 13. fpocket 설치 (선택) — 포켓 자동 탐지를 위해 권장
echo "🕳️ fpocket 설치 중 (없으면 빌드)..."
if ! command -v fpocket &> /dev/null; then
    # APT 패키지가 없는 경우가 많으므로 소스 빌드 시도
    sudo apt-get update
    sudo apt-get install -y git build-essential
    git clone --depth 1 https://github.com/Discngine/fpocket.git /tmp/fpocket && cd /tmp/fpocket
    make && sudo make install
    cd -
else
    echo "✅ fpocket already installed: $(which fpocket)"
fi

# 14. 설치 확인
echo "✅ 설치 확인 중..."
python --version
python -c "import torch; print(f'✅ PyTorch {torch.__version__} (CUDA: {torch.cuda.is_available()})')"
python -c "import numpy; print(f'✅ NumPy {numpy.__version__}')"
python -c "import pandas; print(f'✅ Pandas {pandas.__version__}')"
python -c "import omegafold; print('✅ OmegaFold 설치 완료')"
python -c "import auto_hypothesis_agent; print('✅ 로컬 패키지 설치 완료')"

echo "🎉 Python 3.10 pip 환경 구축 완료!"
echo "🚀 환경 활성화: source bio-info-pip/bin/activate"
echo "🧬 OmegaFold 사용법: omegafold input.fasta output_dir"