from PyQt5.QtWidgets import QLabel
# TODO: from components import 


class Canvas(QLabel):
    def __init__(self, width, height, viewer_to_screen, screen_to_center):
        super(Canvas, self).__init__()
        self.width, self.height = width, height
        self.vts, self.stc = viewer_to_screen, screen_to_center
        self.center = Point2D(width // 2, height // 2)
        self.setPixmap(QPixmap(width, height))
        self.pixmap().fill(QColor(Qt.white))
        self.update()  # preexisting method

        self.pressed = False
        self.position = None

    def drawFace(self, points, brightness=None, color=120):
        p = QPainter(self.pixmap())
        p.setPen(QPen(Qt.NoPen))
        shade = brightness * 200 + 55
        p.setBrush(QBrush(QColor.fromHsv(color, 255, shade, 255),
                   Qt.SolidPattern))
        qpts = [QPoint(pt.x, pt.y) for pt in points]
        p.drawPolygon(*qpts)

    def drawShadow(self, points):
        p = QPainter(self.pixmap())
        p.setPen(QPen(Qt.NoPen))
        p.setBrush(QBrush(Qt.gray, Qt.SolidPattern))
        qpts = [QPoint(pt.x, pt.y) for pt in points]
        p.drawPolygon(*qpts)

    def clearAll(self):
        self.pixmap().fill(QColor(Qt.white))

    def mousePressEvent(self, e):
        self.pressed = True
        self.position = Point2D(e.pos().x(), e.pos().y())

    def mouseMoveEvent(self, e):
        if self.pressed:
            self.position = Point2D(e.pos().x(), e.pos().y())

    def mouseReleaseEvent(self, e):
        self.pressed = False
        self.position = None


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setGeometry(WINDOW_X, WINDOW_Y, CANVAS_WIDTH, CANVAS_HEIGHT)
        self.setWindowTitle("PyQt Drawing")
        self.setWindowIcon(QIcon('pythonlogo.png'))
        self.canvas = Canvas(CANVAS_WIDTH, CANVAS_HEIGHT, VIEWER_TO_SCREEN, SCREEN_TO_CENTER)
        self.setCentralWidget(self.canvas)
        self.show()

        disp = EDGE_LENGTH / 4 + INTERSPACE / 2
        colors = [0, 45, 90, 135, 180, 225, 270, 315]

        self.cubes = [
                Cube(Point( disp,  disp,  disp), self.canvas, colors[3]),
                Cube(Point( disp,  disp, -disp), self.canvas, colors[0]),
                Cube(Point( disp, -disp, -disp), self.canvas, colors[6]),
                Cube(Point( disp, -disp,  disp), self.canvas, colors[1]),
                Cube(Point(-disp, -disp,  disp), self.canvas, colors[4]),
                Cube(Point(-disp,  disp,  disp), self.canvas, colors[7]),
                Cube(Point(-disp,  disp, -disp), self.canvas, colors[2]),
                Cube(Point(-disp, -disp, -disp), self.canvas, colors[5])
        ]

        self.update()

        self.timer = QTimer()
        self.timer.timeout.connect(self.mainloop)
        self.timer.start(1000 // FPS)

    def update(self):
        mytuples = []
        for cube in self.cubes:
            z = cube.update()
            mytuples.append((z, cube))

        for z, cube in sorted(mytuples, key=lambda x: x[0]):
            cube.draw()

    def ease(self, t):
        t1, t2, t3, t4, t5, t6 = 10, 20, 30, 40, 50, EASE_MAX
        max_val = 3
        if t < t1:
            val = 0
        elif t < t2:
            val = (max_val / 2 / (t2 - t1)**2) * (t - t1)**2
        elif t < t3:
            val = - (max_val / 2 / (t2 - t3)**2) * (t - t3)**2 + max_val
        elif t < t4:
            val = max_val
        elif t < t5:
            val = - (max_val / 2 / (t5 - t4)**2) * (t - t4)**2 + max_val
        else:
            val = (max_val / 2 / (t5 - t6)**2) * (t - t6)**2
        return val

    def mainloop(self):
        self.canvas.clearAll()
        self.update()
        self.canvas.update()


