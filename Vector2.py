from math import sqrt


class Vector2:
    def __init__(self, x = 0, y =0):
        self.X = x
        self.Y = y

    def add(self, x, y):
        self.X += x
        self.Y += y
        return self

    def __repr__(self):
        return "".join(["Vector2(", str(self.X), ",", str(self.Y), ")"])

    @staticmethod
    def dist(point_from, point_to):
        return sqrt((point_from.X - point_to.X) ** 2 + (point_from.Y - point_to.Y) ** 2)

    def dist(self, point_to):
        return Vector2.dist(self, point_to)
