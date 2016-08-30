import numpy as np
import cv2


def get_crop_indices(img):
    """
    Get crop indices to crop black border from image.
    Crops non linear borders.
    Starts with small rectangle in middle, grows till black pixels are reached
    at each site.
    """        
    
    x_min= int(img.shape[1] / 2) - 1
    y_min= int(img.shape[0] / 2) - 1
    x_max= int(img.shape[1] / 2) + 1
    y_max= int(img.shape[0] / 2) + 1
    
    x_step_size = int((img.shape[1]/100) * 2)
    y_step_size = int((img.shape[0]/100) * 2) 

    top_done = False
    left_done = False
    bottom_done = False
    right_done = False

    while not top_done or not right_done or not bottom_done or not left_done:
        # check left  
        if not left_done and x_min - x_step_size > -1: 
            for y in range(y_min, y_max):
                value = img[y, x_min - x_step_size, :]
                if sum(value) == 0:
                    left_done = True   
                    break
            if y == y_max -1 :
                left_done = False
                x_min -= x_step_size
        else:
            left_done = True

        # check bottom
        if not bottom_done and y_max + y_step_size < img.shape[0] :
            for x in range(x_min, x_max):
                value = img[y_max + y_step_size, x, :]
                if sum(value) ==  0:
                    bottom_done = True 
                    break
            if x == x_max - 1:
                bottom_done = False 
                y_max += y_step_size
        else:
            bottom_done = True

        # check right
        if not right_done and x_max + x_step_size < img.shape[1] :
            for y in range(y_min, y_max):
                value = img[y, x_max + x_step_size, :]
                if sum(value) == 0:
                    right_done = True
                    break
            if y == y_max - 1:
                right_done = False
                x_max += x_step_size
        else:
            right_done = True

        # check top  
        if not top_done and y_min - y_step_size > -1:
            for x in range(x_min, x_max):
                value = img[y_min - y_step_size, x , :]
                if sum(value) == 0:
                    top_done = True
                    break
            if x == x_max - 1:
                top_done = False
                y_min -= y_step_size
        else:
            top_done = True

    return x_min, x_max, y_min, y_max


def weighted_average_point(point1, point2, alpha):
    """
    Return the average point between two points weighted by alpha.
    """
    x = int((1 - alpha) * point1[0] + alpha * point2[0])
    y = int((1 - alpha) * point1[1] + alpha * point2[1])
    return (x,y)


def get_corners(img, img2, points_img1, points_img2):
    """Adds the corners and middle point of edges to pointlists.
    Finds the user selectet points which are nearest to the four corners and the
    four middle points of the edges of the image. Computes the delta between
    them and their coresponding points. Adds corner points and middle points of
    edges to the point lists and offsets them using the computet delta values.
    Returns the global max and minima used for cropping
    """

    x_max = min(img.shape[1], img2.shape[1]) - 1
    y_max = min(img.shape[0], img2.shape[0]) - 1
    x_mean = int(x_max / 2)
    y_mean = int(y_max / 2)
    corners_img1 = []
    corners_img2 = []

    '''
    # left middle
    p_min_mean, i_min_mean = min(((val, idx) for (idx, val) in enumerate(points_img1)),
                                key=lambda p: (p[0])[0] + abs(y_mean - (p[0])[1]))
    delta_y_half = int((p_min_mean[1] - (points_img2[i_min_mean])[1]) / 2)
    delta_x_half = int((p_min_mean[0] - (points_img2[i_min_mean])[0]) / 2)
    corners_img1.append((0 + abs(delta_x_half) + delta_x_half, p_min_mean[1] + delta_y_half))
    corners_img2.append((0 + abs(delta_x_half) - delta_x_half, p_min_mean[1] - delta_y_half))

    # right middle
    p_max_mean, i_max_mean = min(((val, idx) for (idx, val) in enumerate(points_img1)),
                                key=lambda p: (x_max - (p[0])[0]) + abs(y_mean - (p[0])[1]))
    delta_y_half = int((p_max_mean[1] - (points_img2[i_max_mean])[1]) / 2)
    delta_x_half = int((p_max_mean[0] - (points_img2[i_max_mean])[0]) / 2)
    corners_img1.append((x_max - abs(delta_x_half) + delta_x_half, p_max_mean[1] + delta_y_half))
    corners_img2.append((x_max - abs(delta_x_half) - delta_x_half, p_max_mean[1] - delta_y_half))

    # top middle
    p_mean_min, i_mean_min = min(((val, idx) for (idx, val) in enumerate(points_img1)),
                                key=lambda p: abs(x_mean - (p[0])[0]) + (p[0])[1])
    delta_x_half = int((p_mean_min[0] - (points_img2[i_mean_min])[0]) / 2)
    delta_y_half = int((p_mean_min[1] - (points_img2[i_mean_min])[1]) / 2)
    corners_img1.append((p_mean_min[0] + delta_x_half, 0 + abs(delta_y_half) + delta_y_half))
    corners_img2.append((p_mean_min[0] - delta_x_half, 0 + abs(delta_y_half) - delta_y_half))

    # bottom middle
    p_mean_max, i_mean_max = min(((val, idx) for (idx, val) in enumerate(points_img1)),
                                key=lambda p: abs(x_mean - (p[0])[0]) + (y_max - (p[0])[1]))
    delta_x_half = int((p_mean_max[0] - (points_img2[i_mean_max])[0]) / 2)
    delta_y_half = int((p_mean_max[1] - (points_img2[i_mean_max])[1]) / 2)
    corners_img1.append((p_mean_max[0] + delta_x_half, y_max - abs(delta_y_half) + delta_y_half))
    corners_img2.append((p_mean_max[0] - delta_x_half, y_max - abs(delta_y_half) - delta_y_half))
    '''
    # bottom left
    p_min_max, i_min_max = max(((val, idx) for (idx, val) in enumerate(points_img1)), 
                                key=lambda p: (x_max - (p[0])[0]) + (p[0])[1])
    delta_y_half = int((p_min_max[1] - (points_img2[i_min_max])[1]) / 2)
    delta_x_half = int((p_min_max[0] - (points_img2[i_min_max])[0]) / 2)
    corners_img1.append((0 + abs(delta_x_half) + delta_x_half, y_max - abs(delta_y_half) + delta_y_half))
    corners_img2.append((0 + abs(delta_x_half) - delta_x_half, y_max - abs(delta_y_half) - delta_y_half))

    # bottom right
    p_max_max, i_max_max = max(((val, idx) for (idx, val) in enumerate(points_img1)), 
                                key=lambda p: (p[0])[0] + (p[0])[1])
    delta_y_half = int((p_max_max[1] - (points_img2[i_max_max])[1]) / 2)
    delta_x_half = int((p_max_max[0] - (points_img2[i_max_max])[0]) / 2)
    corners_img1.append((x_max - abs(delta_x_half) + delta_x_half, y_max - abs(delta_y_half) + delta_y_half))
    corners_img2.append((x_max - abs(delta_x_half) - delta_x_half, y_max - abs(delta_y_half) - delta_y_half))

    # top right
    p_max_min, i_max_min = max(((val, idx) for (idx, val) in enumerate(points_img1)), 
                                key=lambda p: (p[0])[0] + (y_max - (p[0])[1]))
    delta_y_half = int((p_max_min[1] - (points_img2[i_max_min])[1]) / 2)
    delta_x_half = int((p_max_min[0] - (points_img2[i_max_min])[0]) / 2)
    corners_img1.append((x_max - abs(delta_x_half) + delta_x_half, 0 + abs(delta_y_half) + delta_y_half))
    corners_img2.append((x_max - abs(delta_x_half) - delta_x_half, 0 + abs(delta_y_half) - delta_y_half))

    # top left
    p_min_min, i_min_min = min(((val, idx) for (idx, val) in enumerate(points_img1)), 
                                key=lambda p: (p[0])[0] + (p[0])[1])
    delta_y_half = int((p_min_min[1] - (points_img2[i_min_min])[1]) / 2)
    delta_x_half = int((p_min_min[0] - (points_img2[i_min_min])[0]) / 2)
    corners_img1.append((0 + abs(delta_x_half) + delta_x_half, 0 + abs(delta_y_half) + delta_y_half))
    corners_img2.append((0 + abs(delta_x_half) - delta_x_half, 0 + abs(delta_y_half) - delta_y_half))

    points_img1 += corners_img1
    points_img2 += corners_img2
    return 


def scale(img1, img2, points_img1, points_img2):
    """
    Prescales images and points to allow delaunay morphing of images of different sizes.
    Upsacles the smaller image
    """
    y_size_img1, x_size_img1, z_size_img1 = img1.shape
    y_size_img2, x_size_img2, z_size_img2 = img2.shape
    x_scale_factor = float(x_size_img1)/ float(x_size_img2)
    y_scale_factor = float(y_size_img1)/ float(y_size_img2)

    # Images are of same size
    if x_size_img1 == x_size_img2 and y_size_img1 == y_size_img2:
        return img1, img2, points_img1, points_img2

    # Image 1 is bigger
    elif x_size_img1 >= x_size_img2 and y_size_img1 >= y_size_img2:
        temp_img = np.zeros(img1.shape, dtype=img1.dtype)
        temp_points = []
        # X scale is smaller
        if x_scale_factor < y_scale_factor:
            img2 = cv2.resize(img2,  (0,0), fx=x_scale_factor, fy=x_scale_factor, interpolation=cv2.INTER_LINEAR)
            for point in points_img2:
                x = point[0] * x_scale_factor
                y = point[1] * x_scale_factor
                temp_points.append((x,y))
        # Y scale is smaller
        else:
            img2 = cv2.resize(img2, (0,0), fx=y_scale_factor, fy=y_scale_factor, interpolation=cv2.INTER_LINEAR)
            for point in points_img2:
                x = point[0] * y_scale_factor
                y = point[1] * y_scale_factor
                temp_points.append((x,y))
        temp_img[0:img2.shape[0], 0:img2.shape[1], 0:img2.shape[2]] = img2
        points_img2 = temp_points
        img2 = temp_img

    # Image 1 is smaller
    elif x_size_img1 <= x_size_img2 and y_size_img1 <= y_size_img2:
        temp_img = np.zeros(img2.shape, dtype=img2.dtype)
        temp_points = []
        # X scale is smaller. we need the inverse
        if x_scale_factor > y_scale_factor:
            img1 = cv2.resize(img1, (0,0), fx=(1/x_scale_factor), fy=(1/x_scale_factor), interpolation=cv2.INTER_LINEAR)
            for point in points_img1:
                x = point[0] * 1/x_scale_factor
                y = point[1] * 1/x_scale_factor
                temp_points.append((x,y))
        # Y scale is smaller
        else:
            img1 = cv2.resize(img1, (0,0), fx=1/y_scale_factor, fy=1/y_scale_factor, interpolation=cv2.INTER_LINEAR)
            for point in points_img1:
                x = point[0] * 1/y_scale_factor
                y = point[1] * 1/y_scale_factor
                temp_points.append((x,y))
        temp_img[0:img1.shape[0], 0:img1.shape[1], 0:img1.shape[2]] = img1
        points_img1 = temp_points
        img1 = temp_img

    # Images size relations are not the same i.e. x_scale < 1 and y_scale > 1 or vice versa
    else:
        temp_img = np.zeros((max(y_size_img1, y_size_img2), max(x_size_img1, x_size_img2), max(z_size_img1, z_size_img2)), dtype=img1.dtype)
        temp_img2 = np.copy(temp_img)
        temp_img[0:img1.shape[0], 0:img1.shape[1], 0:img1.shape[2]] = img1
        img1 = temp_img
        temp_img2[0:img2.shape[0], 0:img2.shape[1], 0:img2.shape[2]] = img2
        img2 = temp_img2

    return img1, img2, points_img1, points_img2

