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
    QShortcut
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


class Window(QMainWindow):


    def deleteItem(self):
        '''
        Удаление выделенного объекта
        '''
        items = self.scene.selectedItems()
        if len(items) != 0:
            for item in items:
                self.scene.removeItem(item)


    def saveNewItems(self):
        '''
        Сохранение объектов в файл
        '''
        items = self.scene.items()
        if len(items) > 0:
            with open('test_save_item.txt', 'w+') as fout:
                for item in items:
                    if item.type() == QGraphicsEllipseItem().type():
                        coords = list(item.rect().getCoords()[0:2])
                        row = ' '.join([ str(int(coord)) for coord in coords ])
                    elif item.type() == QGraphicsRectItem().type():
                        print("Rectangle", list(item.rect().getCoords()))
                    elif item.type() == QGraphicsLineItem().type():
                        coords = [item.line().p1().x(), item.line().p1().y(), item.line().p2().x(), item.line().p2().y()]
                        row = ' '.join([str(int(coord)) for coord in coords])
                    elif item.type() == QGraphicsPolygonItem().type():
                        coords = list(itertools.chain.from_iterable([[p.x(), p.y()] for p in item.polygon()]))
                        row = ' '.join([str(int(coord)) for coord in coords])
                    fout.writelines(row+'\n')


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
        self.graphicsView.scale(zoomFactor, zoomFactor)


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.graphicsView.startPos = event.pos()
        else:
            super(Window,self).mousePressEvent(event)


    def mouseMoveEvent(self, event):
        if self.graphicsView.startPos is not None:
            delta = self.graphicsView.startPos - event.pos()
            transform = self.graphicsView.transform()
            deltaX = delta.x() / transform.m11()
            deltaY = delta.y() / transform.m22()
            self.graphicsView.setSceneRect(self.graphicsView.sceneRect().translated(deltaX, deltaY))
            self.graphicsView.startPos = event.pos()
        else:
             super(Window, self).mouseMoveEvent(event)


    def mouseReleaseEvent(self, event):
        self.graphicsView.startPos = None
        super(Window, self).mouseReleaseEvent(event)


    def create_ui(self):
        '''
        Загрузка файла с интерфейсом .ui
        '''

        loadUi("gui.ui",self)

        self.scene = QGraphicsScene(self)
        self.graphicsView.setBackgroundBrush(Qt.white)
        self.graphicsView.setDragMode(self.graphicsView.ScrollHandDrag)
        self.graphicsView.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.graphicsView.setOptimizationFlag(self.graphicsView.DontAdjustForAntialiasing, True)
        self.graphicsView.wheelEvent = self.zoom
        self.graphicsView.mouseMoveEvent = self.mouseMoveEvent
        self.graphicsView.mousePressEvent = self.mousePressEvent
        self.graphicsView.mouseReleaseEvent = self.mouseReleaseEvent
        self.graphicsView.startPos = None
        self.blueBrush = QBrush(Qt.blue)
        self.blackPen = QPen(Qt.black)
        self.blackPen.setWidth(1)
        self.redPen = QPen(Qt.black)
        self.bluePen = QPen(Qt.blue)
        self.redPen.setWidth(1)
        self.bluePen.setWidth(1)
        self.graphicsView.setScene(self.scene)


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
            if self.filename.text() == '' or self.filename.text() is None:
                fname = QFileDialog.getOpenFileName(
                    self,
                    'Open file',
                    r'C:\Users'
                )
                self.filename.setText(fname[0])
            else:
                fname = [self.filename.text()]
            status_ = self.button_clicked(fname[0])
            self.statusReadingFile.setText(status_reading[status_[0]])
            items = self.scene.items()
            if len(items) != 0:
                for item in items:
                    self.scene.removeItem(item)
            for index, x in status_[1].iterrows():
                if x['geom_type'] == 'Polygon':
                    self.scene.addPolygon(
                        QPolygonF([ QPointF(int(i[0]), int(i[1])) for i in x['coords_pairs']]),
                        self.blackPen
                    )
                elif x['geom_type'] == 'LineString':
                    coords = [ QPointF(int(i[0]), int(i[1])) for i in x['coords_pairs']]
                    self.scene.addLine(
                        QLineF(coords[0],
                               coords[1]),
                        self.bluePen
                    )
                elif x['geom_type'] == 'Point':
                    self.scene.addEllipse(
                        int(x['coords_pairs'][0][0]),
                        int(x['coords_pairs'][0][1]),
                        1,
                        1,
                        self.redPen
                    )
                else:
                    continue
                for item in self.scene.items():
                    item.setFlag(QGraphicsItem.ItemIsSelectable)
        except:
            self.statusReadingFile.setText(status_reading[2])

    def __init__(self):
        super().__init__()
        self.setWindowTitle("gis_proto_alpha")
        self.create_ui()
        self.shortcutSave = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcutSave.activated.connect(self.saveNewItems)
        self.shortcutDel = QShortcut(QKeySequence("Delete"), self)
        self.shortcutDel.activated.connect(self.deleteItem)
        self.browse.clicked.connect(self.browsefiles)
        self.saveBtn.clicked.connect(self.saveNewItems)
        self.delBtn.clicked.connect(self.deleteItem)

        self.show()

app = QApplication(sys.argv)
window = Window()
sys.exit(app.exec_())