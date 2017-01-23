import numpy as np
import cv2
from image_helpers import statistic_canny
from image_helpers import adaptive_thresh
from image_helpers import line_intersect 
from image_helpers import lce
from image_helpers import draw_line

# Patch Size Divisor: Area arround line in which similar line is searched
psd = 70

def lim_line_length(p1_h, p2_h, p1_o, p2_o):
    """
    Limits length of line h to linesegment o.
    Computes a line segment of line h found by hough transform to the
    length of user drawn line segment o by computing the normals at start
    and end point of user drawn line segment and their intersection with
    hough line.
    
    Args:
        p1_h: First point on hough line.
        p2_h: Second point on hough line.
        p1_o: Startpoint of user drawn line segment.
        p2_o: Endpoint of user drawn line segment.

    Returns:
        z1: Startpoint of line segment of hough line.
        z2: Endpoint of line segment of hough line.
    """
    p1_o = np.array(p1_o, dtype=np.float32)
    p2_o = np.array(p2_o, dtype=np.float32)
    p1_h = np.array(p1_h, dtype=np.float32)
    p2_h = np.array(p2_h, dtype=np.float32)
    # Compute end points of orthagonal lines
    b1_o = p1_o + np.array([-(p1_o[1] - p2_o[1]), (p1_o[0] - p2_o[0])])
    b2_o = p2_o + np.array([-(p2_o[1] - p1_o[1]), (p2_o[0] - p1_o[0])])
    z1 = line_intersect(p1_o, b1_o, p1_h, p2_h)
    z2 = line_intersect(p2_o, b2_o, p2_h, p1_h)
    z1 = (np.rint(z1)).astype(int)
    z2 = (np.rint(z2)).astype(int)
    return z1, z2


def get_theta(p1, p2):
    """
    Computes gradient angle of line.

    Args:
        p1_o: First point of line.
        p2_o: Second point of line.

    Returns:
        theta: Gradient angle.
    """
    if p2[0] - p1[0] == 0:
        return 0
    else:
        m = (float(p2[1] - p1[1]) / float(p2[0] - p1[0]))
        return np.arctan(m) + np.pi/2


def weight_lines(patch_p, lines, p1_o, p2_o):
    """
    Weights hough lines by similarity to edges.
    Generates line segments with length according to user drawn lines and 
    compares segments with edges in edge image. Select best matching line.
    Only lines with similar orientation to user drawn line are regarded.
    Only best ten lines fullfilling above criterium are considered.

    Args:
        patch_p: Edgeimage.
        lines: List of lines.
        p1_o: Startpoint of user drawn line.
        p2_o: Endpoint of user drawn line.

    Returns:
        p1: Startpoint of best matching line.
        p2: Endpoint of best matching line.
    """
    #iterate over max ten best lines
    nl = min(10, lines.shape[0])
    line_img = np.empty(patch_p.shape, dtype=np.uint8)
    weights = np.empty((nl), dtype=np.float32)
    line_segs = np.empty((nl), dtype=object)
    i, j = 0, 0
    theta_o = get_theta(p1_o, p2_o)    

    while  j < lines.shape[0] and i < 10 :
        rho = lines[j][0][0]
        theta = lines[j][0][1]
        j += 1
        # allow only lines with roughly the same slope as user drawn lines
        if np.abs(theta_o - theta) < .05 or \
            np.pi - np.abs(theta_o - theta) < 0.05:
            line_img[:] = 0
            a = np.cos(theta)
            b = np.sin(theta)
            x0, y0 = a * rho, b * rho
            pt1 = (int(x0 + 1000 * (-b)), int(y0 + 1000 * a))
            pt2 = (int(x0 - 1000 * (-b)), int(y0 - 1000 * a))
            pt1, pt2 = lim_line_length(pt1, pt2, p1_o, p2_o)
            cv2.line(line_img, (pt1[0], pt1[1]), (pt2[0], pt2[1]), 255, 1, 4)
            weights[i] = np.einsum('ij,ij->', line_img, patch_p, dtype=np.float32)
            line_segs[i] = (pt1, pt2)
            i += 1

    if i > 0:
        k = weights[:i].argmax()
        p1 = line_segs[k][0] 
        p2 = line_segs[k][1] 
        w = weights[k]
    else:
        p1 = p1_o
        p2 = p2_o
        w = 0

    return p1, p2, w


def get_line(p1, p2, img):
    """
    Search in image for neares most similar line of a given line.
    Search in H, S, and V for line in area arround given line. Select line
    with similiar rotation and many supporting edge pixel.

    Args:
        p1: Start point of user drawn line.
        p2: End point of user drawn line.
        img: Image in which neares line in searched.

    Returns:
        [p1,p2]: List of two points of computed most similar line
    """

    # Get length and slope of line
    length = np.sqrt((p1[1] - p2[1]) * (p1[1] - p2[1]) + (p1[0] - p2[0]) * 
        (p1[0] - p2[0])) 
    v = np.array([(p2[1] - p1[1])/length, (p2[0] - p1[0])/length])

    # Compute rectangle with line in the middle and same rotation as line
    # and bounding box arround it
    s = (img.shape[0] + img.shape[1])/ (2 * psd)
    m1 = p1 + s * (v * [ 1, -1] - v[::-1]) 
    m2 = p1 + s * (v * [ -1, 1] - v[::-1]) 
    m3 = p2 + s * (v * [ -1, 1] + v[::-1])
    m4 = p2 + s * (v * [ 1, -1] + v[::-1])
    p = np.array([m1, m2, m3, m4], dtype=np.uint32)
    x_min = int(max(0, p.T[1,:].min()))
    x_max = int(min(img.shape[0], p.T[1,:].max()))
    y_min = int(max(0, p.T[0,:].min()))
    y_max = int(min(img.shape[1], p.T[0,:].max()))

    patch = np.uint8(img[x_min: x_max, y_min: y_max])

    # Generate mask of patch size
    mask = np.zeros((img.shape[0], img.shape[1]), dtype=patch.dtype)
    cv2.fillPoly(mask, [p.astype(int)], (1))
    mask = mask[x_min: x_max, y_min: y_max]

    # Offset points
    offset = np.array([y_min, x_min])
    p1_o = p1 - offset
    p2_o = p2 - offset

    patch = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
    patch = cv2.GaussianBlur(patch, (5,5), 0)

    best_lines = []
    sigma = 0.33
    magic_n = 100
    for i in range(0,3):
        ch = cv2.equalizeHist(patch[:,:,i])

        # Edge dedection
        m = np.median(ch)
        lower_bound = int(max(0, (1.0 - sigma) * m)) + magic_n
        upper_bound = int(min(255, (1.0 + sigma) * m)) + magic_n
        ch = cv2.Canny(ch, lower_bound, upper_bound, L2gradient=True)

        # Filter patch_p to only contain the patch area not the containing rectangle
        ch *= mask
        
        # Line detection
        lines = cv2.HoughLines(ch, 1, np.pi/180.0, 1, np.array([]), 0, 0)

        if lines is not None:
            best_lines.append(weight_lines(ch, lines, p1_o, p2_o))
    
    if len(best_lines) != 0:
        k = max(enumerate(best_lines), key=lambda x: x[1][2])[0]
        p1 = best_lines[k][0] + offset
        p2 = best_lines[k][1] + offset
    
    return [p1[0], p1[1], p2[0], p2[1]]
