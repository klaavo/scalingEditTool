"""
Scaling Edit Tool for RoboFont is a mouse and keyboard controlled version
of what are better known as Interpolated Nudge tools, made famous by
Christian Robertson http://www.christianrobertson.com
When moving oncurve points, offcurve points are scaled in relation to
neighboring oncurve points. The tool works on both bicubic and quadratic
bezier curves, and open and closed contours. All the built-in Edit Tool
functionality should work as expected. Angles of offcurve points are retained
by default. Command-key overrides the angle keeping when mouse is down.
In contextual menu (right mouse click) you can choose whether or not smooth and
non-selected points are affected by the override. Simplified mode offers
a more traditional operation without angle keeping.
"""

from mojo.events import EditingTool, installTool
from mojo.extensions import getExtensionDefault, setExtensionDefault
from mojo.roboFont import version
from AppKit import NSImage
from math import sqrt
from os import path


dirname = path.dirname(__file__)
toolbarIcon = NSImage.alloc().initByReferencingFile_(path.join(dirname, "scalingEditToolbarIcon.pdf"))


def diff(a, b, c=0):
    return float(abs(a - b)) if c == 0 else float(a - b)


def pointData(p1, p2, p1Ut, p2In, simplified):
    # distances between points:
    distX = diff(p1.x, p2.x, simplified)
    distY = diff(p1.y, p2.y, simplified)
    # relative offcurve coordinates
    p1Bcp = p1Ut.x - p1.x, p1Ut.y - p1.y
    p2Bcp = p2In.x - p2.x, p2In.y - p2.y
    # bcp-to-distance-ratios:
    p1xr = p1Bcp[0] / float(distX) if distX else 0
    p2xr = p2Bcp[0] / float(distX) if distX else 0
    p1yr = p1Bcp[1] / float(distY) if distY else 0
    p2yr = p2Bcp[1] / float(distY) if distY else 0
    # y-to-x- and x-to-y-ratios of bcps:
    p1yx, p1xy, p2yx, p2xy = None, None, None, None
    if 0 not in p1Bcp:
        p1yx = p1Bcp[1] / float(p1Bcp[0])
        p1xy = 1 / p1yx
    if 0 not in p2Bcp:
        p2yx = p2Bcp[1] / float(p2Bcp[0])
        p2xy = 1 / p2yx
    # direction multiplier of bcp-coordinates, 1 or -1:
    p1dx = -1 if p1Bcp[0] < 0 else 1
    p1dy = -1 if p1Bcp[1] < 0 else 1
    p2dx = -1 if p2Bcp[0] < 0 else 1
    p2dy = -1 if p2Bcp[1] < 0 else 1
    # 4 points, 4 bcp-distance-ratios, 4 x-y-ratios, 4 directions,
    return p1, p2, p1Ut, p2In, p1xr, p1yr, p2xr, p2yr, p1yx, p1xy, p2yx, p2xy, p1dx, p1dy, p2dx, p2dy


def smoothLines(p, pp, offCurve):
    # bcp length from relative coordinates
    bcp = offCurve.x - p.x, offCurve.y - p.y
    bcpLen = sqrt(bcp[0] ** 2 + bcp[1] ** 2)
    # distances between points:
    distX = diff(p.x, pp.x)
    distY = diff(p.y, pp.y)
    # new relative coordinates:
    newX, newY = 0, 0
    if distX:
        lineYXr = distY / float(distX)
        newX = bcpLen / sqrt(lineYXr ** 2 + 1)
    if distY:
        lineXYr = distX / float(distY)
        newY = bcpLen / sqrt(lineXYr ** 2 + 1)
    # line direction:
    ldrx = -1 if p.x < pp.x else 1
    ldry = -1 if p.y < pp.y else 1
    # new absolute coordinates
    return newX * ldrx + p.x, newY * ldry + p.y


def keepAngles(p, offCurve, pyx, pxy, pdx, pdy):
    # bcp length from relative coordinates:
    bcp = offCurve.x - p.x, offCurve.y - p.y
    bcpLen = sqrt(bcp[0] ** 2 + bcp[1] ** 2)
    # new relative coordinates:
    newX = bcpLen / sqrt(pyx ** 2 + 1)
    newY = bcpLen / sqrt(pxy ** 2 + 1)
    # new absolute coordinates
    return newX * pdx + p.x, newY * pdy + p.y


class ScalingEditTool(EditingTool):

    def getToolbarIcon(self):
        return toolbarIcon

    def getToolbarTip(self):
        return "Scaling Edit"

    def additionContectualMenuItems(self):  # Up to RF 1.6
        selectText = 'Turn On Non-Selected' if self.settings['selectOnly'] else 'Turn Off Non-Selected'
        smoothText = 'Turn Off Smooths' if self.settings['smoothsToo'] else 'Turn On Smooths'
        simpliText = 'Turn Off Simplified Mode' if self.settings['simplified'] else 'Turn On Simplified Mode'
        return [('Angle Keeping Override (cmd-key)', [(selectText, self.menuCallSelected), (smoothText, self.menuCallSmooths)]), (simpliText, self.menuCallSimplified)]

    def additionContextualMenuItems(self):  # RF 1.7
        selectText = 'Turn On Non-Selected' if self.settings['selectOnly'] else 'Turn Off Non-Selected'
        smoothText = 'Turn Off Smooths' if self.settings['smoothsToo'] else 'Turn On Smooths'
        simpliText = 'Turn Off Simplified Mode' if self.settings['simplified'] else 'Turn On Simplified Mode'
        return [('Angle Keeping Override (cmd-key)', [(selectText, self.menuCallSelected), (smoothText, self.menuCallSmooths)]), (simpliText, self.menuCallSimplified)]

    def menuCallSelected(self, call):
        self.settings['selectOnly'] = False if self.settings['selectOnly'] else True
        setExtensionDefault('com.timoklaavo.scalingEditTool.selectOnly', self.settings['selectOnly'])

    def menuCallSmooths(self, call):
        self.settings['smoothsToo'] = False if self.settings['smoothsToo'] else True
        setExtensionDefault('com.timoklaavo.scalingEditTool.smoothsToo', self.settings['smoothsToo'])

    def menuCallSimplified(self, call):
        self.settings['simplified'] = False if self.settings['simplified'] else True
        setExtensionDefault('com.timoklaavo.scalingEditTool.simplified', self.settings['simplified'])
        self.buildScaleDataList()

    def defaultSettings(self):
        self.settings = {}
        self.settings['selectOnly'] = getExtensionDefault('com.timoklaavo.scalingEditTool.selectOnly', fallback=False)
        self.settings['smoothsToo'] = getExtensionDefault('com.timoklaavo.scalingEditTool.smoothsToo', fallback=True)
        self.settings['simplified'] = getExtensionDefault('com.timoklaavo.scalingEditTool.simplified', fallback=False)

    def becomeActive(self):
        self.defaultSettings()
        self.glyph = CurrentGlyph()
        self.buildScaleDataList()

    def currentGlyphChanged(self):
        self.glyph = CurrentGlyph()
        self.buildScaleDataList()

    def mouseDown(self, point, clickCount):
        self.buildScaleDataList()

    def mouseUp(self, point):  # for lasso selections
        self.buildScaleDataList()

    def mouseDragged(self, point, delta):
        if not self.optionDown and not self.commandDown:  # allow default option and command behavior
            self.scalePoints()

    def modifiersChanged(self):
        if self.isDragging():  # command-key override of angle keeping works only when mouse is down
            self.scalePoints()
            if version >= '2.0.0':  # RF2 and later
                self.glyph.changed()
            else:  # RF1
                self.glyph.update()

    def keyDown(self, event):
        if any(self.arrowKeysDown[i] for i in self.arrowKeysDown):
            self.scalePoints(arrowKeyDown=True)
        elif not self.isDragging() or self.isDragging() and event.keyCode() == 48:  # 48 = tab or modifier+tab
            self.buildScaleDataList()  # triggered by tab while dragging, and all keys except arrows while not dragging

    def buildScaleDataList(self, selectionChanged=0):
        self.scaleData = []
        if self.glyph and self.glyph.selectedPoints != []:  # stop if there is nothing selected
            for cI in range(len(self.glyph.contours)):
                if len(self.glyph.contours[cI]) > 1:  # skip lonesome points
                    contr = self.glyph.contours[cI]
                    segms = contr.segments[:]
                    segms = segms[:-1] if segms[-1].type == 'offCurve' else segms  # ignore tailing 'offCurve'-segments in open contours
                    segms = segms[1:] + segms[:1] if segms[0].type == 'move' else segms  # 'move'-segment of open contours from beginning to end
                    for pI in range(len(segms)):
                        if segms[pI-2].type == 'curve' or segms[pI-2].type == 'qcurve':  # not 'offCurve', 'line', 'move' or such
                            i3 = 3 if len(segms) > 2 else 1  # cheat with indexes if only 2 points in contour
                            p1 = segms[pI - i3].points[-1]  # point in beginning of curve to be scaled
                            p2 = segms[pI - 2].points[-1]  # ending point of curve to be scaled
                            if p1.selected and not p2.selected or p2.selected and not p1.selected:
                                p3 = segms[pI - 1].points[-1]  # next onCurve point after p2
                                p0 = segms[pI - i3 - 1].points[-1] if len(segms) != 3 else p3  # previous onCurve point, p0 is p3 in 3-point outline
                                p1Ut = segms[pI - 2].points[-3]  # out-point of p1
                                p2In = segms[pI - 2].points[-2]  # in-point of p2
                                prevType = segms[pI - i3].type  # previous segment type
                                nextType = segms[pI - 1].type  # next segment type
                                self.scaleData.append(pointData(p1, p2, p1Ut, p2In, self.settings['simplified']) + (p0, p3, prevType, nextType))

    def scalePoints(self, arrowKeyDown=0):
        if not self.transformMode():  # normal behavior in transform mode
            for i in self.scaleData:

                p1, p2 = i[0], i[1]  # two onCurve points of the segment to be scaled
                p1Ut, p2In = i[2], i[3]  # out and in offCurve points of the curve
                p1xr, p1yr, p2xr, p2yr = i[4], i[5], i[6], i[7]
                p1yx, p1xy, p2yx, p2xy = i[8], i[9], i[10], i[11]
                p1dx, p1dy, p2dx, p2dy = i[12], i[13], i[14], i[15]
                p0, p3 = i[16], i[17]  # previous and next onCurve points
                prevType, nextType = i[18], i[19]  # previous and next segment types

                # scale curve
                newDistX = diff(p1.x, p2.x, self.settings['simplified'])
                newDistY = diff(p1.y, p2.y, self.settings['simplified'])
                p1UtX, p1UtY = newDistX * p1xr + p1.x, newDistY * p1yr + p1.y
                p2InX, p2InY = newDistX * p2xr + p2.x, newDistY * p2yr + p2.y
                p1Ut.x, p1Ut.y, p2In.x, p2In.y = p1UtX, p1UtY, p2InX, p2InY

                # correct offCurve angles
                if not self.settings['simplified']:
                    if prevType == 'line' and p1.smooth:  # smooth line before
                        p1Ut.x, p1Ut.y = smoothLines(p1, p0, p1Ut)
                    elif p1yx:  # diagonal p1Ut
                        p1Ut.x, p1Ut.y = keepAngles(p1, p1Ut, p1yx, p1xy, p1dx, p1dy)
                        if not arrowKeyDown and self.commandDown:  # keep angle override
                            if self.settings['smoothsToo'] or not self.settings['smoothsToo'] and not p1.smooth:
                                if self.settings['selectOnly'] and p1.selected or not self.settings['selectOnly']:
                                    p1Ut.x, p1Ut.y = p1UtX, p1UtY

                    if nextType == 'line' and p2.smooth:  # smooth line after
                        p2In.x, p2In.y = smoothLines(p2, p3, p2In)
                    elif p2yx:  # diagonal p2In
                        p2In.x, p2In.y = keepAngles(p2, p2In, p2yx, p2xy, p2dx, p2dy)
                        if not arrowKeyDown and self.commandDown:  # keep angle override
                            if self.settings['smoothsToo'] or not self.settings['smoothsToo'] and not p2.smooth:
                                if self.settings['selectOnly'] and p2.selected or not self.settings['selectOnly']:
                                    p2In.x, p2In.y = p2InX, p2InY


installTool(ScalingEditTool())
