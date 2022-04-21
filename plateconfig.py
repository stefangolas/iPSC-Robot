# -*- coding: utf-8 -*-
"""
Created on Sun Mar  6 01:15:48 2022

@author: stefa
"""

from ipsc_utils import (Plate6_2chAI, RgntResAI, MediaRepAI, Plate6, aspirate, dispense, 
                        LayoutManager, layout_item, Tip96, Plate96, Plate24)

PlateConfigDict = {
    "6 Well Plate   Greiner":{
        
        'labware_tilted':'AllnInst_6_2ch_clear_tilt_10degrees_0001',
        'Tilt1':'Tilt1_6',
        'Tilt1_lid':'Tilt1_6_lid',
        'TiltPark1':'TiltPark1_6',
        'CytC24':'CytC24_6wp',
        'Cyt6000' : 'Cyt6000_6wp',
        'Scanner' : 'Scanner_6wp',
        'Lids':'Tilt1_6_lid',
        'Lids_Park':'TiltPark1_6',
        'PlateParkPositions' : 'Plates_6',
        'gripHeight':10,
        'gripWidth':84,
        'openWidth':90,
        'gripHeight_lid':6,
        'volume':1000,
        'LabwareClass': Plate6,
        'TiltedClass':Plate6_2chAI,
        'Dispense_Sites':12,
        'Dispense_Sites_per_Column':4,
        },
    
    '96 Well Plate   CellVis':{
        'Tilt1':'Tilt1_96',
        'Tilt1_lid':'Tilt1_96_lid',
        'TiltPark1':'TiltPark1_96',
        'CytC24':'CytC24_96wp',
        'Cyt6000' : 'Cyt6000_96wp',
        'Scanner' : 'Scanner_96wp',
        'Lids':'Tilt1_96_lid',
        'Lids_Park':'TiltPark1_96',
        'PlateParkPositions' : 'Plates_96',
        'gripHeight':11,
        'gripWidth':84,
        'openWidth':90,
        'gripHeight_lid':4,
        'volume':300,
        'LabwareClass': Plate96,
        'volume_asp_smt' : 1000,
        'volume_disp_smt' : 100,
        'loopNumber_multiDisp_smt' : 10,
        'asp_disp_cycles_smt' : 1,
        'channelPattern_smt' : 11111100,
        'CeligoHandoff' : 'CeligoHandoff_96',
        'ReaderHandoff' : 'ReaderHandoff_96',
        'celigoVendor' : 'In vitro Scientific',
        'celigoAnalysisSettings' : 'IVS_96W_Confluence',
        'celigoScanSettings' : 'IVS_96W_Confluence',
        'celigoPltTypeID':'96-Well In Vitro Scientific P96-1.5H-N Plate',
        }
    
    }

