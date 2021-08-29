from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QFileDialog, QMessageBox, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import QPoint, QThread, pyqtSignal, Qt, QRect
from PyQt5.QtGui import QPixmap, QPainter, QPen
from PIL import Image
import sys


class PicEditWindow(QWidget):
    def __init__(self, parent=None):
        super(PicEditWindow, self).__init__(parent=parent)

        # 控件
        self._save_btn = None
        self._back_btn = None
        self._clear_btn = None
        self._pic_label = None

        # 入口
        self._main()

    def _main(self):
        self._init_widgets()
        self._init_signals()
        self._init_layouts()

    def _init_widgets(self):
        self._save_btn = QPushButton('保存')
        self._back_btn = QPushButton('后退')
        self._clear_btn = QPushButton('清空')
        self._pic_label = PicLabel()

    def _init_signals(self):
        self._save_btn.clicked.connect(self._save_slot)
        self._back_btn.clicked.connect(self._back_slot)
        self._clear_btn.clicked.connect(self._clear_slot)

    def _init_layouts(self):
        v_layout = QVBoxLayout()
        h_layout = QHBoxLayout()
        h_layout.addWidget(self._clear_btn)
        h_layout.addWidget(self._back_btn)
        h_layout.addWidget(self._save_btn)
        v_layout.addWidget(self._pic_label)
        v_layout.addLayout(h_layout)
        self.setLayout(v_layout)

    def _save_slot(self):
        """保存图片槽函数"""
        self._pic_label.save_pics()

    def _back_slot(self):
        """后退槽函数"""
        self._pic_label.delete_last_rect()

    def _clear_slot(self):
        """清空槽函数"""
        self._pic_label.clear_rects()

    def set_pic(self, path):
        """
        设置要编辑的图片
        :param path: 图片路径
        :return: None
        """
        if not path:
            return

        self._pic_label.set_pic(path)


class PicLabel(QLabel):
    def __init__(self):
        super(PicLabel, self).__init__()
        # 要编辑的图片路径
        self._edit_pic_path = None

        # 截图保存路径
        self._cropped_pic_path = None

        # 鼠标坐标点
        self._begin_point = QPoint()
        self._end_point = QPoint()

        # 绘制用的铅笔
        self._pen = QPen(Qt.green, 1, Qt.SolidLine)

        # 矩形区域汇总
        self._rect_list = []

        # 图片保存线程
        self._save_thread = SaveThread(self)
        self._save_thread.save_signal.connect(self._check_save_result)

    def _check_save_result(self, isOk):
        if isOk:
            QMessageBox.information(self, '保存成功', f'图片已经成功保存！')
        else:
            QMessageBox.critical(self, '保存失败', f'图片保存失败！')

    def save_pics(self):
        """通过文件对话框保存 """
        self._cropped_pic_path = QFileDialog.getExistingDirectory(self, '选择存储文件夹', './')
        if self._cropped_pic_path:
            self._save_thread.start()

    def delete_last_rect(self):
        """后退的话删除最后画的一个矩形"""
        if len(self._rect_list) > 0:
            self._rect_list.pop()
            self.update()

    def clear_rects(self):
        """清空所有矩形"""
        self._rect_list = []
        self.update()

    def set_pic(self, path):
        self._edit_pic_path = path
        self.setPixmap(QPixmap(path))

    def mousePressEvent(self, e):
        if e.buttons() == Qt.LeftButton:
            self._begin_point = e.pos()
            self._end_point = e.pos()
            self.update()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton:
            self._end_point = e.pos()
            self.update()

    def mouseReleaseEvent(self, e):
        rect = QRect(self._begin_point, self._end_point)
        self._rect_list.append(rect)
        self._begin_point = QPoint()
        self._end_point = QPoint()
        self.update()

    def paintEvent(self, e):
        super(PicLabel, self).paintEvent(e)
        painter = QPainter(self)
        painter.setPen(self._pen)

        # 实时绘制
        if self._begin_point and self._end_point:
            rect = QRect(self._begin_point, self._end_point)
            painter.drawRect(rect)

        # 绘制已经添加到_rect_list列表中的矩形
        for i, rect in enumerate(self._rect_list):
            painter.drawRect(rect)
            painter.drawText(rect.bottomLeft(), str(i+1))
        

class SaveThread(QThread):
    save_signal = pyqtSignal(bool)

    def __init__(self, window):
        super(SaveThread, self).__init__()
        self.window = window

    def run(self):
        try:
            img = Image.open(self.window._edit_pic_path)
            for i, rect in enumerate(self.window._rect_list):
                x1 = rect.x()
                y1 = rect.y()
                x2 = x1 + rect.width()
                y2 = y1 + rect.height()
                cropped = img.crop((x1, y1, x2, y2))
                cropped.save(f'{self.window._cropped_pic_path}/{i+1}.png')

            self.save_signal.emit(True)
        except Exception as e:
            print(e)
            self.save_signal.emit(False)


if __name__ == '__main__':
    app = QApplication([])
    window = PicEditWindow()
    window.show()
    sys.exit(app.exec_())


