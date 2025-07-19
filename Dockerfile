# Python 3.13 버전을 기반으로 이미지를 생성합니다.
FROM python:3.13-slim

# 작업 디렉토리를 /app으로 설정합니다.
WORKDIR /app

# uv 설치
RUN pip install uv

# 의존성 정의 파일을 복사합니다.
COPY pyproject.toml uv.lock ./

# uv를 사용하여 의존성을 설치합니다.
RUN uv pip install --system --no-cache .

# 나머지 프로젝트 파일들을 복사합니다.
COPY . .

# 애플리케이션을 실행할 명령어입니다.
CMD ["python", "src/main.py"]