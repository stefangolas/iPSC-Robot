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
                        tilt_module_set_pos, process_worklist_for_method, initialize_tec, set_target_tec, start_control_tec ,move_plate, BC_READ, Cytomat)


from pyhamilton import HamiltonInterface


this_file_dir = os.path.dirname(os.path.abspath(__file__))
allen_inst_dir = os.path.abspath(os.path.join(this_file_dir, '..', '..',))
cytomat_path = os.path.join(allen_inst_dir, 'Equipment', 'Cytomat')

print(cytomat_path)


lay_mgr = LayoutManager(LAYFILE)


from plateconfig import PlateConfigDict


def deck_resource_from_config(plate_type, resource_key):
    deck_res = layout_item(lay_mgr, PlateConfigDict[plate_type]['LabwareClass'], PlateConfigDict[plate_type][resource_key])
    return deck_res

barcode, plate_type = process_worklist_for_method("C:\\Users\\BenG\\Desktop\\Scan\\")
barcode = None #placeholder
plate_type = "6 Well Plate   Greiner"

#Get plate and sequence IDs
Tilted_Labware = layout_item(lay_mgr, PlateConfigDict[plate_type]['TiltedClass'], PlateConfigDict[plate_type]['labware_tilted'])
Tilt1 = deck_resource_from_config(plate_type, 'Tilt1')
Tilt1_lid = PlateConfigDict[plate_type]['Tilt1_lid']
TiltPark1 = PlateConfigDict[plate_type]['TiltPark1']
CytC24 = deck_resource_from_config(plate_type, 'CytC24')
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
MediaTrough=layout_item(lay_mgr, MediaRepAI, 'MediaRep_0007')
Media_Warm=layout_item(lay_mgr, MediaRepAI, 'MediaRep_0010')
Liquid_Waste = layout_item(lay_mgr, RgntResAI, 'LiquidWaste')


Scanner_24wp=layout_item(lay_mgr, Plate24, 'Scanner_24wp')


simulation_on = '--simulate' in sys.argv


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

tip_boxes_list = [layout_item(lay_mgr, Tip96, tip_box_str) for tip_box_str in tip_boxes_str_list]
tips_list=[[(tips,tip) for tip in range(8*i,8*i+8)] for tips in tip_boxes_list for i in range(12)]
tips_iter=iter(tips_list)

def get_media_from_incubator():
    
    try:
        tip_eject(ham_int, current_tips)
    except:
        pass
    
    tilt_module_set_pos(ham_int, "T1", 10)
    
    get_plate_gripper_seq(ham_int, Lids_Park, 5, 84, 87)
    place_plate_gripper_seq(ham_int, Lids, 5, 84, 87)
        
    get_plate_gripper_seq(ham_int, 'MediaRep2_Lid') #Add grip parameters
    place_plate_gripper_seq(ham_int, 'MediaRep_Cover')
    
    initialize_tec(ham_int, '0')
    set_target_tec(ham_int, 37.0, '0', '2')
    start_control_tec(ham_int, '0', '2')
    time.sleep(30)
        
    find_media_counter=0
    media_site=106
        
    while find_media_counter<5:
        try:
            Cytomat6000.get_plate_by_position(media_site)
            break
        except:
            media_site+=1
            find_media_counter+=1
            pass
        
    slow_iswap_firmware(ham_int)
    move_plate(ham_int, Media, MediaPltWaste, 3, 82, 0, 90)
    move_plate(ham_int, MediaTrough, Media_Warm, 3, 82, 0, 90)
    tilt_module_init(ham_int, "T1", 4, 1, 0)
    tilt_module_set_pos(ham_int, "T1", 10)
    normal_iswap_firmware(ham_int)

with HamiltonInterface(simulate=simulation_on) as ham_int, Cytomat(comPort='COM5', cytomatType='C24', num_slots=205, db='CytomatC24.mdb') as Cytomat24, Cytomat(comPort='COM6', cytomatType='C6000', num_slots=125, db='CytomatC6002.mdb') as Cytomat6000:
    
    initialize(ham_int)
    
    #Get iPSC plate from Cytomat and place on deck
    Cytomat24.get_plate_by_barcode(barcode)
    slow_iswap_firmware(ham_int) #Slow gripper with firmware commands
    iswap_move_portrait_grip(ham_int, CytC24, Tilt1) #Move plate from CytC24 to Tilt1 position with gripper
    normal_iswap_firmware(ham_int) #Return gripper to normal speed with firmware commands
    
    #Scan iPSC plate barcode and place in TiltPark1
    barcode_initialize(ham_int, "COM10")
    scanned_barcode=barcode_read_with_core_paddles('MediaRep_Cover', 'Scanner_24wp', 'MediaRep2_Lid', 5, 84, 87)
    get_plate_gripper_seq(ham_int, Lids, 5, 84, 87)
    place_plate_gripper_seq(ham_int, TiltPark1)

    
    
    media_exchange_liquid_class="Allen_MediaChange_MediaRemoval_HVF_Water_AliquotDispenseJet_Part"

    tilt_module_set_pos(ham_int, "T1", 10)
    
    
    
    
    for dispense_cycle in range(num_wells//wells_per_col):
        current_tips = next(tips_iter)
        tip_pick_up(ham_int, current_tips)
        
        plate_pos_range = range(dispense_cycle*wells_per_col, dispense_cycle*wells_per_col+wells_per_col)
        
        media_poss = [None]*(8-wells_per_col)+[(Media, pos) for pos in range(wells_per_col)]
        media_vols = [None]*(8-wells_per_col)+[well_vol]*wells_per_col
    
        plate_vols = [well_vol]*wells_per_col+[None]*(8-wells_per_col)
        plate_poss_asp = [(Tilted_Labware, pos) for pos in plate_pos_range]+[None]*(8-wells_per_col)
        plate_poss_disp = [None]*(8-wells_per_col)+[(Tilted_Labware, pos) for pos in plate_pos_range]
        
        liq_waste_poss = [(Liquid_Waste, pos) for pos in range(wells_per_col)]+[None]*(8-wells_per_col)
        
        try:
            aspirate_cLLD(ham_int, media_poss, media_vols, liquidClass=media_exchange_liquid_class)
        except:
            get_media_from_incubator()
            tip_pick_up(ham_int, current_tips)

            
        aspirate(ham_int, plate_poss_asp, plate_vols, liquidClass=media_exchange_liquid_class)
        dispense(ham_int, plate_poss_disp, media_vols, liquidClass=media_exchange_liquid_class)
        dispense(ham_int, liq_waste_poss, plate_vols, liquidClass=media_exchange_liquid_class)
        tip_eject(ham_int, current_tips)
        
    tilt_module_set_pos(ham_int, "T1", 0)
    get_plate_gripper_seq(ham_int, Lids_Park, 5, 84, 87)
    place_plate_gripper_seq(ham_int, Lids, 5, 84, 87)
            
    print("Program complete")