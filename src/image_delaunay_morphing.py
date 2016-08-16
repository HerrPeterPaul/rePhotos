import numpy as np
import cv2


def apply_affine_transform(src, src_tri, dst_tri, size):
    """
    Apply affine transform calculated using src_tri and dst_tri to src and output an image of size.
    """
    # Given a pair of triangles, find the affine transform.
    warp_mat = cv2.getAffineTransform(np.float32(src_tri), np.float32(dst_tri))

    # Apply the Affine Transform just found to the src image
    dst = cv2.warpAffine(src, warp_mat, (size[0], size[1]), None, flags=cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_REFLECT_101)
    return dst

def scale(img1, img2, points_img1, points_img2):
    """
    Prescales images and points to allow delaunay morphing of images of different sizes.
    Upsacles the smaller image
    """
    y_size_img1, x_size_img1, z_size_img1 = img1.shape
    y_size_img2, x_size_img2, z_size_img2 = img2.shape
    x_scale_factor = float(x_size_img1)/ float(x_size_img2)
    y_scale_factor = float(y_size_img1)/ float(y_size_img2)

    # images are of same size
    if x_size_img1 == x_size_img2 and y_size_img1 == y_size_img2:
        return img1, img2, points_img1, points_img2

    # image 1 is bigger
    elif x_size_img1 >= x_size_img2 and y_size_img1 >= y_size_img2:
        temp_img = np.zeros(img1.shape, dtype=img1.dtype)
        temp_points = []
        # x scale is smaller
        if x_scale_factor < y_scale_factor:
            img2 = cv2.resize(img2,  (0,0), fx=x_scale_factor, fy=x_scale_factor, interpolation=cv2.INTER_CUBIC)
            for point in points_img2:
                x = point[0] * x_scale_factor
                y = point[1] * x_scale_factor
                temp_points.append((x,y))
        # y scale is smaller
        else:
            img2 = cv2.resize(img2, (0,0), fx=y_scale_factor, fy=y_scale_factor, interpolation=cv2.INTER_CUBIC)
            for point in points_img2:
                x = point[0] * y_scale_factor
                y = point[1] * y_scale_factor
                temp_points.append((x,y))
        temp_img[0:img2.shape[0], 0:img2.shape[1], 0:img2.shape[2]] = img2
        points_img2 = temp_points
        img2 = temp_img

    #image 1 is smaller
    elif x_size_img1 <= x_size_img2 and y_size_img1 <= y_size_img2:
        temp_img = np.zeros(img2.shape, dtype=img2.dtype)
        temp_points = []
        # x scale is smaller. we need the inverse
        if x_scale_factor > y_scale_factor:
            img1 = cv2.resize(img1, (0,0), fx=(1/x_scale_factor), fy=(1/x_scale_factor), interpolation=cv2.INTER_CUBIC)
            for point in points_img1:
                x = point[0] * 1/x_scale_factor
                y = point[1] * 1/x_scale_factor
                temp_points.append((x,y))
        # y scale is smaller
        else:
            img1 = cv2.resize(img1, (0,0), fx=1/y_scale_factor, fy=1/y_scale_factor, interpolation=cv2.INTER_CUBIC)
            for point in points_img1:
                x = point[0] * 1/y_scale_factor
                y = point[1] * 1/y_scale_factor
                temp_points.append((x,y))
        temp_img[0:img1.shape[0], 0:img1.shape[1], 0:img1.shape[2]] = img1
        points_img1 = temp_points
        img1 = temp_img

    # images size relations are not the same i.e. x_scale < 0 and y_scale > 0 or vice versa
    else:
        temp_img = np.zeros(max(y_size_img1, y_size_img2), max(x_size_img1, x_size_img2), max(z_size_img1, z_size_img2), dtype=img1.dtype)
        temp_img2 = np.copy(temp_img)
        temp_img[0:img1.shape[0], 0:img1.shape[1], 0:img1.shape[2]] = img1
        img1 = temp_img
        temp_img[0:img2.shape[0], 0:img2.shape[1], 0:img2.shape[2]] = img2
        img2 = temp_img2

    return img1, img2, points_img1, points_img2


def morph_triangle(img1, img2, img, t1, t2, t, alpha):
    """
    Warps and alpha blends triangular regions from img1 and img2 to img.
    """
    # Find bounding rectangle for each triangle
    r1 = cv2.boundingRect(np.float32([t1]))
    r2 = cv2.boundingRect(np.float32([t2]))
    r = cv2.boundingRect(np.float32([t]))

    # Offset points by left top corner of the respective rectangles
    t1_rect = []
    t2_rect = []
    t_rect = []

    for i in range(0, 3):
        t_rect.append(((t[i][0] - r[0]), (t[i][1] - r[1])))
        t1_rect.append(((t1[i][0] - r1[0]), (t1[i][1] - r1[1])))
        t2_rect.append(((t2[i][0] - r2[0]), (t2[i][1] - r2[1])))

    # Get mask by filling triangle
    mask = np.zeros((r[3], r[2], 3), dtype=np.float32)
    cv2.fillConvexPoly(mask, np.int32(t_rect), (1.0, 1.0, 1.0), 16, 0)

    # Apply warpImage to small rectangular patches
    img1_rect = img1[r1[1]:r1[1] + r1[3], r1[0]:r1[0] + r1[2]]
    img2_rect = img2[r2[1]:r2[1] + r2[3], r2[0]:r2[0] + r2[2]]

    size = (r[2], r[3])
    warp_image1 = apply_affine_transform(img1_rect, t1_rect, t_rect, size)
    warp_image2 = apply_affine_transform(img2_rect, t2_rect, t_rect, size)

    # Alpha blend rectangular patches
    img_rect = (1.0 - alpha) * warp_image1 + alpha * warp_image2

    # Copy triangular region of the rectangular patch to the output image
    img[r[1]:r[1] + r[3], r[0]:r[0] + r[2]] = img[r[1]:r[1] + r[3], r[0]:r[0] + r[2]] * (1 - mask) + img_rect * mask


def get_indices(rect, points):
    """
    Returns indices of delaunay triangles.
    """
    subdiv = cv2.Subdiv2D(rect)
    for p in points:
        subdiv.insert(p)
    triangle_list = subdiv.getTriangleList()

    indices_tri = []
    ind = [None] * 3
    pt = [None] * 3
    for triangle in triangle_list:
        pt[0] = (int(triangle[0])), int(triangle[1])
        pt[1] = (int(triangle[2])), int(triangle[3])
        pt[2] = (int(triangle[4])), int(triangle[5])
        if rect[0] <= (pt[0])[0] <= rect[2] and rect[1] <= (pt[0])[1] <= rect[3] and rect[0] <= (pt[1])[0] <= rect[2] \
                and rect[1] <= (pt[1])[1] <= rect[3] and rect[0] <= (pt[2])[0] <= rect[2] and rect[1] <= (pt[2])[1] <= rect[3]:
            for i in range(0, 3):
                for j in range(0, len(points)):
                    if pt[i][0] == points[j][0] and pt[i][1] == points[j][1]:
                        ind[i] = j
            indices_tri.append(list(ind))
    return indices_tri


def get_corners(img, img2, points_img1, points_img2, alpha):
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
    alpha_2 = (1 - alpha) * 2

    # left middle
    p_min_mean, i_min_mean = min(((val, idx) for (idx, val) in enumerate(points_img1)),
                                 key=lambda p: (p[0])[0] + abs(y_mean - (p[0])[1]))
    delta_y_half = int((p_min_mean[1] - (points_img2[i_min_mean])[1]) / 2)
    delta_x_half = int((p_min_mean[0] - (points_img2[i_min_mean])[0]) / 2)
    points_img1.append((0 + abs(delta_x_half) + delta_x_half, p_min_mean[1] + delta_y_half))
    points_img2.append((0 + abs(delta_x_half) - delta_x_half, p_min_mean[1] - delta_y_half))
    global_x_min = 0 + abs(delta_x_half) * alpha_2 

    # right middle
    p_max_mean, i_max_mean = min(((val, idx) for (idx, val) in enumerate(points_img1)),
                                 key=lambda p: (x_max - (p[0])[0]) + abs(y_mean - (p[0])[1]))
    delta_y_half = int((p_max_mean[1] - (points_img2[i_max_mean])[1]) / 2)
    delta_x_half = int((p_max_mean[0] - (points_img2[i_max_mean])[0]) / 2)
    points_img1.append((x_max - abs(delta_x_half) + delta_x_half, p_max_mean[1] + delta_y_half))
    points_img2.append((x_max - abs(delta_y_half) - delta_x_half, p_max_mean[1] - delta_y_half))
    global_x_max = x_max - abs(delta_x_half) * alpha_2

    # top middle
    p_mean_min, i_mean_min = min(((val, idx) for (idx, val) in enumerate(points_img1)),
                                 key=lambda p: abs(x_mean - (p[0])[0]) + (p[0])[1])
    delta_x_half = int((p_mean_min[0] - (points_img2[i_mean_min])[0]) / 2)
    delta_y_half = int((p_mean_min[1] - (points_img2[i_mean_min])[1]) / 2)
    points_img1.append((p_mean_min[0] + delta_x_half, 0 + abs(delta_y_half) + delta_y_half))
    points_img2.append((p_mean_min[0] - delta_x_half, 0 + abs(delta_y_half) - delta_y_half))
    global_y_min = abs(delta_y_half) * alpha_2

    # bottom middle
    p_mean_max, i_mean_max = min(((val, idx) for (idx, val) in enumerate(points_img1)),
                                 key=lambda p: abs(x_mean - (p[0])[0]) + (y_max - (p[0])[1]))
    delta_x_half = int((p_mean_max[0] - (points_img2[i_mean_max])[0]) / 2)
    delta_y_half = int((p_mean_max[1] - (points_img2[i_mean_max])[1]) / 2)
    points_img1.append((p_mean_max[0] + delta_x_half, y_max - abs(delta_y_half) + delta_y_half))
    points_img2.append((p_mean_max[0] - delta_x_half, y_max - abs(delta_y_half) - delta_y_half))
    global_y_max = y_max - abs(delta_y_half) * alpha_2

    # bottom left
    p_min_max, i_min_max = max(((val, idx) for (idx, val) in enumerate(points_img1)), key=lambda p: (x_max - (p[0])[0]) + (p[0])[1])
    delta_y_half = int((p_min_max[1] - (points_img2[i_min_max])[1]) / 2)
    delta_x_half = int((p_min_max[0] - (points_img2[i_min_max])[0]) / 2)
    corners_img1.append((0 + abs(delta_x_half) + delta_x_half, y_max - abs(delta_y_half) + delta_y_half))
    corners_img2.append((0 + abs(delta_x_half) - delta_x_half, y_max - abs(delta_y_half) - delta_y_half))
    global_x_min = abs(delta_x_half) * alpha_2 if abs(delta_x_half) * alpha_2 > global_x_min else global_x_min
    global_y_max = y_max - abs(delta_y_half) * alpha_2 if (y_max - abs(delta_y_half)) * alpha_2 < global_y_max else global_y_max

    # bottom right
    p_max_max, i_max_max = max(((val, idx) for (idx, val) in enumerate(points_img1)), key=lambda p: (p[0])[0] + (p[0])[1])
    delta_y_half = int((p_max_max[1] - (points_img2[i_max_max])[1]) / 2)
    delta_x_half = int((p_max_max[0] - (points_img2[i_max_max])[0]) / 2)
    corners_img1.append((x_max - abs(delta_x_half) + delta_x_half, y_max - abs(delta_y_half) + delta_y_half))
    corners_img2.append((x_max - abs(delta_x_half) - delta_x_half, y_max - abs(delta_y_half) - delta_y_half))
    global_x_max = x_max - abs(delta_x_half) * alpha_2 if (x_max - abs(delta_x_half) * alpha_2) < global_x_max else global_x_max
    global_y_max = y_max - abs(delta_y_half) * alpha_2 if (y_max - abs(delta_y_half) * alpha_2) < global_y_max else global_y_max

    # top right
    p_max_min, i_max_min = max(((val, idx) for (idx, val) in enumerate(points_img1)), key=lambda p: (p[0])[0] + (y_max - (p[0])[1]))
    delta_y_half = int((p_max_min[1] - (points_img2[i_max_min])[1]) / 2)
    delta_x_half = int((p_max_min[0] - (points_img2[i_max_min])[0]) / 2)
    corners_img1.append((x_max - abs(delta_x_half) + delta_x_half, 0 + abs(delta_y_half) + delta_y_half))
    corners_img2.append((x_max - abs(delta_x_half) - delta_x_half, 0 + abs(delta_y_half) - delta_y_half))
    global_x_max = x_max - abs(delta_x_half) * alpha_2 if (x_max - abs(delta_x_half) * alpha_2) < global_x_max else global_x_max
    global_y_min = abs(delta_y_half) * alpha_2 if abs(delta_y_half) * alpha_2 > global_y_min else global_y_min

    # top left
    p_min_min, i_min_min = min(((val, idx) for (idx, val) in enumerate(points_img1)), key=lambda p: (p[0])[0] + (p[0])[1])
    delta_y_half = int((p_min_min[1] - (points_img2[i_min_min])[1]) / 2)
    delta_x_half = int((p_min_min[0] - (points_img2[i_min_min])[0]) / 2)
    corners_img1.append((0 + abs(delta_x_half) + delta_x_half, 0 + abs(delta_y_half) + delta_y_half))
    corners_img2.append((0 + abs(delta_x_half) - delta_x_half, 0 + abs(delta_y_half) - delta_y_half))
    global_x_min = abs(delta_x_half) * alpha_2 if abs(delta_x_half) * alpha_2 > global_x_min else global_x_min
    global_y_min = abs(delta_y_half) * alpha_2 if abs(delta_y_half) * alpha_2 > global_y_min else global_y_min

    points_img1 += corners_img1
    points_img2 += corners_img2
    return global_x_min, global_x_max, global_y_min, global_y_max


def morph(img1, img2, points_img1, points_img2, alpha=0.5, steps=2):
    """Returns list of morphed images."""

    assert 0 <= alpha <= 1, "Alpha not between 0 and 1."
    assert len(points_img1) == len(points_img2), "Point lists have different size."

    # Convert Mat to float data type
    img1 = np.float32(img1)
    img2 = np.float32(img2)
    
    img1, img2, points_img1, points_img2 = scale(img1, img2, points_img1, points_img2)

    # Add the corner points and middle point of edges to the point lists
    global_x_min, global_x_max, global_y_min, global_y_max = get_corners(img1, img2, points_img1, points_img2, alpha)

    # Compute weighted average point coordinates
    points = []
    for i in range(0, len(points_img1)):
        x = int((1 - alpha) * points_img1[i][0] + alpha * points_img2[i][0])
        y = int((1 - alpha) * points_img1[i][1] + alpha * points_img2[i][1])
        points.append((x, y))
    
    rect = (0, 0, max(img1.shape[1], img2.shape[1]), max(img1.shape[0], img2.shape[0]))
    indices_tri = get_indices(rect, points)

    images = []
    for a in np.linspace(0.0, 1.0, num=steps):
        # Allocate space for final output
        img_morph = np.zeros((max(img1.shape[0], img2.shape[0]), max(img1.shape[1], img2.shape[1]), max(img1.shape[2], img2.shape[2])), dtype=img1.dtype)

        for ind in indices_tri:
            x = ind[0]
            y = ind[1]
            z = ind[2]

            t1 = [points_img1[x], points_img1[y], points_img1[z]]
            t2 = [points_img2[x], points_img2[y], points_img2[z]]
            t = [points[x], points[y], points[z]]

            # Morph one triangle at a time.
            morph_triangle(img1, img2, img_morph, t1, t2, t, a)
        # add cropped images to list
        images.append(np.copy(np.uint8(img_morph[int(global_y_min):int(global_y_max), int(global_x_min):int(global_x_max), :])))
    return images