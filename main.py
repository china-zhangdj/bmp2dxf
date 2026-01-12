import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QFileDialog, QLineEdit, QVBoxLayout, QHBoxLayout,
    QMessageBox
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import cv2
import numpy as np
from PIL import Image
import ezdxf

class BmpToDxfGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BMP2DXF")
        self.resize(600, 500)

        self.bmp_path = ""
        self.dpi = 1000

        # 1️⃣ 文件选择
        self.select_btn = QPushButton("选择 BMP 文件")
        self.select_btn.clicked.connect(self.select_bmp)

        # 2️⃣ DPI 输入
        self.dpi_label = QLabel("DPI:")
        self.dpi_input = QLineEdit("1000")
        self.dpi_input.setFixedWidth(80)

        dpi_layout = QHBoxLayout()
        dpi_layout.addWidget(self.dpi_label)
        dpi_layout.addWidget(self.dpi_input)
        dpi_layout.addStretch()

        # 3️⃣ BMP 预览
        self.preview_label = QLabel("BMP 预览")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setFixedSize(500, 300)
        self.preview_label.setStyleSheet("border: 1px solid black;")

        # 4️⃣ 生成 DXF
        self.generate_btn = QPushButton("生成 DXF")
        self.generate_btn.clicked.connect(self.generate_dxf)

        # 5️⃣ 布局
        layout = QVBoxLayout()
        layout.addWidget(self.select_btn)
        layout.addLayout(dpi_layout)
        layout.addWidget(self.preview_label)
        layout.addWidget(self.generate_btn)
        self.setLayout(layout)

    # 选择 BMP 文件
    def select_bmp(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 BMP 文件", "", "BMP 文件 (*.bmp)"
        )
        if file_path:
            self.bmp_path = file_path
            # 显示预览
            pixmap = QPixmap(self.bmp_path)
            pixmap = pixmap.scaled(
                self.preview_label.width(),
                self.preview_label.height(),
                Qt.AspectRatioMode.KeepAspectRatio
            )
            self.preview_label.setPixmap(pixmap)

    # 生成 DXF
    def generate_dxf(self):
        if not self.bmp_path:
            QMessageBox.warning(self, "警告", "请先选择 BMP 文件")
            return

        # DPI 输入
        try:
            dpi = float(self.dpi_input.text())
            if dpi <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "警告", "请输入有效 DPI")
            return
        self.dpi = dpi

        # 输出路径
        base_name = os.path.splitext(os.path.basename(self.bmp_path))[0]
        dir_name = os.path.dirname(self.bmp_path)
        dxf_path = os.path.join(dir_name, f"{base_name}.dxf")

        # 文件冲突检测
        if os.path.exists(dxf_path):
            ret = QMessageBox.question(
                self, "文件已存在",
                f"{dxf_path} 已存在，是否覆盖？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if ret == QMessageBox.StandardButton.No:
                return

        # 执行生成
        try:
            self.bmp_to_dxf(self.bmp_path, dxf_path, self.dpi)
            QMessageBox.information(self, "完成", f"DXF 已生成:\n{dxf_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成 DXF 失败:\n{str(e)}")

    # BMP → DXF 核心函数
    def bmp_to_dxf(self, bmp_path, dxf_path, dpi):
        # 读取 BMP
        img = Image.open(bmp_path).convert("L")
        img_np = np.array(img)
        height_px, width_px = img_np.shape

        # 二值化
        _, binary = cv2.threshold(img_np, 128, 255, cv2.THRESH_BINARY_INV)

        # 提取轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        # 创建 DXF
        doc = ezdxf.new(setup=True)
        doc.units = ezdxf.units.MM
        msp = doc.modelspace()
        px_to_mm = 25.4 / dpi

        for cnt in contours:
            eps = 0.005 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, eps, True)
            if len(approx) < 3:
                continue

            points_mm = []
            for p in approx:
                x_px, y_px = p[0]
                x_mm = x_px * px_to_mm
                y_mm = (height_px - y_px) * px_to_mm  # Y 翻转
                points_mm.append((x_mm, y_mm))

            msp.add_lwpolyline(points_mm, close=True)

        doc.saveas(dxf_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BmpToDxfGUI()
    window.show()
    sys.exit(app.exec())
