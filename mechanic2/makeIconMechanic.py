import os

folder = os.getcwd()
baseFolder = os.path.dirname(folder)
imgPath = os.path.join(baseFolder, 'ScalingEditTool.roboFontExt/lib/ScalingEditToolbarIcon.pdf')

size(300, 300)
fill(1)
rect(0, 0, width(), height())
translate(21, 21)
scale(14)
image(imgPath, (0, 0))

outputPath = os.path.join(folder, 'ScalingEditMechanicIcon.png')
saveImage(outputPath)
