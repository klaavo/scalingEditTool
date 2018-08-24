import os

imgPath = '/_code/_extensions/scalingEditTool/ScalingEditTool.roboFontExt/lib/ScalingEditToolbarIcon.pdf'

size(300, 300)
translate(21, 21)
scale(14)
image(imgPath, (0, 0))

folder = os.path.split(imgPath)[0]
outputPath = os.path.join(folder, 'ScalingEditMechanicIcon.png')

saveImage(outputPath)
