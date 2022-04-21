# -*- coding: utf-8 -*-
"""
Created on Fri Mar 19 08:59:12 2021

@author: stefa
"""
import importlib
import sys
import os
import time
import csv
import logging
import platform
import subprocess

from ipsc_utils import (initialize, Plate6_2chAI, RgntResAI, MediaRepAI, 
                        Plate6, aspirate, dispense, LayoutManager,
                        layout_item, Tip96, Plate96, Plate24, tip_pick_up, get_plate_gripper,
                        move_plate_gripper, barcode_initialize, barcode_read, move_sequence,
                        place_plate_gripper, slow_iswap_firmware, normal_iswap_firmware, 
                        iswap_move_portrait_grip, get_plate_gripper_seq, move_plate_gripper_seq, 
                        place_plate_gripper_seq, resource_list_with_prefix, aspirate_cLLD, tip_eject, tilt_module_init,
                        tilt_module_set_pos, initialize_tec, set_target_tec, start_control_tec, move_plate, 
                        BC_READ, Cytomat, Celigo, iswap_move_wide_grip, process_worklist_for_method, get_oldest_file, normal_logging)


from pyhamilton import HamiltonInterface
from plateconfig import PlateConfigDict

this_file_dir = os.path.dirname(os.path.abspath(__file__))
allen_inst_dir = os.path.abspath(os.path.join(this_file_dir, '..', '..',))
cytomat_path = os.path.join(allen_inst_dir, 'Equipment', 'Cytomat')

LAYFILE = 'C:\\Program Files (x86)\\HAMILTON\\Methods\\AllenInst_ReagentCoating_scheduler_V0.1.lay'
lay_mgr = LayoutManager(LAYFILE)

system32 = os.path.join(os.environ['SystemRoot'], 'SysNative' if 
platform.architecture()[0] == '32bit' else 'System32')
listtest_path = os.path.join(system32, 'openSSH', 'ssh.exe',)


def deck_resource_from_config(plate_type, resource_key):
    deck_res = layout_item(lay_mgr, PlateConfigDict[plate_type]['LabwareClass'], PlateConfigDict[plate_type][resource_key])
    return deck_res

barcode, plate_type = process_worklist_for_method("C:\\Users\\BenG\\Desktop\\Scan\\")

#Get deck positions
CytC24 = deck_resource_from_config(plate_type, 'CytC24')
Cyt6000 = deck_resource_from_config(plate_type, 'Cyt6000')
PlateParks = deck_resource_from_config(plate_type, 'PlateParkPositions')
ReaderHandoff = deck_resource_from_config(plate_type, 'ReaderHandoff')
CeligoHandoff = deck_resource_from_config(plate_type, 'CeligoHandoff')
Tilt1 = layout_item(lay_mgr, PlateConfigDict[plate_type]['LabwareClass'], PlateConfigDict[plate_type]['Tilt1'])


#Celigo settings
celigoVendor = PlateConfigDict[plate_type]['celigoVendor']
celigoAnalysisSettings = PlateConfigDict[plate_type]['celigoAnalysisSettings']
celigoScanSettings = PlateConfigDict[plate_type]['celigoScanSettings']
celigoPltType = PlateConfigDict[plate_type]['celigoPltTypeID']


#Get grip parameters
gripHeight = PlateConfigDict[plate_type]['gripHeight']
gripWidth = PlateConfigDict[plate_type]['gripWidth']
openWidth = PlateConfigDict[plate_type]['openWidth']
gripHeight_lid = PlateConfigDict[plate_type]['gripHeight_lid']


DW24wSample = layout_item(lay_mgr, MediaRepAI, 'MediaRep_0016')
AI_24w_Place = layout_item(lay_mgr, MediaRepAI, 'AI_24DW_Place')

AI_24w_DW = layout_item(lay_mgr, Plate24, 'AI_24w_DeepWell')


CPAC_6 = layout_item(lay_mgr, Plate6, 'CPAC_6')

AI_24w_DeepWell = layout_item(lay_mgr, Plate24, 'AI_24w_DeepWell_0003')

scanner_seq = PlateConfigDict[plate_type]['Scanner']
CytC24_6wp = layout_item(lay_mgr, Plate6, 'CytC24_6wp')
Scanner_24wp = layout_item(lay_mgr, Plate24, 'Scanner_24wp')
Plates_6w = resource_list_with_prefix(lay_mgr, 'Plate_6_', Plate6, 5)
CPAC_96screen = layout_item(lay_mgr, Plate96, 'CPAC_96screen')


simulation_on = '--simulate' in sys.argv


if __name__ == "__main__":
    with HamiltonInterface(simulate=simulation_on) as ham_int, Cytomat(comPort='COM5', cytomatType='C24', num_slots=205, db=r'Driver={Microsoft Access Driver (*.mdb)};DBQ=C:\Program Files (x86)\HAMILTON\System\CytomatC24.mdb;') as Cytomat24, Cytomat(comPort='COM6', cytomatType='C6000', num_slots=125, db=r'Driver={Microsoft Access Driver (*.mdb)};DBQ=C:\Program Files (x86)\HAMILTON\System\CytomatC6002.mdb;') as Cytomat6000:
        
        normal_logging(ham_int, '96w_Scan_local')
        
        initialize(ham_int)
    
        celigo = Celigo()
        celigo.connect("169.254.184.127")
        celigo.login("svc_aicspipeline","P#ableDH")
        celigo.ejectPlate()
        celigo.closeDoor()
        
        cytomat_position = Cytomat24.get_location_by_barcode(barcode)
        
        check_barcode = Cytomat24.scan_barcode_at_position(cytomat_position)
        if barcode != check_barcode:
            raise Exception("Scanned barcode doesn't match database position")
        
        Cytomat24.get_plate_by_barcode(barcode)
        
        logging.info("iSwap fetching plate")
        slow_iswap_firmware(ham_int)
        iswap_move_portrait_grip(ham_int, CytC24, Tilt1)
        normal_iswap_firmware(ham_int)
        
        logging.info("iSwap moving plate to celigo")
        celigo.ejectPlate()
        slow_iswap_firmware(ham_int)
        iswap_move_wide_grip(ham_int, ReaderHandoff, CeligoHandoff)
        normal_iswap_firmware(ham_int)
        
        logging.info("Celigo loading plate")
        celigo.ejectPlate()
        celigo.loadPlate(plateID = barcode, description = celigoVendor, plateType = celigoPltType)
    
        celigo.scan(celigoScanSettings, '')
    
        export_dir = 'C:\\Users\\svc_aicspipeline\\Desktop\\CeligoExports'
        logging.info("Exporting to " + export_dir)
        celigo.exportImages(export_dir, image_format = 1, stitching_mode = 1 )
    
        celigo.ejectPlate()
    
        slow_iswap_firmware(ham_int)
        move_plate(ham_int, CeligoHandoff, ReaderHandoff, 12, 123.7, 1, 129)
        normal_iswap_firmware(ham_int)
    
        slow_iswap_firmware(ham_int)
        move_plate(ham_int, ReaderHandoff, CytC24, 12, 123.7, 1, 129)
        normal_iswap_firmware(ham_int)
    
        Cytomat24.store_plate_by_position(cytomat_position, barcode = barcode)
        
        subprocess.Popen([listtest_path, 'svc_aicspipeline@10.128.74.13', '-p', '2022', 'celigo_export.bat'])
