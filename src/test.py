import numpy as np
import cv2
import sys
import sac 
import delaunayMorphing
import roughCalibrator

img1 = None
img2 = None
pointsImg1 = []
pointsImg2 = []
sacInstance = None
radiusSize = 0.003
rectangleWitdh = 0.0008

def myFilledCircle(img, center):
	global radiusSize
	thickness = -1
	lineType = 8
	shape = img.shape
	radius = int((shape[0] + shape[1]) * radiusSize)
	cv2.circle (img, center, radius, (0,0,255), thickness, lineType)

numberOfPointPairs = 0
dragStart = None
rectangle = False
waitingForSecondPoint = False
previousPoint = -1
def onMouse(event, x, y, flags, imageSelect):
	global dragStart, sacInstance, rectangle, rectangleWitdh, waitingForSecondPoint, previousPoint, numberOfPointPairs
	if imageSelect:
		img1Temp = img1
		img2Temp = img2
		img1Name = "Image 1"
		img2Name = "Image 2"
	else:
		img1Temp = img2
		img2Temp = img1
		img1Name = "Image 2"
		img2Name = "Image 1"
	
	# Mouse movement, rectangle drawing
	if event == cv2.EVENT_MOUSEMOVE:
		if rectangle == True:
			img3 = img1Temp.copy()
			shape = img3.shape
			width = int((shape[0] + shape[1]) * rectangleWitdh)
			cv2.rectangle(img3, dragStart, (x, y), (50,255,50), width)
			cv2.imshow(img1Name, img3)
	# Right mouse button
	elif event == cv2.EVENT_RBUTTONDOWN and rectangle is False:
		if (waitingForSecondPoint and (imageSelect + previousPoint) == 1):
			rectangle = True
			dragStart = x, y
			waitingForSecondPoint = False
			previousPoint =  -1
			numberOfPointPairs += 1
		elif not waitingForSecondPoint:
			rectangle = True
			dragStart = x, y
			waitingForSecondPoint = True
			previousPoint = imageSelect
	elif event == cv2.EVENT_RBUTTONUP and rectangle is True:
		dragEnd = x, y
		# get point inside user drawn rectangle
		point = sacInstance.getPointFromRectangle(dragStart, dragEnd, imageSelect)
		if imageSelect:
			pointsImg1.append(point)
		else:
			pointsImg2.append(point)
		rectangle = False
		myFilledCircle(img1Temp, point)
		cv2.imshow(img1Name, img1Temp)
		# calibrate the two images roughly afte two point pairs are marked
		if waitingForSecondPoint == False and numberOfPointPairs == 4:
			print ("Rougly calibrating images...")
			roughCalibrator.calibrate(img1, img2, pointsImg1, pointsImg2)
			cv2.imshow(img1Name, img1Temp)
			cv2.imshow(img2Name, img2Temp)
	# Left mouse button
	elif event == cv2.EVENT_LBUTTONDOWN and not waitingForSecondPoint and rectangle is False:
		rectangle = True
		dragStart = x, y
	elif event == cv2.EVENT_LBUTTONUP and rectangle is True and not waitingForSecondPoint:
		dragEnd = x,y
		rectangle = False
		# get point in rectangle and coresponding point 
		point1, point2 = 	sacInstance.getPFromRectangleACorespondingP(dragStart, dragEnd, imageSelect)
		if imageSelect:
			pointsImg1.append(point1)
			pointsImg2.append(point2)
		else:
			pointsImg1.append(point2)
			pointsImg2.append(point1)
		numberOfPointPairs += 1
		myFilledCircle(img1Temp, point1)
		myFilledCircle(img2Temp, point2)
		cv2.imshow(img1Name, img1Temp)
		cv2.imshow(img2Name, img2Temp)
		# calibrate the two images roughly afte two point pairs are marked
		if waitingForSecondPoint == False and numberOfPointPairs == 4:
			print ("Rougly calibrating images...")
			roughCalibrator.calibrate(img1, img2, pointsImg1, pointsImg2)
			cv2.imshow(img1Name, img1Temp)
			cv2.imshow(img2Name, img2Temp)

def test():
	global img1, img2, sacInstance
	"""
	Test method for semiautomatic point corespondence.
	"""
	if len(sys.argv) < 3:
		print ("Usage: test <imageName1> <imageName2>")
		exit()

	img1, img2  = cv2.imread(sys.argv[1]), cv2.imread(sys.argv[2])

	if img1 is None:
		print ("Image 1 not readable or not found")
		exit()
	if img2 is None:
		print ("Image 2 not readable or not found")
		exit()

	print ("Draw rectangles with LMB to search for corresponding point.")
	print ("Draw rectangles with RMB to only mark point.")
	print ("Click i.e. draw very tiny rectangle to mark point directly.")
	print ("Press Space to start morphing, ESC to quit")

	img1Copy = np.copy(img1)
	img2Copy = np.copy(img2)

	#create sac instance with two images	
	sacInstance = sac.sac(img1, img2)	

	cv2.namedWindow("Image 1", cv2.WINDOW_KEEPRATIO)
	cv2.setMouseCallback("Image 1", onMouse, True)
	cv2.namedWindow("Image 2", cv2.WINDOW_KEEPRATIO)
	cv2.setMouseCallback("Image 2", onMouse, False)
	cv2.imshow("Image 1", img1)
	cv2.imshow("Image 2", img2)
	cv2.resizeWindow("Image 1", 640, 1024)
	cv2.resizeWindow("Image 2", 640, 1024)

	key = 0
	while key != 32:
		key = cv2.waitKey(0)
		if key == 27:
			cv2.destroyAllWindows() 
			exit()
	cv2.destroyAllWindows() 

	#morph images
	print ("Morphing...")
	alpha = 0.5
	steps = 3 
	images = delaunayMorphing.morph(img1Copy, img2Copy, pointsImg1, pointsImg2, alpha, steps)
	cv2.namedWindow("Image 1 morphed", cv2.WINDOW_KEEPRATIO)
	cv2.namedWindow("Image 2 morphed", cv2.WINDOW_KEEPRATIO)
	cv2.namedWindow("Images blended", cv2.WINDOW_KEEPRATIO)
	cv2.imshow("Image 1 morphed", images[0])
	cv2.imshow("Image 2 morphed", images[2])
	cv2.imshow("Images blended", images[1])
	cv2.resizeWindow("Image 1 morphed", 640, 1024)
	cv2.resizeWindow("Image 2 morphed", 640, 1024)
	cv2.resizeWindow("Images blended", 640, 1024)
	while cv2.waitKey(0) != 27:
		pass
	cv2.destroyAllWindows() 
	

if __name__ == "__main__":
    sys.exit(test())
