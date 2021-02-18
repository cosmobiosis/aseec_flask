import cv2
import numpy as np
import base64

def processSingleImage(eye_tracker, image_encoded_data):
    img_data = base64.b64decode(image_encoded_data)
    npimg = np.frombuffer(img_data, dtype=np.uint8)
    frame = cv2.imdecode(npimg, cv2.IMREAD_UNCHANGED)

    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # PUPIL!!!
    (coords, bw_img) = eye_tracker.run(frame_gray)
    _, contours, _ = cv2.findContours(bw_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours_poly = [None] * len(contours)
    boundRect = [None] * len(contours)
    centers = [[]] * len(contours)
    pupilRadiuses = [0] * len(contours)

    for i, c in enumerate(contours):
        contours_poly[i] = cv2.approxPolyDP(c, 3, True)
        boundRect[i] = cv2.boundingRect(contours_poly[i])
        centers[i], pupilRadiuses[i] = cv2.minEnclosingCircle(contours_poly[i])

    pupilX = pupilY = pupilR = float('-inf')
    for i in range(len(contours)):
        if 2 * pupilRadiuses[i] > bw_img.shape[1] / 2:
            # filter big diameter
            continue
        if pupilRadiuses[i] > pupilR:
            pupilX = int(centers[i][0])
            pupilY = int(centers[i][1])
            pupilR = int(pupilRadiuses[i])
    pupilX = -1 if pupilX == float('-inf') else pupilX
    pupilY = -1 if pupilY == float('-inf') else pupilY
    pupilR = -1 if pupilR == float('-inf') else pupilR

    # IRIS!!!!!
    irisCannyThreshold = 60
    irisAccumulatorThreshold = 40
    irisRadMin = 3 * int(frame_gray.shape[1] / 40)
    irisRadMax = 10 * int(frame_gray.shape[1] / 40)
    irisCircles = cv2.HoughCircles(cv2.cvtColor(cv2.medianBlur(frame,5), cv2.COLOR_BGR2GRAY), cv2.HOUGH_GRADIENT, 1, 1,
                               param1=irisCannyThreshold, param2=irisAccumulatorThreshold, minRadius=irisRadMin, maxRadius=irisRadMax)
    irisCircles = np.uint16(np.around(irisCircles))

    irisX = irisY = irisR = -1
    for candidate in irisCircles[0, :]:
        tempIrisX, tempIrisY, tempIrisR = candidate[0], candidate[1],candidate[2]
        curDist = np.sqrt(np.sum(np.square(np.array([tempIrisX, tempIrisY]) - np.array([pupilX, pupilY]))))
        if curDist + pupilR >= tempIrisR:
            # wrong location for iris
            continue
        irisX, irisY, irisR = tempIrisX, tempIrisY, tempIrisR
        break

    height = frame_gray.shape[0]
    width = frame_gray.shape[1]
    return {
        "pupilIrisRatio" : float(pupilR) / float(irisR),
        "imgRatio": height / width,
        "pupil": {
            "r" : float(pupilR) / float(width),
            "x" : float(pupilX) / float(width),
            "y": float(pupilY) / float(height),
        },
        "iris": {
            "r": float(irisR) / float(width),
            "x": float(irisX) / float(width),
            "y": float(irisY) / float(height),
        }
    }
