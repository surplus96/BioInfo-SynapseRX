#!/bin/bash

echo "🧬 OmegaFold 설치 시작..."

# 1. 가상환경 활성화 확인
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️ 가상환경을 먼저 활성화하세요: source bio-info-pip/bin/activate"
    exit 1
fi

# 2. Git clone OmegaFold 저장소
echo "📥 OmegaFold 저장소 클론 중..."
cd /tmp
git clone https://github.com/HeliXonProtein/OmegaFold.git
cd OmegaFold

# 3. OmegaFold 설치
echo "🔧 OmegaFold 설치 중..."
pip install -e .

# 4. 모델 가중치 다운로드
echo "📦 모델 가중치 다운로드 중..."
mkdir -p ~/.cache/omegafold_ckpt
cd ~/.cache/omegafold_ckpt

# 모델 파일 다운로드 (약 2GB)
wget -O model.pt https://helixon.s3.amazonaws.com/release1.pt

# 5. 실행 스크립트 생성
echo "📝 실행 스크립트 생성 중..."
cat > ~/bin/omegafold << 'EOF'
#!/bin/bash
# OmegaFold 실행 스크립트
source ~/projects/Bio-Info/bio-info-pip/bin/activate
python -m omegafold "$@"
EOF

# 6. 실행 권한 부여
chmod +x ~/bin/omegafold

# 7. PATH에 추가 (bashrc 업데이트)
echo "🔗 PATH 설정 중..."
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
export PATH="$HOME/bin:$PATH"

# 8. 설치 확인
echo "✅ 설치 확인 중..."
python -c "import omegafold; print('✅ OmegaFold 모듈 임포트 성공')"
omegafold --help

echo "🎉 OmegaFold 설치 완료!"
echo "🚀 사용법: omegafold input.fasta output_dir"
echo "📂 모델 위치: ~/.cache/omegafold_ckpt/model.pt" 