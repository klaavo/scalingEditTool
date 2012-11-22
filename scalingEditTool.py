"""
Scaling Edit Tool for RoboFont is a mouse and keyboard controlled version of what are better known
as Interpolated Nudge tools, made famous by Christian Robertson http://betatype.com/node/18
When moving oncurve points, offcurve points are scaled in relation to neighboring oncurve points.
Angles of offcurve points are retained. Command-key and mouse down overrides the angle keeping.
The tool works on both bicubic and quadratic bezier curves, and open and closed contours.
All the built-in Edit Tool functionality should work as expected.  By Timo Klaavo 2012  v. 0.9.1

"""

from mojo.events import EditingTool, installTool
from math import sqrt


def diff(a, b):
    return float(abs(a - b))

def pointData(p0, p1, p2, p3):
    # distances between bPoints:
    distX = diff(p1.anchor[0], p2.anchor[0])
    distY = diff(p1.anchor[1], p2.anchor[1])
    # bcp-to-distance-ratios:
    p1xr = p1.bcpOut[0] / float(distX) if distX != 0 else 0
    p2xr = p2.bcpIn[0] / float(distX) if distX != 0 else 0
    p1yr = p1.bcpOut[1] / float(distY) if distY != 0 else 0
    p2yr = p2.bcpIn[1] / float(distY) if distY != 0 else 0
    # y-to-x- and x-to-y-ratios of bcps:
    p1yx, p1xy, p2yx, p2xy = None, None, None, None
    if 0 not in p1.bcpOut:
        p1yx = p1.bcpOut[1] / float(p1.bcpOut[0])
        p1xy = 1 / p1yx
    if 0 not in p2.bcpIn:
        p2yx = p2.bcpIn[1] / float(p2.bcpIn[0])
        p2xy = 1 / p2yx
    # direction factor of bcp-coordinates, 1 or -1:
    p1dx = -1 if p1.bcpOut[0] < 0 else 1
    p1dy = -1 if p1.bcpOut[1] < 0 else 1
    p2dx = -1 if p2.bcpIn[0] < 0 else 1
    p2dy = -1 if p2.bcpIn[1] < 0 else 1
    # 4 bPoints, 4 bcp-distance-ratios, 4 x-y-ratios, 4 directions:
    return p0, p1, p2, p3, p1xr, p1yr, p2xr, p2yr, p1yx, p1xy, p2yx, p2xy, p1dx, p1dy, p2dx, p2dy

def smoothLines(p, pp, bcpLen):
    # distances between bPoints:
    distX = diff(p.anchor[0], pp.anchor[0])
    distY = diff(p.anchor[1], pp.anchor[1])
    # new bcp-coordinates:
    newX, newY = 0, 0
    if distX != 0:
        lineYXr = distY / float(distX)
        newX = bcpLen / sqrt(lineYXr ** 2 + 1)
    if distY != 0:
        lineXYr = distX / float(distY)
        newY = bcpLen / sqrt(lineXYr ** 2 + 1)
    # line direction factor, 1 or -1:
    ldrx = -1 if p.anchor[0] < pp.anchor[0] else 1
    ldry = -1 if p.anchor[1] < pp.anchor[1] else 1
    return newX * ldrx, newY * ldry


class ScalingEditTool(EditingTool):

    def becomeActive(self):
        self.isArrowKeyDown = 0
        self.buildScaleDataList()

    def currentGlyphChanged(self):
        self.buildScaleDataList()

    def mouseDown(self, point, clickCount):
        self.buildScaleDataList()

    def mouseUp(self, point): # for lasso selections
        self.buildScaleDataList()

    def mouseDragged(self, point, delta):
        if not self.optionDown and not self.commandDown:
            self.scalePoints()

    def modifiersChanged(self):
        if self.isDragging(): # command-key override of angle keeping works only when mouse is down
            self.scalePoints()

    def keyDown(self, event):
        self.isTabDown = True if event.keyCode() == 48 else 0 # if tab or modifier+tab pressed
        if any(self.arrowKeysDown[i] for i in self.arrowKeysDown):
            self.isArrowKeyDown = True
            self.scalePoints()
        elif not self.isDragging() or self.isDragging() and self.isTabDown: # keep command-key logic while dragging
            self.buildScaleDataList() # triggered by tab while dragging, and all keys except arrows while not dragging
        self.isTabDown, self.isArrowKeyDown = 0, 0

    def buildScaleDataList(self):
        if CurrentGlyph():
            glyph = CurrentGlyph()
            self.scaleData = []
            if glyph.selection != []: # stop if there is nothing selected
                for cI in range(len(glyph.contours)):
                    if len(glyph.contours[cI]) > 1: # skip lonesome points
                        contr = glyph.contours[cI]
                        segms = contr.segments[:]
                        if segms[-1].type == 'offCurve': # ignore tailing 'offCurve'-segments in open contour
                            segms = segms[:-1]
                        if segms[0].type == 'move': # put 'move'-segment of open contours from start to end
                            segms = segms[1:] + segms[:1]
                        for pI in range(len(contr.bPoints)):
                            if segms[pI-2].type == 'curve' or segms[pI-2].type == 'qcurve':
                                p1 = contr.bPoints[pI-2] # curve start bPoint
                                p2 = contr.bPoints[pI-1] # curve end bPoint
                                if p1.selected and not p2.selected or p2.selected and not p1.selected:
                                    i3 = 3 if len(segms) > 2 else 1 # cheat with indexes if only 2 points in outline
                                    p0 = contr.bPoints[pI-i3] # previous bPoint
                                    p3 = contr.bPoints[pI] # next bPoint
                                    prevType = segms[pI-i3].type # previous segment type
                                    nextType = segms[pI-1].type # next segment type
                                    p1smooth = segms[pI-i3].points[-1].smooth # p1 smooth bool
                                    p2smooth = segms[pI-2].points[-1].smooth # p2 smooth bool
                                    self.scaleData.append(pointData(p0, p1, p2, p3) + (prevType, nextType, p1smooth, p2smooth))

    def scalePoints(self):
        for i in self.scaleData:

            p0, p1, p2, p3 = i[0], i[1], i[2], i[3] # bPoints p1 and p2 are the ends of scaled curve
            p1xr, p1yr, p2xr, p2yr = i[4],  i[5],  i[6],  i[7]  # bcp-to-bPoint-distance-ratios
            p1yx, p1xy, p2yx, p2xy = i[8],  i[9],  i[10], i[11] # bcp y-to-x and x-to-y ratios
            p1dx, p1dy, p2dx, p2dy = i[12], i[13], i[14], i[15] # original bcp-directions 1 or -1
            prevType, nextType = i[16], i[17] # segment types
            p1smooth, p2smooth = i[18], i[19] # smooth bools

            # scale bcps:
            newDistX = diff(p1.anchor[0], p2.anchor[0])
            newDistY = diff(p1.anchor[1], p2.anchor[1])
            p1.bcpOut = newDistX * p1xr, newDistY * p1yr
            p2.bcpIn = newDistX * p2xr, newDistY * p2yr

            # correct bcp angles:
            if prevType == 'line' and p1smooth: # smooth line before
                bcpLen = sqrt(p1.bcpOut[0] ** 2 + p1.bcpOut[1] ** 2)
                p1.bcpOut = smoothLines(p1, p0, bcpLen)
            elif p1yx: # angled p1.bcpOuts
                if not self.commandDown or self.isArrowKeyDown:
                    bcpLen = sqrt(p1.bcpOut[0] ** 2 + p1.bcpOut[1] ** 2)
                    newX = bcpLen / sqrt(p1yx ** 2 + 1)
                    newY = bcpLen / sqrt(p1xy ** 2 + 1)
                    p1.bcpOut = newX * p1dx, newY * p1dy

            if nextType == 'line' and p2smooth: # smooth line after
                bcpLen = sqrt(p2.bcpIn[0] ** 2 + p2.bcpIn[1] ** 2)
                p2.bcpIn = smoothLines(p2, p3, bcpLen)
            elif p2yx: # angled p2.bcpIns
                if not self.commandDown or self.isArrowKeyDown:
                    bcpLen = sqrt(p2.bcpIn[0] ** 2 + p2.bcpIn[1] ** 2)
                    newX = bcpLen / sqrt(p2yx ** 2 + 1)
                    newY = bcpLen / sqrt(p2xy ** 2 + 1)
                    p2.bcpIn = newX * p2dx, newY * p2dy


installTool(ScalingEditTool())