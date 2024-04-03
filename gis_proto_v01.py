import sys
import pandas as pd
from shapely.geometry import (
    Point,
    LineString,
    Polygon
)
from PyQt5.QtWidgets import (
    QFileDialog,
    QGraphicsScene,
    QGraphicsItem,
    QGraphicsEllipseItem,
    QGraphicsRectItem,
    QGraphicsLineItem,
    QGraphicsPolygonItem,
    QMainWindow,
    QApplication,
    QShortcut,
    QMessageBox
)
from PyQt5.uic import loadUi
from PyQt5.QtGui import (
    QPainter,
    QBrush,
    QPen,
    QPolygonF,
    QKeySequence
)
from PyQt5.QtCore import (
    QPointF,
    QLineF,
    Qt
)
import itertools
from gui import Ui_Form


class Window(QMainWindow):


    def deleteItem(self):
        '''
        Удаление выделенного объекта
        '''
        items = self.ui.graphicsView.scene.selectedItems()
        if len(items) != 0:
            for item in items:
                self.ui.graphicsView.scene.removeItem(item)


    def saveNewItems(self):
        '''
        Сохранение объектов в файл
        '''
        try:
            items = self.ui.graphicsView.scene.items()
            print('saving')
            if len(items) > 0:
                with open('test_save_item.txt', 'w+') as fout:
                    for item in items:
                        if item.type() == QGraphicsEllipseItem().type():
                            print('ellips_saving')
                            coords = list(item.rect().getCoords()[0:2])
                            row = ' '.join([ str(int(coord)) for coord in coords ])
                        elif item.type() == QGraphicsRectItem().type():
                            print("Rectangle", list(item.rect().getCoords()))
                        elif item.type() == QGraphicsLineItem().type():
                            print('line_saving')
                            coords = [item.line().p1().x(), item.line().p1().y(), item.line().p2().x(), item.line().p2().y()]
                            row = ' '.join([str(int(coord)) for coord in coords])
                        elif item.type() == QGraphicsPolygonItem().type():
                            print('poly_saving')
                            coords = list(itertools.chain.from_iterable([[p.x(), p.y()] for p in item.polygon()]))
                            row = ' '.join([str(int(coord)) for coord in coords])
                        fout.writelines(row+'\n')
                    print('closing saving...')
                    fout.close()
            print('succsesfull saving')
            self.error = QMessageBox()
            self.error.setText('Файл успешно сохранен')
            self.error.setIcon(QMessageBox.Warning)
            self.error.setStandardButtons(QMessageBox.Ok)
            self.error.exec_()
        except:
            self.error = QMessageBox()
            self.error.setText('Не удалось выполнить сохранение файла')
            self.error.setIcon(QMessageBox.Warning)
            self.error.setStandardButtons(QMessageBox.Ok)
            self.error.exec_()

    def zoom(self, event):
        '''
        Изменение зума сцены
        :param event: событие
        '''
        zoomInFactor = 1.25
        zoomOutFactor = 1 / zoomInFactor
        if event.angleDelta().y() > 0:
            zoomFactor = zoomInFactor
        else:
            zoomFactor = zoomOutFactor
        self.ui.graphicsView.scale(zoomFactor, zoomFactor)


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.ui.graphicsView.startPos = event.pos()
            item = self.ui.graphicsView.itemAt(event.pos().x(), event.pos().y())
            if item:
                item.setSelected(1)
            if item == None:
                self.ui.graphicsView.scene.clearSelection()
        else:
            super(Window,self).mousePressEvent(event)


    def mouseMoveEvent(self, event):
        if self.ui.graphicsView.startPos is not None:
            delta = self.ui.graphicsView.startPos - event.pos()
            transform = self.ui.graphicsView.transform()
            deltaX = delta.x() / transform.m11()
            deltaY = delta.y() / transform.m22()
            self.ui.graphicsView.setSceneRect(self.ui.graphicsView.sceneRect().translated(deltaX, deltaY))
            self.ui.graphicsView.startPos = event.pos()
        else:
             super(Window, self).mouseMoveEvent(event)


    def mouseReleaseEvent(self, event):
        self.ui.graphicsView.startPos = None
        super(Window, self).mouseReleaseEvent(event)


    def create_ui(self):
        '''
        Загрузка файла с интерфейсом .ui
        '''

        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # loadUi("gui.ui",self)

        self.ui.graphicsView.scene = QGraphicsScene(self)
        self.ui.graphicsView.setBackgroundBrush(Qt.white)
        self.ui.graphicsView.setDragMode(self.ui.graphicsView.ScrollHandDrag)
        self.ui.graphicsView.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.ui.graphicsView.setOptimizationFlag(self.ui.graphicsView.DontAdjustForAntialiasing, True)
        self.ui.graphicsView.wheelEvent = self.zoom
        self.ui.graphicsView.mouseMoveEvent = self.mouseMoveEvent
        self.ui.graphicsView.mousePressEvent = self.mousePressEvent
        self.ui.graphicsView.mouseReleaseEvent = self.mouseReleaseEvent
        self.ui.graphicsView.startPos = None
        self.ui.blueBrush = QBrush(Qt.blue)
        self.ui.blackPen = QPen(Qt.black)
        self.ui.blackPen.setWidth(1)
        self.ui.redPen = QPen(Qt.black)
        self.ui.bluePen = QPen(Qt.blue)
        self.ui.redPen.setWidth(1)
        self.ui.bluePen.setWidth(1)
        self.ui.graphicsView.setScene(self.ui.graphicsView.scene)



    def chunks(self, lst, size):
        '''
        Собирает координатные пары для строк полученных из файла
        :param lst: список с координатами
        :param size: размер подсписков
        :return: набор координатных пар
        '''
        return [lst[i:i + size] for i in range(0, len(lst), size)]


    def type_geom(self, x):
        '''
        Определяет тип геометрии в соответствии с количеством элементов полученных в файле для каждой строки
        :param x: строка из датафрейма
        :return: Тип геометрии
        '''
        if x['count_elements'] == 2:
            return 'Point'
        elif x['count_elements'] == 4:
            return 'LineString'
        elif x['count_elements'] == 6 or (x['count_elements'] > 6 and x['count_elements'] % 2 == 0):
            return 'Polygon'
        else:
            return None


    def make_geometry(self, x):
        '''
        Собирает геометрию на основании данных полученных из файла
        :param x: строка из датафрейма
        :return: геомеотрия shapely в соответствии с типом
        '''
        if x['geom_type'] == 'Polygon':
            return Polygon(x['coords_pairs'])
        elif x['geom_type'] == 'Point':
            return Point(x['coords_pairs'])
        elif x['geom_type'] == 'LineString':
            return LineString(x['coords_pairs'])


    def read_file(self, path):
        with open(path, 'r') as file:
            rows = file.read().splitlines()
            file.close()
        df = pd.DataFrame({
            'object': rows
        })
        df['count_elements'] = df.apply(lambda x: len(x['object'].split(' ')), axis=1)
        df['geom_type'] = df.apply(lambda x: self.type_geom(x), axis=1)
        df['coords_pairs'] = df['coords_pairs'] = df.apply(
            lambda x: self.chunks(x['object'].split(' '), 2) if x['geom_type'] is not None else None, axis=1)

        for index, row in df.iterrows():
            if row.geom_type == 'Polygon':
                if row.coords_pairs[0] != row.coords_pairs[-1]:
                    row.coords_pairs.append(row.coords_pairs[0])

        df['geometry'] = df.apply(lambda x: self.make_geometry(x), axis=1)
        df['popup'] = df.apply(lambda x: f'<p>{x["geom_type"]}</p>', axis=1)
        # df.to_csv('testsave.csv', sep=';')
        return df


    def button_clicked(self, fname):
        '''
        Чтение файла к которому пользователь указал путь
        :param fname:
        :return:
        '''
        try:
            if fname != '' and fname is not None:
                df = self.read_file(fname)
            if (df[df['geom_type'].isna()].shape[0]) > 0:
                return [1,df]
            else:
                return [0,df]
        except:
            return [2,None]

    def browsefiles(self):
        '''
        Получение доступа к файлу через проводник или путь записанный в строке
        '''

        status_reading = {
            0:'Файл прочитан успешно',
            1:'Файл прочитан, но в нем есть некорректные данные',
            2:'Файл не удалось прочитать'
        }

        try:
            if self.ui.filename.text() == '' or self.ui.filename.text() is None:
                fname = QFileDialog.getOpenFileName(
                    self,
                    'Open file',
                    r'C:\Users'
                )
                self.ui.filename.setText(fname[0])
            else:
                fname = [self.ui.filename.text()]
            status_ = self.button_clicked(fname[0])
            self.ui.statusReadingFile.setText(status_reading[status_[0]])
            items = self.ui.graphicsView.scene.items()
            if len(items) != 0:
                for item in items:
                    self.ui.graphicsView.scene.removeItem(item)
            for index, x in status_[1].iterrows():
                if x['geom_type'] == 'Polygon':
                    self.ui.graphicsView.scene.addPolygon(
                        QPolygonF([ QPointF(int(i[0]), int(i[1])) for i in x['coords_pairs']]),
                        self.ui.blackPen
                    )
                elif x['geom_type'] == 'LineString':
                    coords = [ QPointF(int(i[0]), int(i[1])) for i in x['coords_pairs']]
                    self.ui.graphicsView.scene.addLine(
                        QLineF(coords[0],
                               coords[1]),
                        self.ui.bluePen
                    )
                elif x['geom_type'] == 'Point':
                    self.ui.graphicsView.scene.addEllipse(
                        int(x['coords_pairs'][0][0]),
                        int(x['coords_pairs'][0][1]),
                        1,
                        1,
                        self.ui.redPen
                    )
                else:
                    continue
                for item in self.ui.graphicsView.scene.items():
                    item.setFlag(QGraphicsItem.ItemIsSelectable)
        except:
            self.ui.statusReadingFile.setText(status_reading[2])

    def __init__(self):
        super().__init__()
        self.setWindowTitle("gis_proto_alpha")
        self.create_ui()
        self.shortcutSave = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcutSave.activated.connect(self.saveNewItems)
        self.shortcutDel = QShortcut(QKeySequence("Delete"), self)
        self.shortcutDel.activated.connect(self.deleteItem)
        self.ui.browse.clicked.connect(self.browsefiles)
        self.ui.saveBtn.clicked.connect(self.saveNewItems)
        self.ui.delBtn.clicked.connect(self.deleteItem)

        self.show()

app = QApplication(sys.argv)
window = Window()
sys.exit(app.exec_())