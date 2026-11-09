# Streamlit Version
# 실제 이미지 처리는 ImageViewerQT.py의 ImageProcessor를 그대로 사용한다.

import os
import random
import streamlit as st
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates

import ImageViewerQT as iv

st.set_page_config(page_title="Image Viewer", layout="wide")
st.title("Image Viewer - Streamlit")


# ------------------------------------------------------------
# ImageViewerQT.py의 공용 이미지 처리 객체를 세션에 보관
if "processor" not in st.session_state:
    st.session_state.processor = iv.ImageProcessor()

if "files" not in st.session_state:
    st.session_state.files = []
    st.session_state.index = 0
    st.session_state.homographyMode = False
    st.session_state.h_points = []
    st.session_state.clickTime = None

viewer = st.session_state.processor


def loadUploadedFile(uploadedFile):
    if uploadedFile is None:
        return

    viewer.loadImageBytes(uploadedFile.getvalue())
    st.session_state.homographyMode = False
    st.session_state.h_points = []


def nextImage():
    if len(st.session_state.files) == 0:
        return

    st.session_state.index += 1

    if st.session_state.index >= len(st.session_state.files):
        st.session_state.index = 0

    loadUploadedFile(st.session_state.files[st.session_state.index])
# ------------------------------------------------------------


# ------------------------------------------------------------
# 파일 / 폴더 선택
with st.sidebar:
    st.header("Image Select")

    selectedFile = st.file_uploader(
        "Select File",
        type=["jpg", "jpeg", "png"],
        key="singleFile"
    )

    if st.button("Open File", use_container_width=True):
        if selectedFile is not None:
            st.session_state.files = [selectedFile]
            st.session_state.index = 0
            loadUploadedFile(selectedFile)

    selectedFolder = st.file_uploader(
        "Select Folder",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files="directory",
        key="folderFiles"
    )

    if st.button("Open Folder", use_container_width=True):
        if selectedFolder:
            st.session_state.files = sorted(
                selectedFolder,
                key=lambda file: file.name
            )
            st.session_state.index = 0
            loadUploadedFile(st.session_state.files[0])
# ------------------------------------------------------------


# ------------------------------------------------------------
# 이미지 이동
col1, col2 = st.columns(2)

if col1.button("Next", use_container_width=True):
    nextImage()

if col2.button("Shuffle", use_container_width=True):
    if st.session_state.files:
        random.shuffle(st.session_state.files)
        st.session_state.index = 0
        loadUploadedFile(st.session_state.files[0])


# ------------------------------------------------------------
# 이미지 편집 -> 실제 처리는 ImageViewerQT.py의 메서드를 호출
st.subheader("Image Edit")
cols = st.columns(8)

buttons = [
    ("B/W", viewer.BWImage),
    ("Crop", viewer.croppingImage),
    ("Rotate", viewer.rotationImage),
    ("Blur", viewer.blurringImage),
    ("Bright +", viewer.bright1Image),
    ("Bright -", viewer.bright2Image),
]

for col, (name, function) in zip(cols, buttons):
    if col.button(name, use_container_width=True):
        function()
        st.session_state.homographyMode = False
        st.session_state.h_points = []

if cols[6].button("Homography", use_container_width=True):
    if viewer.currentImage is not None:
        st.session_state.homographyMode = not st.session_state.homographyMode
        st.session_state.h_points = []
        st.session_state.clickTime = None

if cols[7].button("Rollback", use_container_width=True):
    viewer.rollbackImage()
    st.session_state.homographyMode = False
    st.session_state.h_points = []
# ------------------------------------------------------------


# ------------------------------------------------------------
# 이미지 출력 / 호모그래피 점 선택
if viewer.currentImage is None:
    st.info("왼쪽에서 이미지를 불러오세요.")

elif st.session_state.homographyMode:
    st.info(
        f"호모그래피: 이미지에서 4개의 점을 클릭하세요. "
        f"({len(st.session_state.h_points)}/4)"
    )

    preview = viewer.getHomographyPreview(st.session_state.h_points)

    value = streamlit_image_coordinates(
        Image.fromarray(preview),
        use_column_width="auto",
        key=f"homography_{len(st.session_state.h_points)}"
    )

    if value is not None and value.get("unix_time") != st.session_state.clickTime:
        st.session_state.clickTime = value.get("unix_time")

        img_h, img_w = viewer.currentImage.shape[:2]
        show_w = value.get("width", img_w)
        show_h = value.get("height", img_h)

        x = value["x"] * img_w / show_w
        y = value["y"] * img_h / show_h

        st.session_state.h_points.append((x, y))

        if len(st.session_state.h_points) == 4:
            viewer.applySelectedHomography(st.session_state.h_points)
            st.session_state.homographyMode = False
            st.session_state.h_points = []

        st.rerun()

else:
    st.image(viewer.getRGBImage(), width="stretch")
# ------------------------------------------------------------


# ------------------------------------------------------------
# 저장
if viewer.currentImage is not None:
    fileName = "edited_image.jpg"

    if st.session_state.files:
        name = st.session_state.files[st.session_state.index].name
        fileName = os.path.splitext(os.path.basename(name))[0] + "_edited.jpg"

    st.download_button(
        "Save Image",
        data=viewer.getImageBytes(".jpg"),
        file_name=fileName,
        mime="image/jpeg"
    )
