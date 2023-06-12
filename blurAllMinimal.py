import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import os

def blur(I, faceBoxes, extraMask=None, gaussianFraction=0.1, diagonalExpand=0.15, hardBlurInsideFace=False):
    """
    Blur an image to redact regions:
        I:  
            The image to be blurred as a PIL image object

        faceBoxes:
            A list of tuples that define the boxes to be redacted. 
            These are in [(minX, minY, maxX, maxY), ...] format

        extraMask:
            a boolean image that is also additionally always blurred

        gaussianFraction:
            The standard deviation of the gaussian filter, expressed as a
            fraction of the maximum diagonal of the boxes.

        diagonalExpand:
            The size to expand the box by, expressed as a fraction of the 
            maximum diagonal of the boxes. The blurred faces will be 
            [(minX - diagonalExpand * maxDiagonal,
              minY - diagonalExpand * maxDiagonal, 
              maxX + diagonalExpand * maxDiagonal, 
              maxY + diagonalExpand * maxDiagonal), ...]

        hardBlurInsideFace:
            Whether to force hard-face boxes to be totally blurred. This setting
            leads to box artifacts and should not be necessary unless there are
            enormous faces next to tiny faces. Need has been seen only so far
            in synthetic test cases.

    Based extensively off Kaiyu Yang's Code
        https://github.com/princetonvisualai/imagenet-face-obfuscation/blob/main/experiments/blurring.py
    with modifications:
    (1) the amount that the box is expanded by is determined by the maximum 
        diagonal in the image
    (2) added an optional redaction mask
    (3) via the associated calling code, this avoids/reduces double-jpg'ing
            
    """
    def drawBoxes(drawer, exp):
        for bbox in faceBoxes:
            x0, y0, x1, y1 = bbox
            x0E = x0 - exp * maxDiagonal
            y0E = y0 - exp * maxDiagonal
            x1E = x1 + exp * maxDiagonal
            y1E = y1 + exp * maxDiagonal
            drawer.rectangle((x0E, y0E, x1E, y1E), fill="black")


    M = Image.new(mode="L", size=I.size, color="white")
    h, w = I.size

    #assume a minimal size
    maxDiagonal = 0.025*np.hypot(h,w)

    #need to first go through and figure out the blur size, otherwise this 
    #doesn't work if there are faces of widely varying sizes
    for bbox in faceBoxes:
        x0, y0, x1, y1 = bbox
        diagonal = np.hypot(y1-y0,x1-x0)
        maxDiagonal = max(diagonal, maxDiagonal)

    #now suppress uniformly based on this size
    drawBoxes(ImageDraw.Draw(M), diagonalExpand)

    if extraMask is not None:
        MArray = np.array(M)
        MArray[extraMask] = 0.0
        M = Image.fromarray(MArray)

    IF = ImageFilter.GaussianBlur(gaussianFraction*maxDiagonal)
    blurredI = I.filter(IF)
    blurredM = M.filter(IF)

    if hardBlurInsideFace:
        #for being doubly cautious, it could make sense to force the face to
        #be blurred
        drawBoxes(ImageDraw.Draw(blurredM), 0.0)

    if extraMask is not None:
        MArray = np.array(blurredM)
        MArray[extraMask] = 0.0
        blurredM = Image.fromarray(MArray)
   
    return Image.composite(I,blurredI,blurredM)


def handle(src, target, boxes, **kwArgs):
    #load the image
    I = Image.open(src)

    #blur
    res = blur(I, boxes, **kwArgs)
    
    # sticking it into the object enables re-using the same quality, 
    #subsampling and quantization
    I.paste(res) 

    #save using the original object
    #Kudos to David Pinto for pointing out how to save the info 
    I.save(target, quality="keep", **I.info)



def handleBad(src, target, boxes, **kwArgs):
    #load the image
    I = Image.open(src)

    #blur
    res = blur(I, boxes, **kwArgs)

    #save
    res.save(target)
    

if __name__ == "__main__":

    image2Boxes = {
        "crop5.jpg": [(269,163,547,518)],
        "calder.jpg": [(363,442,390,471)]
    }

    #file name
    src = "calder.jpg"

    #whether to show the difference image 
    showDiff = True


    boxes = image2Boxes[src]


    base, ext = os.path.splitext(src)
    
    mask = None
    if os.path.exists(base+"mask.png"):
        mask = np.array( Image.open(base+"mask.png").convert("L") ) > 128

    targetFolder = base
    if not os.path.exists(targetFolder):
        os.mkdir(targetFolder) 

    target = os.path.join(targetFolder,"blur"+ext)
    handle(src, target, boxes, extraMask=mask)


    if showDiff:
        targetBad = os.path.join(targetFolder,"blurbad"+ext)
        diffImage = os.path.join(targetFolder, "diff.png")
        diffImageBad = os.path.join(targetFolder, "diffbad.png")
        diffScale = 10
        handleBad(src, targetBad, boxes, extraMask=mask)

        #load the results
        beforeImage = np.array(Image.open(src).convert("RGB")).astype(float)
        afterImage = np.array(Image.open(target).convert("RGB")).astype(float)
        afterImageBad = np.array(Image.open(targetBad).convert("RGB")).astype(float)
       
        #compute the differences and scale
        diff = (np.abs(beforeImage - afterImage) * diffScale).astype(np.uint8)
        diffBad = (np.abs(beforeImage - afterImageBad) * diffScale).astype(np.uint8)
       
        #and save
        Image.fromarray(diff).save(diffImage)
        Image.fromarray(diffBad).save(diffImageBad)



