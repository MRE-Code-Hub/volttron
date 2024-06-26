# -*- coding: utf-8 -*- {{{
# ===----------------------------------------------------------------------===
#
#                 Component of Eclipse VOLTTRON
#
# ===----------------------------------------------------------------------===
#
# Copyright 2023 Battelle Memorial Institute
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# ===----------------------------------------------------------------------===
# }}}

import numpy as np

def cmp(a, b):
    return (a > b) - (a < b)

class PolyLine:
    def __init__(self):
        self.points = []
        self.xs = None
        self.ys = None
        self.xsSortedByY = None
        self.ysSortedByY = None
        self._min_x = None
        self._max_x = None
        self._min_y = None
        self._max_y = None

    def add(self, point):
        if self.points is None:
            self.points = []
        if len(self.points) > 0:
            for p in reversed(self.points):
                if p.x == point.x and p.y == point.y:
                    return
        doSort = False
        # if len(self.points) > 0 and point.y < self.points[-1].y:
        if len(self.points) > 0:
            doSort = True

        self.points.append(point)
        if doSort:
            self.points.sort(key=lambda tup: tup[1], reverse=True)
        self.xs = None
        self.ys = None
        if point.x is not None and point.y is not None:
            self._min_x = PolyLine.min(self._min_x, point.x)
            self._min_y = PolyLine.min(self._min_y, point.y)
            self._max_x = PolyLine.max(self._max_x, point.x)
            self._max_y = PolyLine.max(self._max_y, point.y)

    def contains_none(self):
        result = False
        if self.points is not None and len(self.points) > 0:
            for p in self.points:
                if p.x is None or p.y is None:
                    result = True
        return result

    @staticmethod
    def min(x1, x2):
        if x1 is None:
            return x2
        if x2 is None:
            return x1
        return min(x1, x2)

    @staticmethod
    def max(x1, x2):
        if x1 is None:
            return x2
        if x2 is None:
            return x1
        return max(x1, x2)

    @staticmethod
    def sum(x1, x2):
        if x1 is None:
            return x2
        if x2 is None:
            return x1
        return x1 + x2

    def x(self, y):
        if not self.points:
            return None
        if y is None:
            return None
        self.vectorize()
        # return np.interp(y, self.ys, self.xs) #, right=0.) .. we learned that this gave weird results previously
        # ascending = self.ys[0]<self.ys[-1]
        # ys = self.ys if ascending else self.ys[::-1]
        # xs = self.xs if ascending else self.xs[::-1]
        r = np.interp(y, self.ysSortedByY, self.xsSortedByY)
        return None if np.isnan(r) else r

    def y(self, x):
        if not self.points:
            return None
        if x is None:
            return None
        self.vectorize()
        # return np.interp(x, self.xs, self.ys) # this probably doesn't work b/c the xs are not neccesarily in the right order...
        # ascending = self.xs[0]<self.xs[-1]
        # ys = self.ys if ascending else self.ys[::-1]
        # xs = self.xs if ascending else self.xs[::-1]
        r = np.interp(x, self.xs, self.ys)
        return None if np.isnan(r) else r

    # probably replace w/ zip()
    def vectorize(self):
        if not self.points:
            return None, None
        if (self.xs == None or self.ys == None):
            xs = [None] * len(self.points)
            ys = [None] * len(self.points)
            c = 0
            for p in self.points:
                xs[c] = p.x
                ys[c] = p.y
                c += 1
            self.xs = xs
            self.ys = ys
            if self.ys[0] < self.ys[-1]:
                self.xsSortedByY = self.xs
                self.ysSortedByY = self.ys
            else:
                self.xsSortedByY = self.xs[::-1]
                self.ysSortedByY = self.ys[::-1]
        return self.xs, self.ys

    def tuppleize(self):
        if not self.points:
            return None
        ps = [None] * len(self.points)
        c = 0
        for p in self.points:
            ps[c] = p.tuppleize()
            c += 1
        return ps

    def min_y(self):
        return self._min_y

    def max_y(self):
        return self._max_y

    def min_x(self):
        return self._min_x

    def max_x(self):
        return self._max_x

    @staticmethod
    def determinant(point1, point2):
        return point1[0] * point2[1] - point1[1] * point2[0]

    @staticmethod
    def segment_intersection(line1, line2):
        xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
        ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])
        div = PolyLine.determinant(xdiff, ydiff)
        if div == 0:
            return None, None
        d = (PolyLine.determinant(*line1), PolyLine.determinant(*line2))
        x = PolyLine.determinant(d, xdiff) / div
        y = PolyLine.determinant(d, ydiff) / div
        return x, y

    @staticmethod
    def ccw(p1, p2, p3):
        return (p3[1] - p1[1]) * (p2[0] - p1[0]) > (p2[1] - p1[1]) * (p3[0] - p1[0])

    @staticmethod
    def segment_intersects(l1, l2):
        if l1[0][0] is None or l1[0][1] is None or l1[1][0] is None or l1[1][1] is None:
            return False
        if l2[0][0] is None or l2[0][1] is None or l2[1][0] is None or l2[1][1] is None:
            return False
        if (PolyLine.ccw(l1[0], l2[0], l2[1]) != PolyLine.ccw(l1[1], l2[0], l2[1])
            and PolyLine.ccw(l1[0], l1[1], l2[0]) != PolyLine.ccw(l1[0], l1[1], l2[1])):
            return True
        if (l1[0][0] == l2[0][0] and l1[0][1] == l2[0][1]) or (l1[0][0] == l2[1][0] and l1[0][1] == l2[1][1]):
            return True
        if (l1[1][0] == l2[0][0] and l1[1][1] == l2[0][1]) or (l1[1][0] == l2[1][0] and l1[1][1] == l2[1][1]):
            return True

    @staticmethod
    def between(a, b, c):
        if (a[0] is None or a[1] is None or b[0] is None or b[1] is None or c[0] is None or c[1] is None):
            return None
        crossproduct = (c[1] - a[1]) * (b[0] - a[0]) - (c[0] - a[0]) * (b[1] - a[1])
        if abs(crossproduct) > 1e-12:
            return False
        dotproduct = (c[0] - a[0]) * (b[0] - a[0]) + (c[1] - a[1]) * (b[1] - a[1])
        if dotproduct < 0:
            return False
        squaredlengthba = (b[0] - a[0]) * (b[0] - a[0]) + (b[1] - a[1]) * (b[1] - a[1])
        if dotproduct > squaredlengthba:
            return False
        return True

    @staticmethod
    def intersection(pl_1, pl_2):
        pl_1 = pl_1.points
        pl_2 = pl_2.points

        # we have two points
        if len(pl_1) == 1 and len(pl_2) == 1:
            if pl_1[0][0] == pl_2[0][0] and pl_1[0][1] == pl_2[0][1]:
                quantity = pl_1[0][0]
                price = pl_1[0][1]
                return quantity, price

        # we have one point and line segments
        elif len(pl_1) == 1 or len(pl_2) == 1:
            if len(pl_1) == 1:
                point = pl_1[0]
                line = pl_2
            else:
                point = pl_2[0]
                line = pl_1
            for j, pl_2_1 in enumerate(line[:-1]):
                pl_2_2 = line[j + 1]
                if PolyLine.between(pl_2_1, pl_2_2, point):
                    quantity = point[0]
                    price = point[1]
                    return quantity, price

        # we have line segments
        elif len(pl_1) > 1 and len(pl_2) > 1:
            for i, pl_1_1 in enumerate(pl_1[:-1]):
                pl_1_2 = pl_1[i + 1]
                for j, pl_2_1 in enumerate(pl_2[:-1]):
                    pl_2_2 = pl_2[j + 1]
                    if PolyLine.segment_intersects((pl_1_1, pl_1_2), (pl_2_1, pl_2_2)):
                        quantity, price = PolyLine.segment_intersection((pl_1_1, pl_1_2), (pl_2_1, pl_2_2))
                        return quantity, price
        p1_qmax = max([point[0] for point in pl_1])
        p1_qmin = min([point[0] for point in pl_1])

        p2_qmax = max([point[0] for point in pl_2])
        p2_qmin = min([point[0] for point in pl_2])

        p1_pmax = max([point[1] for point in pl_1])
        p2_pmax = max([point[1] for point in pl_2])

        p1_pmin = min([point[1] for point in pl_1])
        p2_pmin = min([point[1] for point in pl_2])
        # The lines don't intersect, add the auxillary information
        # TODO - clean this method up.
        if p1_pmax <= p2_pmax and p1_pmax <=p2_pmin:
            quantity = p1_qmin
            price = p2_pmax

        elif p2_pmin <=p1_pmin and p2_pmax <=p1_pmin:
            quantity = p1_qmax
            price = p2_pmin

        elif p2_qmax >= p1_qmin and p2_qmax >= p1_qmax:
            quantity = np.mean([point[0] for point in pl_1])
            price = np.mean([point[1] for point in pl_1])

        elif p2_qmin <= p1_qmin and p2_qmin <= p1_qmax:
            quantity = p2_qmax
            price = p1_pmax

        else:
            price = None
            quantity = None

        return quantity, price

    @staticmethod
    def line_intersection(line1, line2):
        x1x3 = line1[0][0]-line2[0][0]
        y3y4 = line2[0][1]-line2[1][1]
        y1y3 = line1[0][1]-line2[0][1]
        y1y2 = line1[0][1]-line1[1][1]
        x3x4 = line2[0][0]-line2[1][0]
        x1x2 = line1[0][0]-line1[1][0]
        y1y3 = line1[0][1]-line2[0][1]
        if x1x2*y3y4 - y1y2*x3x4 == 0:
            return None
        t = (x1x3*y3y4 - y1y3*x3x4)/(x1x2*y3y4 - y1y2*x3x4)
        #    u=(x1x2*y1y3-y1y2*x1x3)/(x1x2*y3y4-y1y2*x3x4)
        x = line1[0][0] + t*(line1[1][0] - line1[0][0])
        y = line1[0][1] + t*(line1[1][1] - line1[0][1])
        #       if x>max(line1[0][0],line1[1][0]) or x>max(line2[0][0],line2[1][0]) or x<min(line1[0][0],line1[1][0]) or x<min(line2[0][0],line2[1][0]) or y>max(line1[0][1],line1[1][1]) or y>max(line2[0][1],line2[1][1]) or y<min(line1[0][1],line1[1][1]) or y<min(line2[0][1],line2[1][1]):
        #                return x
        if y > max(line1[0][1], line1[1][1]):
                 return min(line1[0][0], line1[1][0]), y
        if y > max(line2[0][1], line2[1][1]):
                 return min(line2[0][0], line2[1][0]), y
        if y < min(line1[0][1], line1[1][1]):
                 return max(line1[0][0], line1[1][0]), y
        if y < min(line2[0][1], line2[1][1]):
            return max(line2[0][0], line2[1][0]), y
        return x, y

    @staticmethod
    def poly_intersection(poly1, poly2):
        poly1 = poly1.points
        poly2 = poly2.points
        for i, p1_first_point in enumerate(poly1[:-1]):
            p1_second_point = poly1[i + 1]

            for j, p2_first_point in enumerate(poly2[:-1]):
                p2_second_point = poly2[j + 1]

                if PolyLine.line_intersection((p1_first_point, p1_second_point), (p2_first_point, p2_second_point)):
                    x, y = PolyLine.line_intersection((p1_first_point, p1_second_point), (p2_first_point, p2_second_point))
                    return x, y

        return False

    @staticmethod
    def compare(demand_curve, supply_curve):
        aux = {}
        demand_max_quantity = demand_curve.max_x()
        demand_min_quantity = demand_curve.min_x()
        supply_max_quantity = supply_curve.max_x()
        supply_min_quantity = supply_curve.min_x()
        demand_max_price = demand_curve.max_y()
        demand_min_price = demand_curve.min_y()
        supply_max_price = supply_curve.max_y()
        supply_min_price = supply_curve.min_y()

        aux['SQn,DQn'] = (supply_min_quantity > demand_min_quantity) - (supply_min_quantity < demand_min_quantity)
        aux['SQn,DQx'] = (supply_min_quantity > demand_max_quantity) - (supply_min_quantity < demand_max_quantity)
        aux['SQx,DQn'] = (supply_max_quantity > demand_min_quantity) - (supply_max_quantity < demand_min_quantity)
        aux['SQx,DQx'] = (supply_max_quantity > demand_max_quantity) - (supply_max_quantity < demand_max_quantity)

        aux['SPn,DPn'] = (supply_min_price > demand_min_price) - (supply_min_price < demand_min_price)
        aux['SPn,DPx'] = (supply_min_price > demand_max_price) - (supply_min_price < demand_max_price)
        aux['SPx,DPn'] = (supply_max_price > demand_min_price) - (supply_max_price < demand_min_price)
        aux['SPx,DPx'] = (supply_max_price > demand_max_price) - (supply_max_price < demand_max_price)
        return aux
