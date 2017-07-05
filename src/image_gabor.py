#!/usr/bin/env python
"""Adapation of gabor_threads.py from openCV/samples/python/
Filters an image with a set of gabor filters. 
"""
# Python 2/3 compatibility
from __future__ import print_function

import numpy as np
import cv2
from multiprocessing.pool import ThreadPool


def build_filters():
    """Builds collection of gabor filters.
    
    Parameters
    ----------
    
    Returns
    -------
    filters : list
        List of gabor filters.
        
    """
    filters = []
    ksize = 31
    for theta in np.arange(0, np.pi, np.pi / 16):
        kern = cv2.getGaborKernel((ksize, ksize), 4.0, theta, 10.0, 0.5, 0, ktype=cv2.CV_32F)
        kern /= 1.5*kern.sum()
        filters.append(kern)
    return filters


def process(img, filters):
    """Filters image by several gabor filters from a list.

    Parameters
    ----------
    img : ndarray
        To be filtered image.     
    filters : list
        Gabor filters.

    Returns
    -------
    accum : ndarray
        Gaborfiltered image.

    """
    accum = np.zeros_like(img)
    for kern in filters:
        fimg = cv2.filter2D(img, cv2.CV_32F, kern)
        np.maximum(accum, fimg, accum)
    return accum


def process_threaded(img, filters, threadn = 4):
    """Starts threated gabor filtering of image.

    Parameters
    ----------
    img : ndarray
        To be filtered image.     
    filters : list
        Gabor filters.
    threadn : int
        Number of threads for multiprocessing. (Default value = 4)

    Returns
    -------
    accum : ndarray
        Gaborfiltered image.

    """
    accum = np.zeros_like(img)
    def f(kern):
        return cv2.filter2D(img, cv2.CV_32F, kern)
    pool = ThreadPool(processes=threadn)
    for fimg in pool.imap_unordered(f, filters):
        np.maximum(accum, fimg, accum)
    return accum


def get_gabor(img):
    """Returns gabor filtered image of a given image.

    Parameters
    ----------
    img : ndarray
        Image to be filtered.

    Returns
    -------
    img : ndarray
        The filtered image.

    """
    filters = build_filters()
    return process_threaded(img, filters)


if __name__ == '__main__':
    import sys
#    from common import Timer

    print(__doc__)
    try:
        img_fn = sys.argv[1]
    except:
        img_fn = '../data/baboon.jpg'

    img = cv2.imread(img_fn)
    if img is None:
        print('Failed to load image file:', img_fn)
        sys.exit(1)

    filters = build_filters()

#    with Timer('running single-threaded'):
#        res1 = process(img, filters)
#    with Timer('running multi-threaded'):
#        res2 = process_threaded(img, filters)
    res1 = process(img, filters)
    res2 = process_threaded(img, filters)

    print('res1 == res2: ', (res1 == res2).all())
    cv2.imshow('img', img)
    cv2.imshow('result', res2)
    cv2.waitKey()
    cv2.destroyAllWindows()