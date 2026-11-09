# Image Viewer - Streamlit 배포용

원래의 이미지 처리 코드는 `ImageViewerQT.py`에 유지하고, `Streamlit.py`에서 `ImageProcessor`를 가져다 사용하는 프로젝트입니다.

## 구성

- `Streamlit.py`: Streamlit 웹 화면 및 버튼 (배포 진입 파일)
- `ImageViewerQT.py`: 공통 이미지 처리 로직 + 기존 PyQt 프로그램
- `imageViewer.ui`: 기존 PyQt 화면 파일 (웹 배포에는 사용하지 않음)
- `requirements.txt`: Streamlit 서버에서 설치할 패키지 목록
- `.streamlit/config.toml`: Streamlit 테마 및 업로드 용량 설정
- `.gitignore`: GitHub에 올리지 않을 로컬/비밀 파일 설정

## Streamlit 실행 (로컬)

프로젝트 폴더에서 터미널을 열고 다음을 실행합니다.

```bash
python -m pip install -r requirements.txt
python -m streamlit run Streamlit.py
```

## Streamlit Community Cloud 배포

1. 이 프로젝트 폴더 **안의 파일과 `.streamlit` 폴더**를 GitHub 저장소에 올립니다.
2. https://share.streamlit.io/ 에 로그인하여 `Create app`을 선택합니다.
3. Repository와 Branch (`main` 등)를 선택하고 `Main file path`를 `Streamlit.py`로 설정합니다.
4. `Deploy`를 실행합니다. `requirements.txt`는 서버가 자동으로 읽습니다.

> ZIP을 GitHub에 압축 파일 하나로 올리기보다는, ZIP을 먼저 풀어서 파일과 폴더 구조를 그대로 업로드하세요.

## 기존 PyQt 프로그램 (선택)

데스크톱 버전도 실행하려면 PyQt5를 별도로 설치해야 합니다.

```bash
python -m pip install PyQt5
python ImageViewerQT.py
```

## 원본 대비 수정 사항

- `ImageViewerQT.py`, `imageViewer.ui`: 원본 파일 그대로 유지
- `Streamlit.py`: 호모그래피 이미지 표시에서 `width="content"` 한 줄을, 클릭 좌표 라이브러리에서 지원하는 `use_column_width="auto"`로 변경
- `requirements.txt`: 서버 환경을 위해 `opencv-python`을 `opencv-python-headless`로 변경
- `.streamlit/config.toml` 및 배포 안내 파일 추가

이미지 편집 기능(흑백, 10% 자르기, 90도 회전, 블러, 밝기, 호모그래피, 원본 복원, 저장)은 기존 코드에 따라 동작합니다. 웹 버전에는 PyQt의 자동 슬라이드쇼가 포함되지 않습니다.
