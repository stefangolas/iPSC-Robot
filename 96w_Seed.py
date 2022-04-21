# -*- coding: utf-8 -*-
"""
Created on Fri Mar 19 08:59:12 2021

@author: stefa
"""
import importlib
import sys
import os
import time

from ipsc_utils import (initialize, Plate6_2chAI, RgntResAI, MediaRepAI, 
                        Plate6, aspirate, dispense, LAYFILE, LayoutManager,
                        layout_item, Tip96, Plate96, Plate24, tip_pick_up, get_plate_gripper,
                        move_plate_gripper, barcode_initialize, barcode_read, move_sequence,
                        place_plate_gripper, slow_iswap_firmware, normal_iswap_firmware, 
                        iswap_move_portrait_grip, get_plate_gripper_seq, move_plate_gripper_seq, 
                        place_plate_gripper_seq, resource_list_with_prefix, aspirate_cLLD, tip_eject, tilt_module_init,
                        tilt_module_set_pos, initialize_tec, set_target_tec, start_control_tec ,move_plate, BC_READ, Cytomat)


from pyhamilton import HamiltonInterface


this_file_dir = os.path.dirname(os.path.abspath(__file__))
allen_inst_dir = os.path.abspath(os.path.join(this_file_dir, '..', '..',))
cytomat_path = os.path.join(allen_inst_dir, 'Equipment', 'Cytomat')

print(cytomat_path)


lay_mgr = LayoutManager(LAYFILE)


PlateConfigDict={
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

        }
    
    }

barcode = None #placeholder
plate_type = "96 Well Plate   CellVis"

#Get plate and sequence IDs
Tilted_Labware = layout_item(lay_mgr, PlateConfigDict[plate_type]['TiltedClass'], PlateConfigDict[plate_type]['labware_tilted'])
Tilt1 = layout_item(lay_mgr, PlateConfigDict[plate_type]['LabwareClass'], PlateConfigDict[plate_type]['Tilt1'])
Tilt1_lid = PlateConfigDict[plate_type]['Tilt1_lid']
TiltPark1 = PlateConfigDict[plate_type]['TiltPark1']
CytC24 = layout_item(lay_mgr, PlateConfigDict[plate_type]['LabwareClass'], PlateConfigDict[plate_type]['CytC24'])
Cyt6000 = layout_item(lay_mgr, PlateConfigDict[plate_type]['LabwareClass'], PlateConfigDict[plate_type]['Cyt6000'])
PlateParks = layout_item(lay_mgr, PlateConfigDict[plate_type]['LabwareClass'], PlateConfigDict[plate_type]['PlateParkPosition'])
Tilt1_96_tilted = layout_item(lay_mgr, Plate96, 'Tilt1_96_tilted')


Lids = PlateConfigDict[plate_type]['Tilt1_lid']
Lids_Park = PlateConfigDict[plate_type]['TiltPark1']

#Get grip parameters
gripHeight = PlateConfigDict[plate_type]['gripHeight']
gripWidth = PlateConfigDict[plate_type]['gripWidth']
openWidth = PlateConfigDict[plate_type]['openWidth']
gripHeight_lid = PlateConfigDict[plate_type]['gripHeight_lid']

#Get volume and dispense sites
well_vol = PlateConfigDict[plate_type]['volume']
num_wells = PlateConfigDict[plate_type]['Dispense_Sites']
wells_per_col = PlateConfigDict[plate_type]['Dispense_Sites_per_Column']

Media=layout_item(lay_mgr, MediaRepAI, 'MediaFill1')
MediaPltWaste=layout_item(lay_mgr, MediaRepAI, 'MediaRep_0014')
MediaTrough = layout_item(lay_mgr, MediaRepAI, 'MediaRep_0007')
MediaTrough2 = layout_item(lay_mgr, MediaRepAI, 'Ham_DW_Rgt_L_0002')
Media_Warm = layout_item(lay_mgr, MediaRepAI, 'MediaRep_0010')
Media_Warm_1 = layout_item(lay_mgr, MediaRepAI, 'MediaRep_0013')
MediaRep2 = layout_item(lay_mgr, MediaRepAI, 'MediaRep2')
MedTrough2=layout_item(lay_mgr, MediaRepAI, 'MediaRep_0004')


DW24wSample = layout_item(lay_mgr, MediaRepAI, 'MediaRep_0016')
AI_24w_Place = layout_item(lay_mgr, MediaRepAI, 'AI_24DW_Place')

AI_24w_DW = layout_item(lay_mgr, Plate24, 'AI_24w_DeepWell')


CPAC_6 = layout_item(lay_mgr, Plate6, 'CPAC_6')

AI_24w_DeepWell = layout_item(lay_mgr, Plate24, 'AI_24w_DeepWell_0003')

Liquid_Waste = layout_item(lay_mgr, RgntResAI, 'LiquidWaste')

MatrigelL = layout_item(lay_mgr, MediaRepAI, 'MatrigelL')
MatrigelR = layout_item(lay_mgr, MediaRepAI, 'MatrigelR')

Mtesr_RI = layout_item(lay_mgr, MediaRepAI, 'Mtesr_RI')
Mtesr_RImix = layout_item(lay_mgr, MediaRepAI, 'Mtesr_RImix')

CPAC_6_2ch = layout_item(lay_mgr, Plate6_2chAI, 'Mtesr_RImix')

scanner_seq = PlateConfigDict[plate_type]['Scanner']

CytC24_6wp = layout_item(lay_mgr, Plate6, 'CytC24_6wp')

Scanner_24wp = layout_item(lay_mgr, Plate24, 'Scanner_24wp')

Plates_6w = resource_list_with_prefix(lay_mgr, 'Plate_6_', Plate6, 5)

CPAC_96screen = layout_item(lay_mgr, Plate96, 'CPAC_96screen')



simulation_on = '--simulate' in sys.argv

def barcode_read(ham_int):
    cid = ham_int.send_command(BC_READ)
    response=ham_int.wait_on_response(cid, raise_first_exception=True, timeout=120)
    return response

def barcode_read_with_core_paddles(pickupSeq, scannerLocation, dropoffLocation, gripHeight, gripWidth, openWidth):
    get_plate_gripper_seq(ham_int, pickupSeq, gripHeight, gripWidth, openWidth)
    move_plate_gripper_seq(ham_int, scannerLocation)
    print('moved')
    #barcode=barcode_read(ham_int)
    barcode=""
    #while barcode is "":
        #move_sequence(scannerLocation, zDisplacement=20)
        #move_plate_gripper(ham_int, scannerLocation)
        #move_sequence(scannerLocation, zDisplacement=-20)
    move_plate_gripper_seq(ham_int,'Scanner_24wp_01')
    cid = ham_int.send_command(BC_READ)
    barcode = ham_int.wait_on_response(cid, raise_first_exception=True, timeout=120, return_data='step-return1')
    print(barcode)
    print("finished wait on response")
    barcode=int(barcode)
    print(barcode)
    move_plate_gripper_seq(ham_int,'Scanner_24wp')      
    place_plate_gripper_seq(ham_int, dropoffLocation)
    return barcode


tip_boxes_str_list=['HTF_L_0001', 'HTF_L_0002', 'HTF_L_0003', 'HTF_L_0004', 'HTF_L_0005']

#tip_boxes_str_list=['ST_L_NE_stack_0006_0004', 'ST_L_NE_stack_0007_0004', 'ST_L_NE_stack_0008_0004', 'ST_L_NE_stack_0009_0004', 'ST_L_NE_stack_0010_0004']
tip_boxes_list = [layout_item(lay_mgr, Tip96, tip_box_str) for tip_box_str in tip_boxes_str_list]
tips_list=[[(tips,tip) for tip in range(8*i,8*i+8)] for tips in tip_boxes_list for i in range(12)]
tips_iter=iter(tips_list)
park_positions = iter(PlateParks)

with HamiltonInterface(simulate=simulation_on) as ham_int, Cytomat(comPort='COM5', cytomatType='C24', num_slots=205, db='CytomatC24.mdb') as Cytomat24, Cytomat(comPort='COM6', cytomatType='C6000', num_slots=125, db='CytomatC6002.mdb') as Cytomat6000:
    
    initialize(ham_int)
    
    slot_number = 181
    
    num_plates = 2
    
    #bc_from_worklist = None #Get from work-list
    
    for plate in range(num_plates):
    
        Cytomat24.get_plate_by_range(181, 12)
    
        iswap_move_portrait_grip(ham_int, CytC24, Tilt1)
    
        barcode96 = barcode_read_with_core_paddles('Tilt1_96_lid', scanner_seq, 'TiltPark1_96', 4, gripWidth, openWidth)
    
        tilt_module_init(ham_int, "T1", 4, 1, 0)
        
        current_tips = next(tips_iter)
        tip_pick_up(ham_int, current_tips)
        
        for col_idx in range(1,11):
            asp_pos_range = range(col_idx*8+1, col_idx*8+7)
            asp_poss = [(Tilt1_96_tilted, pos) for pos in asp_pos_range] + [None]*2
            vols = [100]*6 + [None]*2
            aspirate(ham_int, asp_poss, vols)
        
        vols = [1000]*6+[None]*2
        disp_poss = [(Liquid_Waste, x) for x in range(8)]
        dispense(ham_int, Liquid_Waste, vols)
        tip_eject(ham_int)
        
        tilt_module_set_pos(ham_int, "T1", 0)
        
        asp_poss = [(AI_24w_DW, pos) for pos in range(12,18)] + [None]*2
        vols = [1000]*6 + [None]*2
        aspirate(ham_int, asp_poss, vols)
        dispense(ham_int, asp_poss, vols)
        aspirate(ham_int, asp_poss, vols)
        
        for col_idx in range(1,11):
            disp_pos_range = range(col_idx*8+1, col_idx*8+7)
            disp_poss = [(Tilt1, pos) for pos in disp_pos_range] + [None]*2
            vols = [100]*6 + [None]*2
            dispense(ham_int, disp_poss, vols)
        
        get_plate_gripper(ham_int, 'TiltPark1_96', gripHeight_lid, gripWidth, openWidth)
         
        place_plate_gripper(ham_int, 'Tilt1_96_lid')

        iswap_move_portrait_grip(ham_int, Tilt1, CytC24)
        
        cytomat_plate_position = 3
        iteration = 0
        success = False
        while success == False and iteration < 12:
            try:
                Cytomat24.store_plate_by_position(cytomat_plate_position+iteration)
                success = True
            except:
                iteration +=1
                pass