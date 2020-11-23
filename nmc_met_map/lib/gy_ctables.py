# _*_ coding: utf-8 _*_

# Copyright (c) 2019 NMC Developers.
# Distributed under the terms of the GPL V3 License.

"""
Define customer color maps.
"""

import numpy as np
import matplotlib as mpl
from nmc_met_graphics.cmap.cm import make_cmap

def wvfl_ctable(pos=None):
    """
    Precipitation type color map.
    Keyword Arguments:
        pos {[type]} -- specify the color position (default: {None})
    """
    _colors = [
        '#FDD6C4','#FCAE92','#FC8363','#F6573E','#DE2B25','#B81419','#840711', 
        '#FBB1BA','#F98CAE','#F25E9F','#DC3296','#B40781','#890179','#600070', 
        '#787878','#8C8C8C','#A0A0A0','#B4B4B4','#C8C8C8','#DCDCDC','#F0F0F0']

    if pos is None:
        _pos =[
        5,6,7,8,9,10,11, 
        12,13,14,15,16,17,18, 
        19,20,21,22,23,24,25]
    else:
        _pos = pos
    #cmap, norm = mpl.colors.from_levels_and_colors(_pos, _colors, extend='max')
    #return cmap, norm
    cmap, norm = mpl.colors.from_levels_and_colors(_pos, _colors, extend='max')
    return cmap, norm

def cm_precipitation_nmc(atime=24):
    """
    http://jjhelmus.github.io/blog/2013/09/17/plotting-nsw-precipitation-data/
    :param atime: accumulative time period.
    :return: colormap function, normalization boundary.
    """

    if atime >= 24 :
        clevs = [0.01, 10, 25, 50, 100, 250]
    else:
        clevs = [0.01, 2.5, 5, 10, 25, 50, 100,250]
    
    if atime >= 24 :
        colors = ["#88F492", "#00A929", "#2AB8FF", "#1202FC", "#FF04F4", "#850C3E"]
    else: 
        colors = ["#88F492", "#6FD96D","#3AB941","#308932", "#2AB8FF", "#1202FC", "#FF04F4", "#850C3E"]
    return colors, clevs
