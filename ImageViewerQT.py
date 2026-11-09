# PyQT Version
#
# 이 파일은 두 가지 역할을 한다.
# 1) ImageProcessor : PyQt와 Streamlit이 함께 사용하는 이미지 처리 기능
# 2) ViewerClass    : 기존 PyQt 화면
#
# 따라서 Streamlit에서는
#     import ImageViewerQT as iv
#     viewer = iv.ImageProcessor()
# 처럼 이미지 처리 기능만 가져다 사용할 수 있다.

import sys
import os
import glob
import random
import cv2
import numpy


# ============================================================
# PyQt / Streamlit 공용 이미지 처리 클래스
class ImageProcessor:
    def __init__(self):
        # 처음 불러온 원본 이미지와 현재 편집 중인 이미지
        self.originalImage = None
        self.currentImage = None

    # ------ OpenCV 이미지 자체를 불러오기 ------
    def setImage(self, img):
        if img is None:
            return False

        self.originalImage = img.copy()
        self.currentImage = img.copy()
        return True

    # ------ 파일 경로의 이미지를 불러오기 (PyQt에서 사용) ------
    def loadImage(self, fName):
        img = cv2.imread(fName)
        return self.setImage(img)

    # ------ 업로드된 bytes 이미지를 불러오기 (Streamlit에서 사용) ------
    def loadImageBytes(self, fileBytes):
        data = numpy.frombuffer(fileBytes, dtype=numpy.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        return self.setImage(img)

    # ------ Streamlit 출력용 RGB 이미지 반환 ------
    def getRGBImage(self):
        if self.currentImage is None:
            return None

        return cv2.cvtColor(self.currentImage, cv2.COLOR_BGR2RGB)

    # ------ Streamlit 다운로드용 이미지 bytes 생성 ------
    def getImageBytes(self, extension=".jpg"):
        if self.currentImage is None:
            return None

        ok, buffer = cv2.imencode(extension, self.currentImage)
        if not ok:
            return None

        return buffer.tobytes()

    # ------ 4개의 점을 [좌상, 우상, 우하, 좌하] 순서로 정렬 ------
    def orderPoints(self, points):
        rect = numpy.zeros((4, 2), dtype="float32")

        s = points.sum(axis=1)
        rect[0] = points[numpy.argmin(s)]       # 좌상
        rect[2] = points[numpy.argmax(s)]       # 우하

        diff = numpy.diff(points, axis=1)
        rect[1] = points[numpy.argmin(diff)]    # 우상
        rect[3] = points[numpy.argmax(diff)]    # 좌하

        return rect

    # ------ 선택한 4개 점에 대해서만 호모그래피 적용 ------
    def applySelectedHomography(self, points):
        if self.currentImage is None or len(points) != 4:
            return False

        src = numpy.float32(points)
        src = self.orderPoints(src)

        # 선택한 사각형의 가로/세로 길이를 계산해서
        # 결과 이미지 크기를 자연스럽게 정함
        widthA = numpy.linalg.norm(src[2] - src[3])
        widthB = numpy.linalg.norm(src[1] - src[0])
        maxWidth = max(int(widthA), int(widthB))

        heightA = numpy.linalg.norm(src[1] - src[2])
        heightB = numpy.linalg.norm(src[0] - src[3])
        maxHeight = max(int(heightA), int(heightB))

        if maxWidth < 1 or maxHeight < 1:
            return False

        dst = numpy.float32([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]
        ])

        matrix = cv2.getPerspectiveTransform(src, dst)

        self.currentImage = cv2.warpPerspective(
            self.currentImage,
            matrix,
            (maxWidth, maxHeight)
        )

        return True

    # ------ 호모그래피 점 표시용 이미지 ------
    def getHomographyPreview(self, points):
        if self.currentImage is None:
            return None

        preview = self.currentImage.copy()
        drawPoints = [(int(x), int(y)) for x, y in points]

        for x, y in drawPoints:
            cv2.circle(preview, (x, y), 7, (0, 0, 255), -1)

        for i in range(1, len(drawPoints)):
            cv2.line(
                preview,
                drawPoints[i - 1],
                drawPoints[i],
                (0, 0, 255),
                3
            )

        return cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)


    # ==== 기본 포토샵 기능 ====

    # 흑백사진으로
    def BWImage(self):
        if self.currentImage is None:
            return False

        gray = cv2.cvtColor(self.currentImage, cv2.COLOR_BGR2GRAY)

        # 이후 다른 기능도 계속 사용할 수 있도록 다시 BGR로 변환
        self.currentImage = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        return True

    # 자르기
    def croppingImage(self):
        if self.currentImage is None:
            return False

        height, width = self.currentImage.shape[:2]

        # 상하좌우 10%씩 잘라냄
        x1 = int(width * 0.1)
        x2 = int(width * 0.9)
        y1 = int(height * 0.1)
        y2 = int(height * 0.9)

        self.currentImage = self.currentImage[y1:y2, x1:x2].copy()
        return True

    # 회전
    def rotationImage(self):
        if self.currentImage is None:
            return False

        self.currentImage = cv2.rotate(
            self.currentImage,
            cv2.ROTATE_90_CLOCKWISE
        )
        return True

    # 블러처리
    def blurringImage(self):
        if self.currentImage is None:
            return False

        self.currentImage = cv2.GaussianBlur(
            self.currentImage,
            (9, 9),
            0
        )
        return True

    # 밝기+
    def bright1Image(self):
        if self.currentImage is None:
            return False

        self.currentImage = cv2.convertScaleAbs(
            self.currentImage,
            alpha=1.0,
            beta=30
        )
        return True

    # 밝기-
    def bright2Image(self):
        if self.currentImage is None:
            return False

        dark = numpy.full(
            self.currentImage.shape,
            30,
            dtype=numpy.uint8
        )

        self.currentImage = cv2.subtract(
            self.currentImage,
            dark
        )
        return True

    # 원본으로 복구
    def rollbackImage(self):
        if self.originalImage is None:
            return False

        self.currentImage = self.originalImage.copy()
        return True


# ============================================================
# 아래부터는 PyQt 전용 코드
# Streamlit 서버에 PyQt5가 없어도 ImageProcessor는 import 가능하도록
# PyQt import를 별도로 처리한다.
PYQT_AVAILABLE = True
PYQT_ERROR = None

try:
    from PyQt5.QtWidgets import (
        QMainWindow,
        QApplication,
        qApp,
        QFileDialog,
        QAction
    )
    from PyQt5.uic import loadUiType
    from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen
    from PyQt5.QtCore import QTimer, Qt, QEvent
except Exception as e:
    PYQT_AVAILABLE = False
    PYQT_ERROR = e


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_PATH = os.path.join(BASE_DIR, "imageViewer.ui")


if PYQT_AVAILABLE and os.path.exists(UI_PATH):
    form_class = loadUiType(UI_PATH)[0]

    class ViewerClass(QMainWindow, form_class, ImageProcessor):
        def __init__(self, parent=None):
            QMainWindow.__init__(self, parent)
            ImageProcessor.__init__(self)
            self.setupUi(self)

            # 폴더에서 불러온 jpg 파일 목록
            self.files = []

            # 현재 보여주는 이미지의 위치
            self.index = 0

            # 파일/폴더 선택창 시작 위치
            self.startDir = BASE_DIR

            # ------ 선택형 호모그래피용 변수 ------
            self.homographyMode = False
            self.h_points = []

            # label에서 마우스 클릭을 받기 위해 이벤트 필터 설치
            self.label.installEventFilter(self)

            # ----- 메뉴 연결 -----
            self.actionSelect.triggered.connect(self.fileSelect)
            self.actionExit.triggered.connect(qApp.quit)

            # UI에 actionFolder가 없다면 자동으로 생성
            if not hasattr(self, "actionFolder"):
                self.actionFolder = QAction("Select Folder", self)

                if hasattr(self, "menuFile"):
                    if hasattr(self, "actionExit"):
                        self.menuFile.insertAction(self.actionExit, self.actionFolder)
                    else:
                        self.menuFile.addAction(self.actionFolder)

            self.actionFolder.triggered.connect(self.folderSelect)

            # ------ 버튼 연결 -----
            self.nextButton.clicked.connect(self.nextImage)
            self.shuffleButton.clicked.connect(self.shuffle)

            if hasattr(self, "slideShowButton"):
                self.slideShowButton.clicked.connect(self.slideShow)

            # ------ 기본 포토샵 버튼 연결 ------
            self.BWButton.clicked.connect(self.BWImage)
            self.CroppingButton.clicked.connect(self.croppingImage)
            self.RotationButton.clicked.connect(self.rotationImage)
            self.BlurringButton.clicked.connect(self.blurringImage)
            self.Bright1_Button.clicked.connect(self.bright1Image)
            self.Bright2_Button.clicked.connect(self.bright2Image)
            self.HomographyButton.clicked.connect(self.homographyImage)
            self.SaveButton.clicked.connect(self.saveImage)
            self.RollbackButton.clicked.connect(self.rollbackImage)

            # ------ 슬라이드 쇼용 타이머 ------
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.nextImage)

        # ------ 이미지 출력 ------
        def showImage(self, fName):
            if not self.loadImage(fName):
                print("이미지를 읽을 수 없습니다:", fName)
                return

            # 새 이미지를 열면 이전 호모그래피 선택 상태는 초기화
            self.homographyMode = False
            self.h_points = []
            self.statusbar.showMessage("")

            self.displayImage()

        # ------ 현재 편집 중인 이미지를 화면에 출력 ------
        def displayImage(self):
            if self.currentImage is None:
                return

            img = cv2.cvtColor(self.currentImage, cv2.COLOR_BGR2RGB)

            height, width, channel = img.shape
            bytesPerLine = width * channel

            qImage = QImage(
                img.data,
                width,
                height,
                bytesPerLine,
                QImage.Format_RGB888
            ).copy()

            qPixmapVar = QPixmap.fromImage(qImage)

            qPixmapVar = qPixmapVar.scaled(
                self.label.width(),
                self.label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            # 호모그래피 선택 중이면 클릭한 점과 선을 화면에 표시
            if self.homographyMode and len(self.h_points) > 0:
                drawPixmap = qPixmapVar.copy()
                painter = QPainter(drawPixmap)
                pen = QPen(Qt.red, 3)
                painter.setPen(pen)

                img_h, img_w = self.currentImage.shape[:2]
                draw_points = []

                for x, y in self.h_points:
                    px = int(x * drawPixmap.width() / img_w)
                    py = int(y * drawPixmap.height() / img_h)
                    draw_points.append((px, py))

                for px, py in draw_points:
                    painter.drawEllipse(px - 4, py - 4, 8, 8)

                for i in range(1, len(draw_points)):
                    painter.drawLine(
                        draw_points[i - 1][0], draw_points[i - 1][1],
                        draw_points[i][0], draw_points[i][1]
                    )

                painter.end()
                self.label.setPixmap(drawPixmap)
            else:
                self.label.setPixmap(qPixmapVar)

        # ------ label에서 마우스 클릭 받기 ------
        def eventFilter(self, obj, event):
            if obj == self.label and self.homographyMode:
                if event.type() == QEvent.MouseButtonPress:
                    if event.button() == Qt.LeftButton:
                        self.handleHomographyClick(event.pos().x(), event.pos().y())
                        return True
            return super().eventFilter(obj, event)

        # ------ 호모그래피 모드에서 클릭한 점 처리 ------
        def handleHomographyClick(self, click_x, click_y):
            if self.currentImage is None:
                return

            pixmap = self.label.pixmap()
            if pixmap is None:
                return

            offset_x = (self.label.width() - pixmap.width()) / 2
            offset_y = (self.label.height() - pixmap.height()) / 2

            x = click_x - offset_x
            y = click_y - offset_y

            if x < 0 or y < 0 or x > pixmap.width() or y > pixmap.height():
                return

            img_h, img_w = self.currentImage.shape[:2]

            image_x = img_w * x / pixmap.width()
            image_y = img_h * y / pixmap.height()

            self.h_points.append((image_x, image_y))

            self.statusbar.showMessage(
                f"호모그래피 점 선택 중: {len(self.h_points)}/4"
            )

            self.displayImage()

            if len(self.h_points) == 4:
                self.applySelectedHomography()

        # ------ 선택한 4개 점에 대해서만 호모그래피 적용 ------
        def applySelectedHomography(self):
            if len(self.h_points) != 4:
                return

            success = ImageProcessor.applySelectedHomography(
                self,
                self.h_points
            )

            self.h_points = []
            self.homographyMode = False

            if success:
                self.statusbar.showMessage(
                    "선택한 영역에 호모그래피가 적용되었습니다."
                )
            else:
                self.statusbar.showMessage(
                    "호모그래피를 적용할 수 없습니다."
                )

            self.displayImage()

        # ------ Select File : jpg 파일 하나 선택 ------
        def fileSelect(self):
            fName = QFileDialog.getOpenFileName(
                self,
                "Open file",
                self.startDir,
                "Image files (*.jpg)"
            )[0]

            if fName == "":
                return

            self.startDir = os.path.dirname(fName)
            self.showImage(fName)

        # ------ Select Folder : 폴더 안의 jpg 파일 목록 저장 ------
        def folderSelect(self):
            dirName = QFileDialog.getExistingDirectory(
                self,
                "Open Folder",
                self.startDir
            )

            if dirName == "":
                return

            self.startDir = dirName
            self.files = []

            for file in glob.glob(os.path.join(dirName, "*.jpg")):
                self.files.append(file)

            self.files.sort()
            self.index = 0

            if len(self.files) == 0:
                print("선택한 폴더에 jpg 파일이 없습니다.")
                self.label.clear()
                self.originalImage = None
                self.currentImage = None
                return

            self.showImage(self.files[self.index])

        # ------ Next : 다음 이미지 표시 ------
        def nextImage(self):
            if len(self.files) == 0:
                print("먼저 Select Folder로 이미지 폴더를 선택하세요.")
                return

            self.index += 1

            if self.index >= len(self.files):
                self.index = 0

            self.showImage(self.files[self.index])

        # ------ Shuffle ------
        def shuffle(self):
            if len(self.files) == 0:
                print("먼저 Select Folder로 이미지 폴더를 선택하세요.")
                return

            random.shuffle(self.files)
            self.index = 0
            self.showImage(self.files[self.index])

        # ------ Slide Show ------
        def slideShow(self):
            if len(self.files) == 0:
                print("먼저 Select Folder로 이미지 폴더를 선택하세요.")
                return

            if self.timer.isActive():
                self.timer.stop()
                self.slideShowButton.setText("Slide Show")
            else:
                self.timer.start(1500)
                self.slideShowButton.setText("Stop")

        # =========================
        # 아래 함수들은 실제 처리는 ImageProcessor를 사용하고
        # PyQt에서는 화면 갱신만 담당한다.
        def BWImage(self):
            if ImageProcessor.BWImage(self):
                self.displayImage()

        def croppingImage(self):
            if ImageProcessor.croppingImage(self):
                self.displayImage()

        def rotationImage(self):
            if ImageProcessor.rotationImage(self):
                self.displayImage()

        def blurringImage(self):
            if ImageProcessor.blurringImage(self):
                self.displayImage()

        def bright1Image(self):
            if ImageProcessor.bright1Image(self):
                self.displayImage()

        def bright2Image(self):
            if ImageProcessor.bright2Image(self):
                self.displayImage()

        # 호모그래피 선택 모드 ON/OFF는 PyQt UI 기능이므로 여기 유지
        def homographyImage(self):
            if self.currentImage is None:
                return

            if self.homographyMode:
                self.homographyMode = False
                self.h_points = []
                self.statusbar.showMessage("호모그래피 선택이 취소되었습니다.")
                self.displayImage()
                return

            self.homographyMode = True
            self.h_points = []
            self.statusbar.showMessage(
                "호모그래피 모드: 이미지에서 4개의 점을 차례대로 클릭하세요."
            )
            self.displayImage()

        # 저장은 PyQt의 QFileDialog를 사용하므로 여기 유지
        def saveImage(self):
            if self.currentImage is None:
                return

            fName = QFileDialog.getSaveFileName(
                self,
                "Save Image",
                self.startDir,
                "JPEG Image (*.jpg);;PNG Image (*.png)"
            )[0]

            if fName == "":
                return

            root, ext = os.path.splitext(fName)

            if ext == "":
                fName = fName + ".jpg"

            cv2.imwrite(fName, self.currentImage)

        def rollbackImage(self):
            if ImageProcessor.rollbackImage(self):
                self.homographyMode = False
                self.h_points = []
                self.statusbar.showMessage("원본 이미지로 복구되었습니다.")
                self.displayImage()

else:
    # Streamlit에서 import할 때 PyQt5나 imageViewer.ui가 없어도 ImageProcessor를 사용할 수 있게
    ViewerClass = None


if __name__ == "__main__":
    if not PYQT_AVAILABLE:
        print("PyQt5를 불러올 수 없습니다:", PYQT_ERROR)
        sys.exit(1)

    if not os.path.exists(UI_PATH):
        print("imageViewer.ui 파일을 찾을 수 없습니다:", UI_PATH)
        sys.exit(1)

    app = QApplication(sys.argv)

    myWindow = ViewerClass(None)
    myWindow.show()

    sys.exit(app.exec_())
