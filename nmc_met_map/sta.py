import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import math
import os
import xarray as xr
import metpy.calc as mpcalc
from metpy.units import units
from nmc_met_io.retrieve_micaps_server import get_model_points,get_model_3D_grid,get_latest_initTime,get_model_3D_grids,get_station_data,get_model_grids
import nmc_met_io.retrieve_micaps_server as MICAPS_IO
import nmc_met_map.lib.utility as utl
from nmc_met_map.graphics import sta_graphics
import matplotlib.pyplot as plt
import metpy.calc as mpcalc
from metpy.cbook import get_test_data
from metpy.plots import add_metpy_logo, SkewT
from metpy.units import units
from scipy.stats import norm
from scipy.interpolate import LinearNDInterpolator

def Station_Synthetical_Forecast_From_Cassandra(
        model='ECMWF',
        output_dir=None,
        t_range=[0,84],
        t_gap=3,
        points={'lon':[116.3833], 'lat':[39.9]},
        initTime=None,
        draw_VIS=True,drw_thr=False,
        extra_info={
            'output_head_name':' ',
            'output_tail_name':' ',
            'point_name':' '}
            ,**kwargs):

    #+get all the directories needed
    try:
        dir_rqd=[ 
                "ECMWF_HR/10_METRE_WIND_GUST_IN_THE_LAST_3_HOURS/",
                "ECMWF_HR/10_METRE_WIND_GUST_IN_THE_LAST_6_HOURS/",
                "ECMWF_HR/TCDC/",
                "ECMWF_HR/LCDC/",
                "ECMWF_HR/UGRD_100M/",
                "ECMWF_HR/VGRD_100M/",
                "NWFD_SCMOC/VIS/",

                utl.Cassandra_dir(
                    data_type='surface',data_source=model,var_name='RAIN03'),
                utl.Cassandra_dir(
                    data_type='surface',data_source=model,var_name='RAIN06'),
                utl.Cassandra_dir(
                    data_type='surface',data_source=model,var_name='T2m'),
                utl.Cassandra_dir(
                    data_type='surface',data_source=model,var_name='u10m'),
                utl.Cassandra_dir(
                    data_type='surface',data_source=model,var_name='v10m'),
                ]
    except KeyError:
        raise ValueError('Can not find all required directories needed')
    
    try:
        dir_opt=[ 
                utl.Cassandra_dir(
                    data_type='surface',data_source=model,var_name='Td2m')
                ]
        name_opt=['Td2m']
    except:
        dir_opt=[
                utl.Cassandra_dir(data_type='surface',data_source=model,var_name='rh2m')
                ]
        name_opt=['rh2m']
          
    #+get all the directories needed

    if(initTime == None):
        last_file={model:get_latest_initTime(dir_rqd[7]),
                    'SCMOC':get_latest_initTime(dir_rqd[0]),
                    }
    else:
        last_file={model:initTime[0],
                    'SCMOC':initTime[1],
                    }        

    fhours = np.arange(t_range[0], t_range[1], t_gap)

    filenames = [last_file[model]+'.'+str(fhour).zfill(3) for fhour in fhours]
    t2m=utl.get_model_points_gy(dir_rqd[9], filenames, points,allExists=False)
    
    if(name_opt[0] == 'rh2m'):
        rh2m=utl.get_model_points_gy(dir_opt[0], filenames, points,allExists=False)
        Td2m=mpcalc.dewpoint_rh(t2m['data'].values*units('degC'),rh2m['data'].values/100.)
        p_vapor=(rh2m['data'].values/100.)*6.105*(math.e**((17.27*t2m['data'].values/(237.7+t2m['data'].values))))

    if(name_opt[0] == 'Td2m'):
        Td2m=utl.get_model_points_gy(dir_opt[0], filenames, points,allExists=False)        
        rh2m=mpcalc.relative_humidity_from_dewpoint(t2m['data'].values* units('degC'),
                Td2m['data'].values* units('degC'))
        p_vapor=(np.array(rh2m))*6.105*(math.e**((17.27*t2m['data'].values/(237.7+t2m['data'].values))))
        Td2m=np.array(Td2m['data'].values)* units('degC')

    u10m=utl.get_model_points_gy(dir_rqd[10], filenames, points,allExists=False)
    v10m=utl.get_model_points_gy(dir_rqd[11], filenames, points,allExists=False)
    wsp10m=(u10m['data']**2+v10m['data']**2)**0.5
    AT=1.07*t2m['data'].values+0.2*p_vapor-0.65*wsp10m-2.7

    if((fhours[-1]) > 72):
        fhours = np.arange(6, t_range[1], 6)
        filenames = [last_file[model]+'.'+str(fhour).zfill(3) for fhour in fhours]
        r03=utl.get_model_points_gy(dir_rqd[8], filenames, points,allExists=False)
    else:
        r03=utl.get_model_points_gy(dir_rqd[7], filenames, points,allExists=False)

    # if(last_file['SCMOC'] == last_file[model] and t_range[1] > 72):
    #     fhours = np.append(np.arange(3,72,3),np.arange(72, (t_range[1]), 6))
    #     filenames = [last_file[model]+'.'+str(fhour).zfill(3) for fhour in fhours]
    #     filenames2 = [last_file[model]+'.'+str(fhour).zfill(3) for fhour in fhours]            

    # if(last_file['SCMOC'] != last_file[model] and t_range[1] > 60):
    #     fhours = np.append(np.arange(3,60,3),np.arange(60, (t_range[1]), 6))
    #     filenames = [last_file[model]+'.'+str(fhour+12).zfill(3) for fhour in fhours]
    #     filenames2 = [last_file['SCMOC']+'.'+str(fhour).zfill(3) for fhour in fhours]

    # if(last_file['SCMOC'] != last_file[model] and t_range[1] <= 60):
    #     fhours = np.arange(t_range[0], t_range[1], t_gap)
    #     filenames = [last_file[model]+'.'+str(fhour+12).zfill(3) for fhour in fhours]
    #     filenames2 = [last_file['SCMOC']+'.'+str(fhour).zfill(3) for fhour in fhours]

    # if(last_file['SCMOC'] == last_file[model] and t_range[1] <= 72):
    #     fhours = np.arange(t_range[0], t_range[1], t_gap)
    #     filenames = [last_file[model]+'.'+str(fhour).zfill(3) for fhour in fhours]
    #     filenames2 = [last_file[model]+'.'+str(fhour).zfill(3) for fhour in fhours]

    fhours = np.arange(t_range[0], t_range[1], t_gap)
    filenames2 = [last_file['SCMOC']+'.'+str(fhour).zfill(3) for fhour in fhours]
    VIS=utl.get_model_points_gy(dir_rqd[6], filenames2, points,allExists=False,fill_null=True,Null_value=-0.001)
    TCDC=utl.get_model_points_gy(dir_rqd[2], filenames2, points,allExists=False)
    LCDC=utl.get_model_points_gy(dir_rqd[3], filenames2, points,allExists=False)
    u100m=utl.get_model_points_gy(dir_rqd[4], filenames2, points,allExists=False)
    v100m=utl.get_model_points_gy(dir_rqd[5], filenames2, points,allExists=False)
    wsp100m=(u100m['data']**2+v100m['data']**2)**0.5
    if(fhours[-1] < 120):
        gust10m=utl.get_model_points_gy(dir_rqd[0], filenames2, points,allExists=False)
    if(fhours[-1] > 120):
        gust10m=utl.get_model_points_gy(dir_rqd[1], filenames2, points,allExists=False)        

    # if(fhours[-1] < 120):
    #     gust10m=utl.get_model_points_gy(dir_rqd[0], filenames2, points,allExists=False)
    # if(fhours[-1] > 120):
    #     if(last_file['SCMOC'] == last_file[model]):
    #         fhours = np.arange(0, t_range[1], 6)
    #         filenames = [last_file[model]+'.'+str(fhour).zfill(3) for fhour in fhours]
    #     if(last_file['SCMOC'] != last_file[model]):
    #         fhours = np.arange(0, t_range[1], 6)
    #         filenames = [last_file[model]+'.'+str(fhour+12).zfill(3) for fhour in fhours]
    #     gust10m=utl.get_model_points_gy(dir_rqd[1], filenames2, points,allExists=False)        
        
    time_all=gust10m.time.values[np.in1d(gust10m.time.values,t2m.time.values)]

    time_new=[pd.to_datetime(time_all[0]).replace(tzinfo=None).to_pydatetime()+timedelta(hours=int(ihour)) for ihour in np.arange(0,(time_all[-1]-time_all[0])/np.timedelta64(1,'h')+1)]
    VIS_hourly=VIS.interp(time=time_new).rename({'data':'VIS'}).to_dataframe().drop(columns=['lon', 'lat','forecast_reference_time','forecast_period'])
    wsp10m_hourly=wsp10m.interp(time=time_new).to_dataframe(name='wsp10m').drop(columns=['lon', 'lat','forecast_reference_time','forecast_period'])
    r03_hourly=r03.interp(time=time_new).rename({'data':'r03'}).to_dataframe().drop(columns=['lon', 'lat','forecast_reference_time','forecast_period'])
    t2m_hourly=t2m.interp(time=time_new).rename({'data':'t2m'}).to_dataframe().drop(columns=['lon', 'lat','forecast_reference_time','forecast_period'])
    pd_output=VIS_hourly.merge(wsp10m_hourly,on='time').merge(r03_hourly,on='time').merge(t2m_hourly,on='time')
    if(output_dir is not None):
        pd_output.to_csv(output_dir+extra_info['point_name']+pd.to_datetime(wsp10m['forecast_reference_time'].values).replace(tzinfo=None).to_pydatetime().strftime('%Y%m%d%H')+'_起报.csv')

    sta_graphics.draw_Station_Synthetical_Forecast_From_Cassandra(
            t2m=t2m,Td2m=Td2m,AT=AT,u10m=u10m,v10m=v10m,u100m=u100m,v100m=v100m,
            gust10m=gust10m,wsp10m=wsp10m,wsp100m=wsp100m,r03=r03,TCDC=TCDC,LCDC=LCDC,
            draw_VIS=draw_VIS,VIS=VIS,drw_thr=drw_thr,
            time_all=time_all,
            model=model,points=points,
            output_dir=output_dir,extra_info=extra_info)

def Station_Snow_Synthetical_Forecast_From_Cassandra(
        model='ECMWF',
        output_dir=None,
        t_range=[0,84],
        t_gap=3,
        points={'lon':[116.3833], 'lat':[39.9]},
        initTime=None,
        draw_VIS=True,drw_thr=False,
        extra_info={
            'output_head_name':' ',
            'output_tail_name':' ',
            'point_name':' '}
            ,**kwargs):

    #+get all the directories needed
    try:
        dir_rqd=[ 
                "ECMWF_HR/10_METRE_WIND_GUST_IN_THE_LAST_3_HOURS/",
                "ECMWF_HR/10_METRE_WIND_GUST_IN_THE_LAST_6_HOURS/",
                "ECMWF_HR/SNOD/",
                "ECMWF_HR/SDEN/",
                "ECMWF_HR/UGRD_100M/",
                "ECMWF_HR/VGRD_100M/",
                "NWFD_SCMOC/VIS/",
                "NCEP_GFS_HR/SNOD/",
                "ECMWF_HR/SNOW06/",
                utl.Cassandra_dir(
                    data_type='surface',data_source=model,var_name='T2m'),
                utl.Cassandra_dir(
                    data_type='surface',data_source=model,var_name='u10m'),
                utl.Cassandra_dir(
                    data_type='surface',data_source=model,var_name='v10m'),
                'ECMWF_ENSEMBLE/RAW/SNOW06/'
                ]
    except KeyError:
        raise ValueError('Can not find all required directories needed')
    
    try:
        dir_opt=[ 
                utl.Cassandra_dir(
                    data_type='surface',data_source=model,var_name='Td2m')
                ]
        name_opt=['Td2m']
    except:
        dir_opt=[
                utl.Cassandra_dir(data_type='surface',data_source=model,var_name='rh2m')
                ]
        name_opt=['rh2m']
          
    #+get all the directories needed

    if(initTime == None):
        last_file={model:get_latest_initTime(dir_rqd[0]),
                    'SCMOC':get_latest_initTime(dir_rqd[6]),
                    }
    else:
        last_file={model:initTime[0],
                    'SCMOC':initTime[1],
                    }        

    y_s={model:int('20'+last_file[model][0:2]),
        'SCMOC':int('20'+last_file['SCMOC'][0:2])}
    m_s={model:int(last_file[model][2:4]),
        'SCMOC':int(last_file['SCMOC'][2:4])}
    d_s={model:int(last_file[model][4:6]),
        'SCMOC':int(last_file['SCMOC'][4:6])}
    h_s={model:int(last_file[model][6:8]),
        'SCMOC':int(last_file['SCMOC'][6:8])}

    fhours = np.arange(t_range[0], t_range[1], t_gap)

    for ifhour in fhours:
        if (ifhour == fhours[0] ):
            time_all=datetime(y_s['SCMOC'],m_s['SCMOC'],d_s['SCMOC'],h_s['SCMOC'])+timedelta(hours=int(ifhour))
        else:
            time_all=np.append(time_all,datetime(y_s['SCMOC'],m_s['SCMOC'],d_s['SCMOC'],h_s['SCMOC'])+timedelta(hours=int(ifhour)))            

    filenames = [last_file[model]+'.'+str(fhour).zfill(3) for fhour in fhours]
    t2m=utl.get_model_points_gy(dir_rqd[9], filenames, points,allExists=False)
    
    if(name_opt[0] == 'rh2m'):
        rh2m=utl.get_model_points_gy(dir_opt[0], filenames, points,allExists=False)
        Td2m=mpcalc.dewpoint_rh(t2m['data'].values*units('degC'),rh2m['data'].values/100.)
        p_vapor=(rh2m['data'].values/100.)*6.105*(math.e**((17.27*t2m['data'].values/(237.7+t2m['data'].values))))

    if(name_opt[0] == 'Td2m'):
        Td2m=utl.get_model_points_gy(dir_opt[0], filenames, points,allExists=False)        
        rh2m=mpcalc.relative_humidity_from_dewpoint(t2m['data'].values* units('degC'),
                Td2m['data'].values* units('degC'))
        p_vapor=(np.array(rh2m))*6.105*(math.e**((17.27*t2m['data'].values/(237.7+t2m['data'].values))))
        Td2m=np.array(Td2m['data'].values)* units('degC')

    #SN06_ensm=utl.get_model_points_gy(dir_rqd[12], filenames, points,allExists=False)
    '''
    for i in range(0,len(SN06_ensm['forecast_period'])):
        SN06_std=np.std(np.squeeze(SN06_ensm['data'].values[i,:]))
        SN06_mean=np.mean(np.squeeze(SN06_ensm['data'].values[i,:]))
        if(i == 0):
            SN06_01=norm.pdf(0.01, SN06_mean, SN06_std)
            SN06_10=norm.pdf(0.1, SN06_mean, SN06_std)
            SN06_25=norm.pdf(0.25, SN06_mean, SN06_std)
            SN06_50=norm.pdf(0.5, SN06_mean, SN06_std)
            SN06_75=norm.pdf(0.75, SN06_mean, SN06_std)
            SN06_90=norm.pdf(0.9, SN06_mean, SN06_std)
            SN06_99=norm.pdf(0.99, SN06_mean, SN06_std)
        if(i > 0):
            SN06_01=[SN06_01,norm.pdf(0.01, SN06_mean, SN06_std)]
            SN06_10=[SN06_10,norm.pdf(0.1, SN06_mean, SN06_std)]
            SN06_25=[SN06_25,norm.pdf(0.25, SN06_mean, SN06_std)]
            SN06_50=[SN06_50,norm.pdf(0.5, SN06_mean, SN06_std)]
            SN06_75=[SN06_75,norm.pdf(0.75, SN06_mean, SN06_std)]
            SN06_90=[SN06_90,norm.pdf(0.9, SN06_mean, SN06_std)]
            SN06_99=[SN06_99,norm.pdf(0.99, SN06_mean, SN06_std)]

    SN06_ensm_stc={            
        'SN06_01'=SN06_01
        'SN06_10'=SN06_10
        'SN06_25'=SN06_25
        'SN06_50'=SN06_50
        'SN06_75'=SN06_75
        'SN06_90'=SN06_90
        'SN06_99'=SN06_99
        }
    '''
    u10m=utl.get_model_points_gy(dir_rqd[10], filenames, points,allExists=False)
    v10m=utl.get_model_points_gy(dir_rqd[11], filenames, points,allExists=False)
    wsp10m=(u10m['data']**2+v10m['data']**2)**0.5
    AT=1.07*t2m['data'].values+0.2*p_vapor-0.65*wsp10m-2.7
    #https://en.wikipedia.org/wiki/Wind_chill
    TWC=13.12+0.6215*t2m['data'].values-11.37*(wsp10m**0.16)+0.3965*t2m['data'].values*(wsp10m**0.16)

    fhours = np.arange(t_range[0], t_range[1], t_gap)
    filenames = [last_file['SCMOC']+'.'+str(fhour).zfill(3) for fhour in fhours]
    VIS=utl.get_model_points_gy(dir_rqd[6], filenames, points,allExists=False,fill_null=True,Null_value=-0.001)     

    if(last_file['SCMOC'] == last_file[model] and t_range[1] > 72):
        fhours = np.append(np.arange(3,72,3),np.arange(72, (t_range[1]), 6))
        filenames = [last_file[model]+'.'+str(fhour).zfill(3) for fhour in fhours]
        filenames2 = [last_file[model]+'.'+str(fhour).zfill(3) for fhour in fhours]            

    if(last_file['SCMOC'] != last_file[model] and t_range[1] > 60):
        fhours = np.append(np.arange(3,60,3),np.arange(60, (t_range[1]), 6))
        filenames = [last_file[model]+'.'+str(fhour+12).zfill(3) for fhour in fhours]
        filenames2 = [last_file[model]+'.'+str(fhour).zfill(3) for fhour in fhours]

    if(last_file['SCMOC'] != last_file[model] and t_range[1] <= 60):
        fhours = np.arange(t_range[0], t_range[1], t_gap)
        filenames = [last_file[model]+'.'+str(fhour+12).zfill(3) for fhour in fhours]
        filenames2 = [last_file[model]+'.'+str(fhour).zfill(3) for fhour in fhours]

    if(last_file['SCMOC'] == last_file[model] and t_range[1] <= 72):
        fhours = np.arange(t_range[0], t_range[1], t_gap)
        filenames = [last_file[model]+'.'+str(fhour).zfill(3) for fhour in fhours]
        filenames2 = [last_file[model]+'.'+str(fhour).zfill(3) for fhour in fhours]

    SNOD1=utl.get_model_points_gy(dir_rqd[2], filenames2, points,allExists=False)
    SNOD2=utl.get_model_points_gy(dir_rqd[7], filenames2, points,allExists=False)
    SDEN=utl.get_model_points_gy(dir_rqd[3], filenames2, points,allExists=False)
    SN06=utl.get_model_points_gy(dir_rqd[8], filenames2, points,allExists=False)
    u100m=utl.get_model_points_gy(dir_rqd[4], filenames2, points,allExists=False)
    v100m=utl.get_model_points_gy(dir_rqd[5], filenames2, points,allExists=False)
    wsp100m=(u100m['data']**2+v100m['data']**2)**0.5

    if(fhours[-1] < 120):
        gust10m=utl.get_model_points_gy(dir_rqd[0], filenames, points,allExists=False)
    if(fhours[-1] > 120):
        if(last_file['SCMOC'] == last_file[model]):
            fhours = np.arange(0, t_range[1], 6)
            filenames = [last_file[model]+'.'+str(fhour).zfill(3) for fhour in fhours]
        if(last_file['SCMOC'] != last_file[model]):
            fhours = np.arange(0, t_range[1], 6)
            filenames = [last_file[model]+'.'+str(fhour+12).zfill(3) for fhour in fhours]
        gust10m=utl.get_model_points_gy(dir_rqd[1], filenames, points,allExists=False)        
        
    sta_graphics.draw_Station_Snow_Synthetical_Forecast_From_Cassandra(
            TWC=TWC,AT=AT,u10m=u10m,v10m=v10m,u100m=u100m,v100m=v100m,
            gust10m=gust10m,wsp10m=wsp10m,wsp100m=wsp100m,SNOD1=SNOD1,SNOD2=SNOD2,SDEN=SDEN,SN06=SN06,
            draw_VIS=draw_VIS,VIS=VIS,drw_thr=drw_thr,
            time_all=time_all,
            model=model,points=points,
            output_dir=output_dir,extra_info=extra_info)
            
def sta_SkewT(model='ECMWF',points={'lon':[116.3833], 'lat':[39.9]},
    levels=[1000, 950, 925, 900, 850, 800, 700,600,500,400,300,250,200,150,100],
    fhour=3,output_dir=None,extra_info=None,**kwargs):

    try:
        data_dir = [utl.Cassandra_dir(data_type='high',data_source=model,var_name='TMP',lvl=''),
                    utl.Cassandra_dir(data_type='high',data_source=model,var_name='UGRD',lvl=''),
                    utl.Cassandra_dir(data_type='high',data_source=model,var_name='VGRD',lvl=''),
                    utl.Cassandra_dir(data_type='high',data_source=model,var_name='HGT',lvl=''),
                    utl.Cassandra_dir(data_type='high',data_source=model,var_name='RH',lvl='')]
    except KeyError:
        raise ValueError('Can not find all directories needed')

    # # 度数据
    initTime = get_latest_initTime(data_dir[0][0:-1]+"850")
    filename = initTime+'.'+str(fhour).zfill(3)
    TMP_4D=get_model_3D_grid(directory=data_dir[0][0:-1],filename=filename,levels=levels, allExists=False)
    TMP_2D=TMP_4D.interp(lon=('points', points['lon']), lat=('points', points['lat']))

    u_4D=get_model_3D_grid(directory=data_dir[1][0:-1],filename=filename,levels=levels, allExists=False)
    u_2D=u_4D.interp(lon=('points', points['lon']), lat=('points', points['lat']))

    v_4D=get_model_3D_grid(directory=data_dir[2][0:-1],filename=filename,levels=levels, allExists=False)
    v_2D=v_4D.interp(lon=('points', points['lon']), lat=('points', points['lat']))

    HGT_4D=get_model_3D_grid(directory=data_dir[3][0:-1],filename=filename,levels=levels, allExists=False)
    HGT_2D=HGT_4D.interp(lon=('points', points['lon']), lat=('points', points['lat']))
    HGT_2D.attrs['model']=model
    HGT_2D.attrs['points']=points

    RH_4D=get_model_3D_grid(directory=data_dir[4][0:-1],filename=filename,levels=levels, allExists=False)
    RH_2D=RH_4D.interp(lon=('points', points['lon']), lat=('points', points['lat']))

    wind_dir_2D=mpcalc.wind_direction(u_2D['data'].values* units.meter / units.second,
        v_2D['data'].values* units.meter / units.second)
    wsp10m_2D=(u_2D['data']**2+v_2D['data']**2)**0.5
    Td2m=mpcalc.dewpoint_rh(TMP_2D['data'].values*units('degC'),RH_2D['data'].values/100.)

    p = np.squeeze(levels) * units.hPa
    T = np.squeeze(TMP_2D['data'].values) * units.degC
    Td = np.squeeze(np.array(Td2m)) * units.degC
    wind_speed = np.squeeze(wsp10m_2D.values) * units.meter
    wind_dir = np.squeeze(np.array(wind_dir_2D)) * units.degrees
    u=np.squeeze(u_2D['data'].values)* units.meter
    v=np.squeeze(v_2D['data'].values)* units.meter

    fcst_info= xr.DataArray(np.array(u_2D['data'].values),
                        coords=u_2D['data'].coords,
                        dims=u_2D['data'].dims,
                        attrs={'points': points,
                                'model': model})

    sta_graphics.draw_sta_skewT(
        p=p,T=T,Td=Td,wind_speed=wind_speed,wind_dir=wind_dir,u=u,v=v,
        fcst_info=fcst_info,extra_info=extra_info,output_dir=output_dir)


def point_wind_time_fcst_according_to_3D_wind(
        model='ECMWF',
        output_dir=None,
        t_range=[0,60],
        t_gap=3,
        points={'lon':[116.3833], 'lat':[39.9], 'altitude':[1351]},
        initTime=None,draw_obs=True,obs_ID=54511,day_back=0,
        extra_info={
            'output_head_name':' ',
            'output_tail_name':' ',
            'point_name':' ',
            'drw_thr':True,
            'levels_for_interp':[1000, 950, 925, 900, 850, 800, 700, 600, 500]}
            ,**kwargs):

    #+get all the directories needed
    try:
        dir_rqd=[utl.Cassandra_dir(data_type='high',data_source=model,var_name='HGT',lvl=''),
                        utl.Cassandra_dir(data_type='high',data_source=model,var_name='UGRD',lvl=''),
                        utl.Cassandra_dir(data_type='high',data_source=model,var_name='VGRD',lvl='')]
    except KeyError:
        raise ValueError('Can not find all required directories needed')
    
    #-get all the directories needed
    if(initTime == None):
        initTime = get_latest_initTime(dir_rqd[0][0:-1]+'/850')
        #initTime=utl.filename_day_back_model(day_back=day_back,fhour=0)[0:8]

    directory=dir_rqd[0][0:-1]
    fhours = np.arange(t_range[0], t_range[1], t_gap)
    filenames = [initTime+'.'+str(fhour).zfill(3) for fhour in fhours]
    HGT_4D=get_model_3D_grids(directory=directory,filenames=filenames,levels=extra_info['levels_for_interp'], allExists=False)
    directory=dir_rqd[1][0:-1]
    U_4D=get_model_3D_grids(directory=directory,filenames=filenames,levels=extra_info['levels_for_interp'], allExists=False)
    directory=dir_rqd[2][0:-1]
    V_4D=get_model_3D_grids(directory=directory,filenames=filenames,levels=extra_info['levels_for_interp'], allExists=False)
    #obs
    if(draw_obs == True):
        initTime=pd.to_datetime(str(V_4D['forecast_reference_time'].values)).replace(tzinfo=None).to_pydatetime()
        sign=0
        for ifhour in V_4D['forecast_period'].values:
            temp=(initTime+timedelta(hours=ifhour))
            filenames_obs=temp.strftime("%Y%m%d%H")+'0000.000'
            try:
                obs_data=get_station_data('SURFACE/PLOT/',filename=filenames_obs)
            except:
                break

            if(obs_data is not None):
                temp=obs_data.where(obs_data['ID']==obs_ID).dropna(how='all')
                if ((ifhour == V_4D['forecast_period'].values[0]) or ((ifhour > V_4D['forecast_period'].values[0]) and (sign==0))):
                    if(len(temp) > 0):
                        sta_obs_data=obs_data.where(obs_data['ID']==obs_ID).dropna(how='all').reset_index()
                        sign=1
                else:
                    if(len(temp) > 0):
                        sta_obs_data=sta_obs_data.append(temp).reset_index()
            if(obs_data is None):
                break
        try:
            sta_obs_data
        except:
            draw_obs=False

    delt_xy=HGT_4D['lon'].values[1]-HGT_4D['lon'].values[0]
    mask = (HGT_4D['lon']<(points['lon']+2*delt_xy))&(HGT_4D['lon']>(points['lon']-2*delt_xy))&(HGT_4D['lat']<(points['lat']+2*delt_xy))&(HGT_4D['lat']>(points['lat']-2*delt_xy))

    HGT_4D_sm=HGT_4D['data'].where(mask,drop=True)
    U_4D_sm=U_4D['data'].where(mask,drop=True)
    V_4D_sm=V_4D['data'].where(mask,drop=True)

    lon_md=np.squeeze(HGT_4D_sm['lon'].values)
    lat_md=np.squeeze(HGT_4D_sm['lat'].values)
    alt_md=np.squeeze(HGT_4D_sm.values*10).flatten()
    time_md=np.squeeze(HGT_4D_sm['forecast_period'].values)

    coords = np.zeros((len(time_md),len(extra_info['levels_for_interp']),len(lat_md),len(lon_md),4))
    coords[...,0]=time_md.reshape((len(time_md),1,1,1))
    coords[...,2] = lat_md.reshape((1,1,len(lat_md),1))
    coords[...,3] = lon_md.reshape((1,1,1,len(lon_md)))
    coords = coords.reshape((alt_md.size,4))
    coords[:,1]=alt_md

    interpolator_U = LinearNDInterpolator(coords,U_4D_sm.values.reshape((U_4D_sm.values.size)),rescale=True)
    interpolator_V = LinearNDInterpolator(coords,V_4D_sm.values.reshape((V_4D_sm.values.size)),rescale=True)

    coords2 = np.zeros((len(time_md),1,1,1,4))
    coords2[...,0]=time_md.reshape((len(time_md),1,1,1))
    coords2[...,1]=points['altitude'][0]
    coords2[...,2] = points['lat'][0]
    coords2[...,3] = points['lon'][0]
    coords2 = coords2.reshape((time_md.size,4))

    U_interped=np.squeeze(interpolator_U(coords2))
    V_interped=np.squeeze(interpolator_V(coords2))
    time_info=HGT_4D_sm.coords

    sta_graphics.draw_point_wind(U=U_interped,V=V_interped,
        model=model,
        output_dir=output_dir,
        points=points,
        time_info=time_info,
        extra_info=extra_info
            )        

def point_fcst(
        model='ECMWF',
        output_dir=None,
        t_range=[0,60],
        t_gap=3,
        points={'lon':[116.3833], 'lat':[39.9], 'altitude':[1351]},
        initTime=None,day_back=0,
        extra_info={
            'output_head_name':' ',
            'output_tail_name':' ',
            'point_name':' '}
            ,**kwargs):

    #+get all the directories needed
    try:
        dir_rqd=[utl.Cassandra_dir(data_type='surface',data_source=model,var_name='T2m'),
                        utl.Cassandra_dir(data_type='surface',data_source=model,var_name='u10m'),
                        utl.Cassandra_dir(data_type='surface',data_source=model,var_name='v10m'),
                        utl.Cassandra_dir(data_type='surface',data_source=model,var_name='RAIN'+str(t_gap).zfill(2)),
                        ]
    except KeyError:
        raise ValueError('Can not find all required directories needed')
    
    #-get all the directories needed
    if(initTime == None):
        initTime = get_latest_initTime(dir_rqd[0])
        #initTime=utl.filename_day_back_model(day_back=day_back,fhour=0)[0:8]

    directory=dir_rqd[0][0:-1]
    fhours = np.arange(t_range[0], t_range[1], t_gap)
    filenames = [initTime+'.'+str(fhour).zfill(3) for fhour in fhours]
    t2m=utl.get_model_points_gy(dir_rqd[0], filenames, points,allExists=False)
    u10m=utl.get_model_points_gy(dir_rqd[1], filenames, points,allExists=False)
    v10m=utl.get_model_points_gy(dir_rqd[2], filenames, points,allExists=False)
    rn=utl.get_model_points_gy(dir_rqd[3], filenames, points,allExists=False)
    sta_graphics.draw_point_fcst(t2m=t2m,u10m=u10m,v10m=v10m,rn=rn,
        model=model,
        output_dir=output_dir,
        points=points,
        extra_info=extra_info
            )

def point_fcst_ecgust(
        model='ECMWF',
        output_dir=None,
        t_range=[0,61],
        t_gap=3,
        points={'lon':[116.3833], 'lat':[39.9], 'altitude':[1351]},
        initTime=None,day_back=0,
        extra_info={
            'output_head_name':' ',
            'output_tail_name':' ',
            'point_name':' '}
            ,**kwargs):

    #+get all the directories needed
    try:
        dir_rqd=[utl.Cassandra_dir(data_type='surface',data_source=model,var_name='T2m'),
                        utl.Cassandra_dir(data_type='surface',data_source=model,var_name='u10m'),
                        utl.Cassandra_dir(data_type='surface',data_source=model,var_name='v10m'),
                        utl.Cassandra_dir(data_type='surface',data_source=model,var_name='RAIN'+str(t_gap).zfill(2)),
                        utl.Cassandra_dir(data_type='surface',data_source='ECMWF',var_name='10M_GUST_3H')
                        ]
    except KeyError:
        raise ValueError('Can not find all required directories needed')
    
    #-get all the directories needed
    if(initTime == None):
        initTime = get_latest_initTime(dir_rqd[0])
        initTime_ec = get_latest_initTime(dir_rqd[-1])
        #initTime=utl.filename_day_back_model(day_back=day_back,fhour=0)[0:8]

    directory=dir_rqd[0][0:-1]
    fhours = np.arange(t_range[0], t_range[1], t_gap)
    filenames = [initTime+'.'+str(fhour).zfill(3) for fhour in fhours]
    if(model == '中央气象台中短期指导'):
        fhours_ec = np.arange(t_range[0]+12, t_range[1]+12, t_gap)
    else:
        fhours_ec=fhours
    if(fhours[0]==0 and fhours_ec[0] !=0):
        fhours_ec=fhours_ec[1:]
    filenames_ec=[initTime_ec+'.'+str(fhour).zfill(3) for fhour in fhours_ec]
    t2m=utl.get_model_points_gy(dir_rqd[0], filenames, points,allExists=False)
    u10m=utl.get_model_points_gy(dir_rqd[1], filenames, points,allExists=False)
    v10m=utl.get_model_points_gy(dir_rqd[2], filenames, points,allExists=False)
    rn=utl.get_model_points_gy(dir_rqd[3], filenames, points,allExists=False)
    gust=utl.get_model_points_gy(dir_rqd[4], filenames_ec, points,allExists=False)
    wind_dir=mpcalc.wind_direction(u10m['data'].values* units.meter / units.second,v10m['data'].values* units.meter / units.second)
    u10m_ec,v10m_ec=mpcalc.wind_components(np.squeeze(gust['data'].values)* units.meter / units.second,np.squeeze(wind_dir))
    u10m['data'].values[:,0,0]=u10m_ec
    v10m['data'].values[:,0,0]=v10m_ec

    sta_graphics.draw_point_fcst(t2m=t2m,u10m=u10m,v10m=v10m,rn=rn,
        model=model,
        output_dir=output_dir,
        points=points,
        extra_info=extra_info
            )

def point_uv_tmp_rh_rn_fcst(
        model='中央气象台中短期指导',
        output_dir=None,
        t_range=[0,60],
        t_gap=3,
        points={'lon':[116.3833], 'lat':[39.9], 'altitude':[1351]},
        initTime=None,day_back=0,
        extra_info={
            'output_head_name':' ',
            'output_tail_name':' ',
            'point_name':' '}
            ,**kwargs):

    #+get all the directories needed
    try:
        dir_rqd=[utl.Cassandra_dir(data_type='surface',data_source=model,var_name='T2m'),
                        utl.Cassandra_dir(data_type='surface',data_source=model,var_name='u10m'),
                        utl.Cassandra_dir(data_type='surface',data_source=model,var_name='v10m'),
                        utl.Cassandra_dir(data_type='surface',data_source=model,var_name='rh2m'),
                        utl.Cassandra_dir(data_type='surface',data_source=model,var_name='RAIN'+str(t_gap).zfill(2))]
    except KeyError:
        raise ValueError('Can not find all required directories needed')
    
    #-get all the directories needed
    if(initTime == None):
        initTime = get_latest_initTime(dir_rqd[0])
        #initTime=utl.filename_day_back_model(day_back=day_back,fhour=0)[0:8]

    directory=dir_rqd[0][0:-1]
    fhours = np.arange(t_range[0], t_range[1], t_gap)
    filenames = [initTime+'.'+str(fhour).zfill(3) for fhour in fhours]
    t2m=utl.get_model_points_gy(dir_rqd[0], filenames, points,allExists=False)
    u10m=utl.get_model_points_gy(dir_rqd[1], filenames, points,allExists=False)
    v10m=utl.get_model_points_gy(dir_rqd[2], filenames, points,allExists=False)
    rh=utl.get_model_points_gy(dir_rqd[3], filenames, points,allExists=False)
    rn=utl.get_model_points_gy(dir_rqd[4], filenames, points,allExists=False)
    sta_graphics.draw_point_uv_tmp_rh_rn_fcst(t2m=t2m,u10m=u10m,v10m=v10m,rh=rh,rn=rn,
        model=model,
        output_dir=output_dir,
        points=points,
        extra_info=extra_info
            )



def point_fcst_according_to_3D_field(
        model='ECMWF',
        output_dir=None,
        t_range=[0,60],
        t_gap=3,
        points={'lon':[116.3833], 'lat':[39.9], 'altitude':[1351]},
        initTime=None,obs_ID=54511,day_back=0,
        extra_info={
            'output_head_name':' ',
            'output_tail_name':' ',
            'point_name':' ',
            'drw_thr':True,
            'levels_for_interp':[1000, 950, 925, 900, 850, 800, 700, 600, 500]}
            ,**kwargs):

    try:
        dir_rqd=[utl.Cassandra_dir(data_type='high',data_source=model,var_name='HGT',lvl=''),
                        utl.Cassandra_dir(data_type='high',data_source=model,var_name='UGRD',lvl=''),
                        utl.Cassandra_dir(data_type='high',data_source=model,var_name='VGRD',lvl=''),
                        utl.Cassandra_dir(data_type='high',data_source=model,var_name='TMP',lvl=''),
                        utl.Cassandra_dir(data_type='surface',data_source=model,var_name='RAIN'+str(t_gap).zfill(2))]
    except KeyError:
        raise ValueError('Can not find all required directories needed')
    
    #-get all the directories needed
    if(initTime == None):
        initTime = get_latest_initTime(dir_rqd[0][0:-1]+'/850')
        #initTime=utl.filename_day_back_model(day_back=day_back,fhour=0)[0:8]

    directory=dir_rqd[0][0:-1]

    if(t_range[1] > 72):
        fhours = np.append(np.arange(t_range[0], 72, t_gap),np.arange(72,t_range[1],6))
    else:
        fhours = np.arange(t_range[0], t_range[1], t_gap)

    filenames = [initTime+'.'+str(fhour).zfill(3) for fhour in fhours]
    HGT_4D=get_model_3D_grids(directory=directory,filenames=filenames,levels=extra_info['levels_for_interp'], allExists=False)
    directory=dir_rqd[1][0:-1]
    U_4D=get_model_3D_grids(directory=directory,filenames=filenames,levels=extra_info['levels_for_interp'], allExists=False)
    directory=dir_rqd[2][0:-1]
    V_4D=get_model_3D_grids(directory=directory,filenames=filenames,levels=extra_info['levels_for_interp'], allExists=False)

    directory=dir_rqd[3][0:-1]
    TMP_4D=get_model_3D_grids(directory=directory,filenames=filenames,levels=extra_info['levels_for_interp'], allExists=False)
    
    rn=utl.get_model_points_gy(dir_rqd[4], filenames, points,allExists=False)

    directory=dir_rqd[3][0:-1]
    coords_info_2D=utl.get_model_points_gy(directory+str(extra_info['levels_for_interp'][0])+'/',
                        points=points,filenames=filenames,allExists=False)

    delt_xy=HGT_4D['lon'].values[1]-HGT_4D['lon'].values[0]
    mask = (HGT_4D['lon']<(points['lon']+2*delt_xy))&(HGT_4D['lon']>(points['lon']-2*delt_xy))&(HGT_4D['lat']<(points['lat']+2*delt_xy))&(HGT_4D['lat']>(points['lat']-2*delt_xy))

    HGT_4D_sm=HGT_4D['data'].where(mask,drop=True)
    U_4D_sm=U_4D['data'].where(mask,drop=True)
    V_4D_sm=V_4D['data'].where(mask,drop=True)
    TMP_4D_sm=TMP_4D['data'].where(mask,drop=True)

    lon_md=np.squeeze(HGT_4D_sm['lon'].values)
    lat_md=np.squeeze(HGT_4D_sm['lat'].values)
    alt_md=np.squeeze(HGT_4D_sm.values*10).flatten()
    time_md=np.squeeze(HGT_4D_sm['forecast_period'].values)

    coords = np.zeros((len(time_md),len(extra_info['levels_for_interp']),len(lat_md),len(lon_md),4))
    coords[...,0]=time_md.reshape((len(time_md),1,1,1))
    coords[...,2] = lat_md.reshape((1,1,len(lat_md),1))
    coords[...,3] = lon_md.reshape((1,1,1,len(lon_md)))
    coords = coords.reshape((alt_md.size,4))
    coords[:,1]=alt_md

    interpolator_U = LinearNDInterpolator(coords,U_4D_sm.values.reshape((U_4D_sm.values.size)),rescale=True)
    interpolator_V = LinearNDInterpolator(coords,V_4D_sm.values.reshape((V_4D_sm.values.size)),rescale=True)
    interpolator_TMP = LinearNDInterpolator(coords,TMP_4D_sm.values.reshape((TMP_4D_sm.values.size)),rescale=True)

    coords2 = np.zeros((len(time_md),1,1,1,4))
    coords2[...,0]=time_md.reshape((len(time_md),1,1,1))
    coords2[...,1]=points['altitude'][0]
    coords2[...,2] = points['lat'][0]
    coords2[...,3] = points['lon'][0]
    coords2 = coords2.reshape((time_md.size,4))

    U_interped=np.squeeze(interpolator_U(coords2))
    V_interped=np.squeeze(interpolator_V(coords2))
    TMP_interped=np.squeeze(interpolator_TMP(coords2))

    U_interped_xr=coords_info_2D.copy()
    U_interped_xr['data'].values=U_interped.reshape(U_interped.size,1,1)
    V_interped_xr=coords_info_2D.copy()
    V_interped_xr['data'].values=V_interped.reshape(V_interped.size,1,1)
    TMP_interped_xr=coords_info_2D.copy()
    TMP_interped_xr['data'].values=TMP_interped.reshape(TMP_interped.size,1,1)
    
    sta_graphics.draw_point_fcst(t2m=TMP_interped_xr,u10m=U_interped_xr,v10m=V_interped_xr,rn=rn,
        model=model,
        output_dir=output_dir,
        points=points,
        extra_info=extra_info
            )

def point_uv_rh_fcst_according_to_3D_field(
        model='ECMWF',
        output_dir=None,
        t_range=[0,60],
        t_gap=3,
        points={'lon':[116.3833], 'lat':[39.9], 'altitude':[1351]},
        initTime=None,obs_ID=54511,day_back=0,
        extra_info={
            'output_head_name':' ',
            'output_tail_name':' ',
            'point_name':' ',
            'drw_thr':True,
            'levels_for_interp':[1000, 950, 925, 900, 850, 800, 700, 600, 500]}
            ,**kwargs):

    try:
        if(t_range[1] > 72 ):
            t_gap_r=6
        else:
            t_gap_r=3
        dir_rqd=[utl.Cassandra_dir(data_type='high',data_source=model,var_name='HGT',lvl=''),
                        utl.Cassandra_dir(data_type='high',data_source=model,var_name='UGRD',lvl=''),
                        utl.Cassandra_dir(data_type='high',data_source=model,var_name='VGRD',lvl=''),
                        utl.Cassandra_dir(data_type='high',data_source=model,var_name='RH',lvl=''),
                        utl.Cassandra_dir(data_type='surface',data_source=model,var_name='RAIN'+str(t_gap_r).zfill(2))]
    except KeyError:
        raise ValueError('Can not find all required directories needed')
    
    #-get all the directories needed
    if(initTime == None):
        initTime = get_latest_initTime(dir_rqd[0][0:-1]+'/850')
        #initTime=utl.filename_day_back_model(day_back=day_back,fhour=0)[0:8]

    directory=dir_rqd[0][0:-1]

    if(t_range[1] > 72):
        fhours = np.append(np.arange(t_range[0], 72, t_gap),np.arange(72,241,6))
    else:
        fhours = np.arange(t_range[0], t_range[1], t_gap)

    filenames = [initTime+'.'+str(fhour).zfill(3) for fhour in fhours]
    HGT_4D=get_model_3D_grids(directory=directory,filenames=filenames,levels=extra_info['levels_for_interp'], allExists=False)
    directory=dir_rqd[1][0:-1]
    U_4D=get_model_3D_grids(directory=directory,filenames=filenames,levels=extra_info['levels_for_interp'], allExists=False)
    directory=dir_rqd[2][0:-1]
    V_4D=get_model_3D_grids(directory=directory,filenames=filenames,levels=extra_info['levels_for_interp'], allExists=False)

    directory=dir_rqd[3][0:-1]
    RH_4D=get_model_3D_grids(directory=directory,filenames=filenames,levels=extra_info['levels_for_interp'], allExists=False)
    
    rn=utl.get_model_points_gy(dir_rqd[4], filenames, points,allExists=False)

    directory=dir_rqd[3][0:-1]
    coords_info_2D=utl.get_model_points_gy(directory+str(extra_info['levels_for_interp'][0])+'/',
                        points=points,filenames=filenames,allExists=False)

    delt_xy=HGT_4D['lon'].values[1]-HGT_4D['lon'].values[0]
    mask = (HGT_4D['lon']<(points['lon']+2*delt_xy))&(HGT_4D['lon']>(points['lon']-2*delt_xy))&(HGT_4D['lat']<(points['lat']+2*delt_xy))&(HGT_4D['lat']>(points['lat']-2*delt_xy))

    HGT_4D_sm=HGT_4D['data'].where(mask,drop=True)
    U_4D_sm=U_4D['data'].where(mask,drop=True)
    V_4D_sm=V_4D['data'].where(mask,drop=True)
    RH_4D_sm=RH_4D['data'].where(mask,drop=True)

    lon_md=np.squeeze(HGT_4D_sm['lon'].values)
    lat_md=np.squeeze(HGT_4D_sm['lat'].values)
    alt_md=np.squeeze(HGT_4D_sm.values*10).flatten()
    time_md=np.squeeze(HGT_4D_sm['forecast_period'].values)

    coords = np.zeros((len(time_md),len(extra_info['levels_for_interp']),len(lat_md),len(lon_md),4))
    coords[...,0]=time_md.reshape((len(time_md),1,1,1))
    coords[...,2] = lat_md.reshape((1,1,len(lat_md),1))
    coords[...,3] = lon_md.reshape((1,1,1,len(lon_md)))
    coords = coords.reshape((alt_md.size,4))
    coords[:,1]=alt_md

    interpolator_U = LinearNDInterpolator(coords,U_4D_sm.values.reshape((U_4D_sm.values.size)),rescale=True)
    interpolator_V = LinearNDInterpolator(coords,V_4D_sm.values.reshape((V_4D_sm.values.size)),rescale=True)
    interpolator_RH = LinearNDInterpolator(coords,RH_4D_sm.values.reshape((RH_4D_sm.values.size)),rescale=True)

    coords2 = np.zeros((len(time_md),1,1,1,4))
    coords2[...,0]=time_md.reshape((len(time_md),1,1,1))
    coords2[...,1]=points['altitude'][0]
    coords2[...,2] = points['lat'][0]
    coords2[...,3] = points['lon'][0]
    coords2 = coords2.reshape((time_md.size,4))

    U_interped=np.squeeze(interpolator_U(coords2))
    V_interped=np.squeeze(interpolator_V(coords2))
    RH_interped=np.squeeze(interpolator_RH(coords2))

    U_interped_xr=coords_info_2D.copy()
    U_interped_xr['data'].values=U_interped.reshape(U_interped.size,1,1)
    V_interped_xr=coords_info_2D.copy()
    V_interped_xr['data'].values=V_interped.reshape(V_interped.size,1,1)
    RH_interped_xr=coords_info_2D.copy()
    RH_interped_xr['data'].values=RH_interped.reshape(RH_interped.size,1,1)
    
    sta_graphics.draw_point_uv_rh_fcst(rh2m=RH_interped_xr,u10m=U_interped_xr,v10m=V_interped_xr,rn=rn,
        model=model,
        output_dir=output_dir,
        points=points,
        extra_info=extra_info
            )                    

def point_fcst_according_to_3D_field_VS_zd_plot(
        model='ECMWF',
        output_dir=None,
        t_range=[0,60],
        t_gap=3,
        points={'lon':[116.3833], 'lat':[39.9], 'altitude':[1351]},
        initTime=None,obs_ID=54511,day_back=0,
        extra_info={
            'output_head_name':' ',
            'output_tail_name':' ',
            'point_name':' ',
            'drw_thr':True,
            'levels_for_interp':[1000, 950, 925, 900, 850, 800, 700, 600, 500]}
            ,**kwargs):

    try:
        dir_rqd=[utl.Cassandra_dir(data_type='high',data_source=model,var_name='HGT',lvl=''),
                        utl.Cassandra_dir(data_type='high',data_source=model,var_name='UGRD',lvl=''),
                        utl.Cassandra_dir(data_type='high',data_source=model,var_name='VGRD',lvl=''),
                        utl.Cassandra_dir(data_type='high',data_source=model,var_name='TMP',lvl=''),
                        utl.Cassandra_dir(data_type='surface',data_source=model,var_name='RAIN'+str(t_gap).zfill(2)),
                        utl.Cassandra_dir(data_type='surface',data_source='OBS',var_name='PLOT_ALL'),
                        utl.Cassandra_dir(data_type='surface',data_source='OBS',var_name='RAIN'+str(t_gap).zfill(2)+'_ALL')]
    except KeyError:
        raise ValueError('Can not find all required directories needed')
    
    #-get all the directories needed
    if(initTime == None):
        initTime = get_latest_initTime(dir_rqd[0][0:-1]+'/850')
        #initTime=utl.filename_day_back_model(day_back=day_back,fhour=0)[0:8]

    directory=dir_rqd[0][0:-1]

    if(t_range[1] > 72):
        fhours = np.append(np.arange(t_range[0], 72, t_gap),np.arange(72,t_range[1],6))
    else:
        fhours = np.arange(t_range[0], t_range[1], t_gap)

    filenames = [initTime+'.'+str(fhour).zfill(3) for fhour in fhours]
    filenames_obs= [(datetime.strptime('20'+initTime,'%Y%m%d%H')+timedelta(hours=int(fhour))).strftime('%Y%m%d%H')+'0000.000' for fhour in np.arange(0,fhours[-1])]
    HGT_4D=get_model_3D_grids(directory=directory,filenames=filenames,levels=extra_info['levels_for_interp'], allExists=False)
    directory=dir_rqd[1][0:-1]
    U_4D=get_model_3D_grids(directory=directory,filenames=filenames,levels=extra_info['levels_for_interp'], allExists=False)
    directory=dir_rqd[2][0:-1]
    V_4D=get_model_3D_grids(directory=directory,filenames=filenames,levels=extra_info['levels_for_interp'], allExists=False)

    directory=dir_rqd[3][0:-1]
    TMP_4D=get_model_3D_grids(directory=directory,filenames=filenames,levels=extra_info['levels_for_interp'], allExists=False)
    
    rn=utl.get_model_points_gy(dir_rqd[4], filenames, points,allExists=False)

    directory=dir_rqd[3][0:-1]
    coords_info_2D=utl.get_model_points_gy(directory+str(extra_info['levels_for_interp'][0])+'/',
                        points=points,filenames=filenames,allExists=False)

    dataset_obs = []
    for filename in filenames_obs:
        try:
            obs_1h= MICAPS_IO.get_station_data(dir_rqd[5], filename=filename)
            #obs_r_6h=MICAPS_IO.get_station_data(dir_rqd[6], filename=filename)
        except:
            continue
        dataset_obs.append(obs_1h[obs_1h['ID']==obs_ID])
        #dataset_obs_r.append(obs_r_6h[obs_r_6h['ID']==obs_ID])
    obs_all=pd.concat(dataset_obs).reset_index(drop=True)
    
    dataset_obs_r=[]
    time_obs_r=[]
    for idx in range(6,len(obs_all['Rain_1h']),t_gap):
        dataset_obs_r.append(sum(obs_all['Rain_1h'][idx-5:idx+1].dropna()))
        time_obs_r.append(obs_all['time'][idx])
    
    obs_r=pd.DataFrame({
                        'Rain':dataset_obs_r,
                        'time':time_obs_r
                        })

    delt_xy=HGT_4D['lon'].values[1]-HGT_4D['lon'].values[0]
    mask = (HGT_4D['lon']<(points['lon']+2*delt_xy))&(HGT_4D['lon']>(points['lon']-2*delt_xy))&(HGT_4D['lat']<(points['lat']+2*delt_xy))&(HGT_4D['lat']>(points['lat']-2*delt_xy))

    HGT_4D_sm=HGT_4D['data'].where(mask,drop=True)
    U_4D_sm=U_4D['data'].where(mask,drop=True)
    V_4D_sm=V_4D['data'].where(mask,drop=True)
    TMP_4D_sm=TMP_4D['data'].where(mask,drop=True)

    lon_md=np.squeeze(HGT_4D_sm['lon'].values)
    lat_md=np.squeeze(HGT_4D_sm['lat'].values)
    alt_md=np.squeeze(HGT_4D_sm.values*10).flatten()
    time_md=np.squeeze(HGT_4D_sm['forecast_period'].values)

    coords = np.zeros((len(time_md),len(extra_info['levels_for_interp']),len(lat_md),len(lon_md),4))
    coords[...,0]=time_md.reshape((len(time_md),1,1,1))
    coords[...,2] = lat_md.reshape((1,1,len(lat_md),1))
    coords[...,3] = lon_md.reshape((1,1,1,len(lon_md)))
    coords = coords.reshape((alt_md.size,4))
    coords[:,1]=alt_md

    interpolator_U = LinearNDInterpolator(coords,U_4D_sm.values.reshape((U_4D_sm.values.size)),rescale=True)
    interpolator_V = LinearNDInterpolator(coords,V_4D_sm.values.reshape((V_4D_sm.values.size)),rescale=True)
    interpolator_TMP = LinearNDInterpolator(coords,TMP_4D_sm.values.reshape((TMP_4D_sm.values.size)),rescale=True)

    coords2 = np.zeros((len(time_md),1,1,1,4))
    coords2[...,0]=time_md.reshape((len(time_md),1,1,1))
    coords2[...,1]=points['altitude'][0]
    coords2[...,2] = points['lat'][0]
    coords2[...,3] = points['lon'][0]
    coords2 = coords2.reshape((time_md.size,4))

    U_interped=np.squeeze(interpolator_U(coords2))
    V_interped=np.squeeze(interpolator_V(coords2))
    TMP_interped=np.squeeze(interpolator_TMP(coords2))

    U_interped_xr=coords_info_2D.copy()
    U_interped_xr['data'].values=U_interped.reshape(U_interped.size,1,1)
    V_interped_xr=coords_info_2D.copy()
    V_interped_xr['data'].values=V_interped.reshape(V_interped.size,1,1)
    TMP_interped_xr=coords_info_2D.copy()
    TMP_interped_xr['data'].values=TMP_interped.reshape(TMP_interped.size,1,1)
    
    sta_graphics.draw_point_fcst_VS_obs(t2m=TMP_interped_xr,u10m=U_interped_xr,v10m=V_interped_xr,rn=rn,
        obs_all=obs_all,obs_r=obs_r,
        model=model,
        output_dir=output_dir,
        points=points,
        extra_info=extra_info
            )
