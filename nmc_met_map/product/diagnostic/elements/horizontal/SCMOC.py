# _*_ coding: utf-8 _*_

# Copyright (c) 2019 NMC Developers.
# Distributed under the terms of the GPL V3 License.

"""
Map design before drawing
"""

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
#import cartopy.io.img_tiles as cimgt
from matplotlib.patches import Patch
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from nmc_met_graphics.plot.china_map import add_china_map_2cartopy
from nmc_met_graphics.cmap.cm import guide_cmaps
from nmc_met_graphics.plot.util import add_logo, add_model_title
from nmc_met_map.lib.utility import add_logo_extra,add_city_on_map,add_china_map_2cartopy_public,add_public_title,add_south_China_sea,adjust_map_ratio,add_public_title_obs,add_logo_extra_in_axes,add_public_title_sta
from datetime import datetime, timedelta
import pandas as pd
import locale
import scipy.ndimage as ndimage
from matplotlib.colors import BoundaryNorm,ListedColormap
import sys
import nmc_met_graphics.cmap.ctables as dk_ctables
import nmc_met_graphics.cmap.cm as dk_ctables2
import nmc_met_graphics.cmap.wrf as wrf_ctables
import nmc_met_map.lib.utility as utl
import nmc_met_graphics.mask as dk_mask
import os
from scipy.ndimage import gaussian_filter
import matplotlib.patheffects as path_effects
import cartopy.io.img_tiles as cimg
from matplotlib.font_manager import FontProperties
import matplotlib.patches as mpatches
import nmc_met_map.graphics2 as GF


def draw_TMP2(TMP2,map_extent=(60, 150, 0, 65),
                    add_china=True,city=True,south_China_sea=True,add_background=True,
                    output_dir=None,**kargws):

    initTime = pd.to_datetime(TMP2.coords['time'].values[0]).replace(tzinfo=None).to_pydatetime()
    fhour = int(TMP2['fhour'].values[0])
    fcstTime = initTime + timedelta(hours=fhour)

    title = '[{}] 过去{}小时最高温度'.format(TMP2.attrs['model_name'],str(np.abs(TMP2.attrs['vhours'])))
    
    forcast_info = '起报时间: {0:%Y}年{0:%m}月{0:%d}日{0:%H}时\n预报时间: {1:%Y}年{1:%m}月{1:%d}日{1:%H}时\n预报时效: {2}小时\nwww.nmc.cn'.format(initTime, fcstTime, fhour)

    fig, ax, map_extent = GF.pallete_set.Horizontal_Pallete((18, 9),map_extent=map_extent, title=title, forcast_info=forcast_info,info_zorder=4,
                                             add_china=add_china, add_city=city, add_background=add_background, south_China_sea=south_China_sea)

    pcolor_Tmx=GF.draw_method.Tmx_pcolormesh(ax, TMP2['lon'].values, TMP2['lat'].values, np.squeeze(TMP2.values),zorder=1)

    z=gaussian_filter(np.squeeze(TMP2.values),5)
    contour_Heat=GF.draw_method.Tmx_contour(ax, TMP2['lon'].values, TMP2['lat'].values, z,zorder=2)
    contour_Zero=GF.draw_method.Tmx_contour(ax, TMP2['lon'].values, TMP2['lat'].values, z,colors=['#232B99'],levels=[0],zorder=3)

    if(city is True):
        utl.add_city_values_on_map(ax,TMP2,map_extent=map_extent,zorder=5)

    l, b, w, h = ax.get_position().bounds
    cax=plt.axes([l,b-0.04,w,.02])
    cb = plt.colorbar(pcolor_Tmx, cax=cax, orientation='horizontal',
                      extend='both',extendrect=False)
    cb.ax.tick_params(labelsize='x-large')
    cb.set_label('($^\circ$C)',size=20)

    if output_dir:
        png_name = '{0:%Y}年{0:%m}月{0:%d}日{0:%H}时观测|分析'.format(initTime)+'的过去{}小时最高温度'.format(str(np.abs(TMP2['data'].attrs['vhours'])))
        plt.savefig(os.path.join(output_dir, png_name), idpi=300, bbox_inches='tight')
    else:
        plt.show()

def draw_dT2m(dT2m,map_extent=(60, 150, 0, 65),
                    add_china=True,city=True,south_China_sea=True,add_background=True,
                    output_dir=None,**kargws):

    initTime = pd.to_datetime(dT2m.coords['time'].values[0]).replace(tzinfo=None).to_pydatetime()
    fhour = int(dT2m['fhour'].values[0])
    fcstTime = initTime + timedelta(hours=fhour)

    title = '[{}] {}'.format(dT2m.attrs['model_name'],dT2m.attrs['var_name'])
    
    forcast_info = '起报时间: {0:%Y}年{0:%m}月{0:%d}日{0:%H}时\n预报时间: {1:%Y}年{1:%m}月{1:%d}日{1:%H}时\n预报时效: {2}小时\nwww.nmc.cn'.format(initTime, fcstTime, fhour)

    fig, ax, map_extent = GF.pallete_set.Horizontal_Pallete((18, 9),map_extent=map_extent, title=title, forcast_info=forcast_info,info_zorder=4,
                                             add_china=add_china, add_city=city, add_background=add_background, south_China_sea=south_China_sea)

    pcolor_dTm=GF.draw_method.dT2m_pcolormesh(ax, dT2m['lon'].values, dT2m['lat'].values, np.squeeze(dT2m.values),zorder=1)
    z=gaussian_filter(np.squeeze(dT2m.values),5)
    contour_dTm=GF.draw_method.dT2m_contour(ax, dT2m['lon'].values, dT2m['lat'].values, z,zorder=2)
    if(city is True):
        utl.add_city_values_on_map(ax,dT2m,map_extent=map_extent,zorder=5)

    l, b, w, h = ax.get_position().bounds
    cax=plt.axes([l,b-0.04,w,.02])
    cb = plt.colorbar(pcolor_dTm, cax=cax, orientation='horizontal',
                      extend='both',extendrect=False)
    cb.ax.tick_params(labelsize='x-large')
    cb.set_label('($^\circ$C)',size=20)

    if output_dir:
        png_name = '{0:%Y}年{0:%m}月{0:%d}日{0:%H}时观测|分析'.format(initTime)+'的过去{}小时最高温度'.format(str(np.abs(TMP2['data'].attrs['vhours'])))
        plt.savefig(os.path.join(output_dir, png_name), idpi=300, bbox_inches='tight')
    else:
        plt.show()