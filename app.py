"""

3D cube. click and drag to rotate.

"""


from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from math import *
from random import randint
# TODO: from tools.visual import ...
# TODO: from tools.components import ...

WINDOW_X, WINDOW_Y = 20, 50
CANVAS_WIDTH = 1300
CANVAS_HEIGHT = 650

FPS = 30
EDGE_LENGTH = 250
VIEWER_TO_SCREEN = 2 * EDGE_LENGTH
SCREEN_TO_CENTER = 2 * EDGE_LENGTH
INPUT_SENSITIVITY = 0.01
INTERSPACE = 20
GROUND_DISTANCE = 100 + EDGE_LENGTH

EASE_MAX = 60

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

class Vector2D:
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __sub__(self, other):
        x = self.x - other.x
        y = self.y = other.y
        return Vector(x, y)

    def __mul__(self, other):
        return self.x * other.y - self.y * other.x

    def magnitude(self):
        return sqrt(self.x**2 + self.y**2)

class Vector:
    def __init__(self, x, y, z, norm=False):
        self.x, self.y, self.z = x, y, z
        if norm:
            self.normalize()

    def __iter__(self):
        return iter([self.x, self.y, self.z])

    def __mul__(self, other):
        if type(other) == type(self):
            return self.x * other.x + self.y * other.y + self.z * other.z
        else:
            return Vector(self.x * other, self.y * other, self.z * other)

    def __truediv__(self, other):
        return Vector(self.x / other, self.y / other, self.z / other)

    def normalize(self):
        r = sqrt(self.x**2 + self.y**2 + self.z**2)
        if r == 0:
            return
        self.x, self.y, self.z = self.x / r, self.y / r, self.z / r

    def toRotationQuaternion(self, half_angle):
        return Quaternion(cos(half_angle),
                          self.x * sin(half_angle),
                          self.y * sin(half_angle),
                          self.z * sin(half_angle))

class Face:
    def __init__(self, a, b, c, d):
        self.points = [a, b, c, d]  # each point is an instance of Point

    def draw(self, canv, cube_center, color):
        pts = []
        for point in self.points:
            # each point is an instance of Point2D
            pts.append(point.perspectivepoint(canv))
        viewable = self.viewability(canv, cube_center)
        if viewable > 0:
            canv.drawFace(pts, brightness=viewable, color=color)

    def viewability(self, canv, cube_center):
        face_center_pt = (self.points[1] + self.points[3]) / 2
        viewer_pt = Point(0, 0, canv.vts + canv.stc)
        self.face_normal_vector = face_center_pt - cube_center
        face_to_viewer_vector = viewer_pt - face_center_pt
        self.face_normal_vector.normalize()
        face_to_viewer_vector.normalize()
        return self.face_normal_vector * face_to_viewer_vector

    def drawShadow(self, canv, gnd):
        pts = []
        for point in self.points:
            shadow_point = Point(point.x, gnd, point.z).perspectivepoint(canv)
            pts.append(shadow_point)
            canv.drawShadow(pts)


class Point2D(object):
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __sub__(self, other):
        x = self.x - other.x
        y = self.y - other.y
        return Vector2D(x, y)

class Point(object):
    def __init__(self, x, y, z):
        self.defx, self.defy, self.defz = x, y, z  # default, reference values (of non-transformed cube)
        self.reset()

    def __iter__(self):
        return iter([self.x, self.y, self.z])

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        # returns vector
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)

    def __truediv__(self, other):
        return Point(self.x / other, self.y / other, self.z / other)

    def reset(self):
        self.x, self.y, self.z = self.defx, self.defy, self.defz
        # initial identity quaternion
        self.rotation_quaternion = Quaternion(1, 0, 0, 0) 

    def transform(self, v, th):
        # rotating point about v (unit vector) by angle th
        new_quat = Quaternion(cos(th/2), *(v * sin(th/2)))
        q = new_quat * self.rotation_quaternion
        if q.a >= 1 or q.a <= -1:
            return
        half_angle = acos(q.a)
        qv = q.toVector() / sin(half_angle)
        qv.normalize()
        a, b, c = qv.x, qv.y, qv.z
        q = self.rotation_quaternion = Vector(a, b, c).toRotationQuaternion(half_angle)
        w = Quaternion(0, self.defx, self.defy, self.defz)
        res = (q * w * q.conj()).toVector()  # resulting point after transformation
        self.x, self.y, self.z = res.x, res.y, res.z

    def perspectivepoint(self, canv):
        # called when drawing point
        ratio = canv.vts / (canv.vts + canv.stc - self.z)
        newx, newy = self.x * ratio, self.y * ratio
        return Point2D(newx + canv.center.x, newy + canv.center.y)

class Quaternion:
    def __init__(self, a, b, c, d):
        self.a, self.b, self.c, self.d = a, b, c, d

    def __mul__(self, other):
        a, b, c, d = self.a, self.b, self.c, self.d
        a_, b_, c_, d_ = other.a, other.b, other.c, other.d
        aa = a*a_ - b*b_ - c*c_ - d*d_
        bb = a*b_ + b*a_ + c*d_ - d*c_
        cc = a*c_ - b*d_ + c*a_ + d*b_
        dd = a*d_ + b*c_ - c*b_ + d*a_
        return Quaternion(aa, bb, cc, dd)

    def __str__(self):
        return "<{}, {}, {}, {}>".format(self.a, self.b, self.c, self.d)

    def conj(self):
        ''' conjugate '''
        return Quaternion(self.a, -self.b, -self.c, -self.d)

    def toVector(self):
        return Vector(self.b, self.c, self.d)

class Cube(object):
    def __init__(self, cube_center, canv, color):
        self.canv = canv
        self.color = color
        e = EDGE_LENGTH / 2
        self.points = [
                cube_center,
                Point( e / 2 + cube_center.x,  e / 2 + cube_center.y,  e / 2 + cube_center.z),
                Point( e / 2 + cube_center.x,  e / 2 + cube_center.y, -e / 2 + cube_center.z),
                Point( e / 2 + cube_center.x, -e / 2 + cube_center.y, -e / 2 + cube_center.z),
                Point( e / 2 + cube_center.x, -e / 2 + cube_center.y,  e / 2 + cube_center.z),
                Point(-e / 2 + cube_center.x, -e / 2 + cube_center.y,  e / 2 + cube_center.z),
                Point(-e / 2 + cube_center.x, -e / 2 + cube_center.y, -e / 2 + cube_center.z),
                Point(-e / 2 + cube_center.x,  e / 2 + cube_center.y, -e / 2 + cube_center.z),
                Point(-e / 2 + cube_center.x,  e / 2 + cube_center.y,  e / 2 + cube_center.z)
        ]

        self.faces = [
                Face(self.points[1], self.points[2], self.points[7], self.points[8]),
                Face(self.points[1], self.points[8], self.points[5], self.points[4]),
                Face(self.points[1], self.points[4], self.points[3], self.points[2]),
                Face(self.points[6], self.points[5], self.points[8], self.points[7]),
                Face(self.points[6], self.points[3], self.points[4], self.points[5]),
                Face(self.points[6], self.points[7], self.points[2], self.points[3])              
        ]

        self.last_mouse_pos = None
        self.update()

    def update(self):
        mouse_pos = self.canv.position
        if mouse_pos is not None and self.last_mouse_pos is not None:
            rot_dir = mouse_pos - self.last_mouse_pos  # type Vector2D
            self.rotation_vector = Vector(-rot_dir.y, rot_dir.x, 0, norm=True)
            self.rotation_angle = rot_dir.magnitude() * INPUT_SENSITIVITY

            for point in self.points:
                point.transform(self.rotation_vector, self.rotation_angle)
        self.last_mouse_pos = mouse_pos
        return self.points[0].z

    def draw(self):
        for face in self.faces:
            face.draw(self.canv, self.points[0], self.color)
            if face.face_normal_vector.y < 0:
                face.drawShadow(self.canv, GROUND_DISTANCE)

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

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    app.exec_()
