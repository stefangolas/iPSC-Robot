# -*- coding: utf-8 -*-
"""
Created on Wed Nov 25 19:34:32 2020

@author: stefa
"""


#!python3

import sys, os, time, logging, importlib
import csv
from threading import Thread

this_file_dir = os.path.dirname(__file__)
methods_dir = os.path.abspath(os.path.join(this_file_dir, '..', '..'))
dropbox_dir = os.path.dirname(methods_dir)
user_dir = os.path.dirname(dropbox_dir)
global_log_dir = os.path.join(dropbox_dir, 'Monitoring', 'log')

#pyham_pkg_path = os.path.join(methods_dir, 'perma_oem', 'pyhamilton')



#if pyham_pkg_path not in sys.path:
#    sys.path.append(pyham_pkg_path)



import pyhamilton
from pyhamilton import (HamiltonInterface, LayoutManager, ResourceType, Plate24, Plate96, Tip96,
    INITIALIZE, PICKUP, EJECT, ASPIRATE, DISPENSE, ISWAP_GET, ISWAP_PLACE, HEPA,
    WASH96_EMPTY, PICKUP96, EJECT96, ASPIRATE96, DISPENSE96, GRIP_GET, GRIP_MOVE, GRIP_PLACE, BC_READ, 
    BC_INITIALIZE, MOVE_SEQ, FIRMWARECOMMAND, TEC_INIT, TEC_SET_TARGET, TEC_START, TEC_STOP, TEC_TERMINATE, TILT_INIT,
    TILT_MOVE, oemerr, PositionError, DeckResource, Vessel)

this_file_dir = os.path.dirname(os.path.abspath(__file__))
allen_inst_dir = os.path.abspath(os.path.join(this_file_dir, '..', '..',))
cytomat_path = os.path.join(allen_inst_dir, 'Equipment', 'Cytomat')
celigo_path = os.path.join(allen_inst_dir, 'Equipment', 'Celigo')


for imp_path in (cytomat_path,celigo_path):
    pkgname = os.path.basename(imp_path)
    try:
        imported_mod = importlib.import_module(pkgname)
    except ModuleNotFoundError:
        if imp_path not in sys.path:
            sys.path.append(imp_path)
            imported_mod = importlib.import_module(pkgname)
    print('USING ' + ('SITE-PACKAGES ' if 'site-packages' in os.path.abspath(imported_mod.__file__) else 'LOCAL ') + pkgname)

from Cytomat import Cytomat
from Celigo import Celigo


def resource_list_with_prefix(layout_manager, prefix, res_class, num_ress, order_key=None, reverse=False):
    def name_from_line(line):
        field = LayoutManager.layline_objid(line)
        if field:
            return field
        return LayoutManager.layline_first_field(line)
    layline_test = lambda line: LayoutManager.field_starts_with(name_from_line(line), prefix)
    res_type = ResourceType(res_class, layline_test, name_from_line)
    res_list = [layout_manager.assign_unused_resource(res_type, order_key=order_key, reverse=reverse) for _ in range(num_ress)]
    return res_list

def labware_pos_str(labware, idx):
    print("printing idx")
    print(idx)
    return labware.layout_name() + ', ' + labware.position_id(idx)

def compound_pos_str(pos_tuples):
    present_pos_tups = [pt for pt in pos_tuples if pt is not None]
    return ';'.join((labware_pos_str(labware, idx) for labware, idx in present_pos_tups))

def compound_pos_str_96(labware96):
    return ';'.join((labware_pos_str(labware96, idx) for idx in range(96)))

def get_oldest_file(directory):
    list_of_files = os.listdir(directory)
    full_paths = [directory + x for x in list_of_files if '.ini' not in x]
    oldest_file = min(full_paths, key=os.path.getctime)
    return oldest_file

def get_plate_params_from_worklist(worklist):
    with open(worklist, "r") as csvfile: 
        reader = csv.DictReader(csvfile)
        print(reader.fieldnames)
        barcode = ''
        for row in reader:
            if barcode != row['Barcode']:
                barcode = int(row['Barcode'])
                plate_geom = row['PlateGeometry']
            break
        return barcode, plate_geom

def process_worklist_for_method(method_dir):
    scanfile = get_oldest_file(method_dir)
    barcode, plate_geometry = get_plate_params_from_worklist(scanfile)
    return barcode, plate_geometry

def initialize(ham, async_=False):
    logging.info('initialize: ' + ('a' if async_ else '') + 'synchronously initialize the robot')
    cmd = ham.send_command(INITIALIZE)
    if not async_:
        ham.wait_on_response(cmd, raise_first_exception=True)
    return cmd

def layout_item(lmgr, item_class, item_name):
    return lmgr.assign_unused_resource(ResourceType(item_class, item_name))


def hepa_on(ham, speed=15, async_=False, **more_options):
    logging.info('hepa_on: turn on HEPA filter at ' + str(speed) + '% capacity' +
            ('' if not more_options else ' with extra options ' + str(more_options)))
    cmd = ham.send_command(HEPA, fanSpeed=speed, **more_options)
    if not async_:
        ham.wait_on_response(cmd, raise_first_exception=True)
    return cmd

def wash_empty_refill(ham, async_=False, **more_options):
    logging.info('wash_empty_refill: empty the washer' +
            ('' if not more_options else ' with extra options ' + str(more_options)))
    cmd = ham.send_command(WASH96_EMPTY, **more_options)
    if not async_:
        ham.wait_on_response(cmd, raise_first_exception=True)
    return cmd

def move_plate(ham, source_plate, target_plate, gripHeight, gripWidth, gripMode, openWidth, CmplxGetDict = None, CmplxPlaceDict = None, try_inversions=None):
    
    logging.info('move_plate: Moving plate ' + source_plate.layout_name() + ' to ' + target_plate.layout_name())
    src_pos = labware_pos_str(source_plate, 0)
    trgt_pos = labware_pos_str(target_plate, 0)
    print(try_inversions)
    #if try_inversions is None:
    #    try_inversions = (0, 1)
    try_inversions=(0,1)
    
    getCmplxMvmnt, getRetractDist, getLiftUpHeight, getOrientation = (0, 0.0, 20.0, 1)
    placeCmplxMvmnt, placeRetractDist, placeLiftUpHeight, placeOrientation = (0, 0.0, 20.0, 1)
    
    
    if CmplxGetDict:
        getCmplxMvmnt = 1
        getRetractDist = CmplxGetDict['retractDist']
        getLiftUpHeight = CmplxGetDict['liftUpHeight']
        getOrientation = CmplxGetDict['labwareOrientation']
    
    if CmplxPlaceDict:
        placeCmplxMvmnt = 1
        placeRetractDist = CmplxPlaceDict['retractDist']
        placeLiftUpHeight = CmplxPlaceDict['liftUpHeight']
        placeOrientation = CmplxPlaceDict['labwareOrientation']
    
    print(placeCmplxMvmnt)
    print(getCmplxMvmnt)
    
    for inv in try_inversions:
        cid = ham.send_command(ISWAP_GET, 
                               plateLabwarePositions=src_pos, 
                               inverseGrip=inv, 
                               gripHeight=gripHeight, 
                               gripWidth=gripWidth, 
                               widthBefore=openWidth, 
                               gripMode=gripMode,
                               movementType = getCmplxMvmnt,
                               retractDistance = getRetractDist,
                               liftUpHeight = getLiftUpHeight,
                               labwareOrientation = getOrientation,
                               )
        try:
            ham.wait_on_response(cid, raise_first_exception=True, timeout=120)
            break
        except PositionError:
            print("trying inverse")
            pass
    #else:
    #    raise IOError
    cid = ham.send_command(ISWAP_PLACE, 
                           plateLabwarePositions=trgt_pos, 
                           movementType = placeCmplxMvmnt, 
                           retractDistance = placeRetractDist,
                           liftUpHeight = placeLiftUpHeight,
                           labwareOrientation = placeOrientation
                           )
    try:
        ham.wait_on_response(cid, raise_first_exception=True, timeout=120)
    except PositionError:
        raise IOError

def iswap_move_wide_grip(ham_int, source, destination):
    CmplxPlaceDict = {'retractDist': 200.0, 'liftUpHeight': 20.0, 'labwareOrientation': 4}
    move_plate(ham_int, source, destination, 12, 123.7, 1, 132, CmplxPlaceDict = CmplxPlaceDict)

def iswap_move_portrait_grip(ham_int, source, destination):
    firmware_command(ham_int, [{'FirmwareCommand':'C0AA', 'FirmwareParameter':'xe1/1'}])
    #CmplxPlaceDict = {'retractDist': 200.0, 'liftUpHeight': 20.0, 'labwareOrientation': 4}
    move_plate(ham_int, source, destination, 12, 81, 0, 87)
    firmware_command(ham_int, [{'FirmwareCommand':'C0AA', 'FirmwareParameter':'xe4/1'}])
    

def offset_equal_spaced_idxs(start_idx, increment):
    # a generator that will be used for reader positions
    idx = start_idx
    while True:
        yield idx
        idx += increment

def read_plate(ham_int, reader_int, reader_site, plate, protocol_names, plate_id=None, async_task=None, plate_destination=None):
    logging.info('read_plate: Running plate protocols ' + ', '.join(protocol_names) +
            ' on plate ' + plate.layout_name() + ('' if plate_id is None else ' with id ' + plate_id))
    reader_int.plate_out(block=True)
    move_plate(ham_int, plate, reader_site)
    if async_task:
        t = run_async(async_task)
    plate_datas = reader_int.run_protocols(protocol_names, plate_id_1=plate_id)
    reader_int.plate_out(block=True)
    if async_task:
        t.join()
    if plate_destination is None:
        plate_destination = plate
    move_plate(ham_int, reader_site, plate_destination)
    return plate_datas

def channel_var(pos_tuples):
    ch_var = ['0']*16
    for i, pos_tup in enumerate(pos_tuples):
        if pos_tup is not None:
            ch_var[i] = '1'
    return ''.join(ch_var)

def get_plate_gripper(ham, source_plate, gripHeight, gripWidth, openWidth, try_inversions=None, lid=False):
    logging.info('get_plate: Getting plate ' + source_plate.layout_name() )
    src_pos = labware_pos_str(source_plate, 0)
    if lid:
        cid = ham.send_command(GRIP_GET, plateLabwarePositions=src_pos, transportMode=1, gripHeight=gripHeight, gripWidth=gripWidth, openWidth=openWidth, toolSequence='COREGripTool_OnWaste_1000ul_0001')
    else:
        cid = ham.send_command(GRIP_GET, plateLabwarePositions=src_pos, transportMode=0, gripHeight=0, toolSequence='COREGripTool_OnWaste_1000ul_0001')
    ham.wait_on_response(cid, raise_first_exception=True, timeout=120)


def move_plate_gripper(ham, dest_plate, try_inversions=None):
    logging.info('move_plate: Moving plate ' + dest_plate.layout_name() )
    dest_pos = labware_pos_str(dest_plate, 0)
    cid = ham.send_command(GRIP_MOVE, plateLabwarePositions=dest_pos)
    ham.wait_on_response(cid, raise_first_exception=True, timeout=120)
    
def place_plate_gripper(ham, dest_plate, try_inversions=None):
    logging.info('place_plate: Placing plate ' + dest_plate.layout_name() )
    dest_pos = labware_pos_str(dest_plate, 0)
    cid = ham.send_command(GRIP_PLACE, plateLabwarePositions=dest_pos, toolSequence='COREGripTool_OnWaste_1000ul_0001')
    ham.wait_on_response(cid, raise_first_exception=True, timeout=120)


def initialize_tec(ham, controller_id):
    logging.info('Initializing TEC ' + str(controller_id) )
    cid = ham.send_command(TEC_INIT, ControllerID=controller_id)
    ham.wait_on_response(cid, raise_first_exception=True, timeout=120)

def set_target_tec(ham, target_temp, controller_id, device_id):
    logging.info('Set target temperature ' + str(controller_id) +' '+ str(device_id)+' to '+str(target_temp)+' degrees C')
    cid = ham.send_command(TEC_SET_TARGET, TargetTemperature=target_temp, ControllerID=controller_id, DeviceID=device_id)
    ham.wait_on_response(cid, raise_first_exception=True, timeout=120)

def start_control_tec(ham, controller_id, device_id):
    logging.info('Starting temperature control '+str(controller_id)+' '+str(device_id))
    cid=ham.send_command(TEC_START, ControllerID=controller_id, DeviceID=device_id)
    ham.wait_on_response(cid, raise_first_exception=True, timeout=120)

def stop_control_tec(ham, controller_id, device_id):
    logging.info('Ending temperature control '+str(controller_id)+' '+str(device_id))
    cid=ham.send_command(TEC_STOP, ControllerID=controller_id, DeviceID=device_id)
    ham.wait_on_response(cid, raise_first_exception=True, timeout=120)

def terminate_tec(ham, stop_all_devices):
    logging.info('Terminating TEC')
    cid=ham.send_command(TEC_TERMINATE, StopAllDevices=stop_all_devices)
    ham.wait_on_response(cid, raise_first_exception=True, timeout=120)

def tilt_module_init(ham, ModuleName, Comport, TraceLevel, Simulate):
    logging.info('Initializing Tilt Module')
    cid = ham.send_command(TILT_INIT, ModuleName=ModuleName, Comport=Comport, TraceLevel=TraceLevel, Simulate=Simulate)
    ham.wait_on_response(cid, raise_first_exception=True, timeout=120)

def tilt_module_set_pos(ham, ModuleName, Angle):
    logging.info('Setting tilt module to position')
    cid = ham.send_command(TILT_MOVE, ModuleName=ModuleName, Angle=Angle)
    ham.wait_on_response(cid, raise_first_exception=True, timeout=120)

def get_plate_gripper_seq(ham, source_plate_seq,  gripHeight, gripWidth, openWidth,  try_inversions=None, lid=False):
    logging.info('get_plate: Getting plate ' + source_plate_seq )
    if lid:
        cid = ham.send_command(GRIP_GET, plateSequence=source_plate_seq, transportMode=1, gripHeight=gripHeight, gripWidth=gripWidth, widthBefore=openWidth, toolSequence='COREGripTool_OnWaste_1000ul_0001')
    else:
        cid = ham.send_command(GRIP_GET, plateSequence=source_plate_seq, transportMode=0, gripHeight=gripHeight, gripWidth=gripWidth, widthBefore=openWidth, toolSequence='COREGripTool_OnWaste_1000ul_0001')
    ham.wait_on_response(cid, raise_first_exception=True, timeout=120)

def move_plate_gripper_seq(ham, dest_plate_seq, try_inversions=None):
    logging.info('move_plate: Moving plate ' + dest_plate_seq)
    cid = ham.send_command(GRIP_MOVE, plateSequence=dest_plate_seq)
    ham.wait_on_response(cid, raise_first_exception=True, timeout=120)
    
def place_plate_gripper_seq(ham, dest_plate_seq, try_inversions=None):
    logging.info('place_plate: Placing plate ' + dest_plate_seq )
    cid = ham.send_command(GRIP_PLACE, plateSequence=dest_plate_seq, toolSequence='COREGripTool_OnWaste_1000ul_0001')
    ham.wait_on_response(cid, raise_first_exception=True, timeout=120)


def barcode_initialize(ham_int,comport):
    logging.info('Initializing reader on COMPORT '+comport)
    cid = ham_int.send_command(BC_INITIALIZE, ComPort=comport)
    print(cid)
    response = ham_int.wait_on_response(cid, raise_first_exception=True, timeout=120)
    print(response)

def barcode_read(ham_int):
    cid = ham_int.send_command(BC_READ)
    response=ham_int.wait_on_response(cid, raise_first_exception=True, timeout=120)
    return response

def move_sequence(ham_int, sequence, xDisplacement=0, yDisplacement=0, zDisplacement=0):
    cid = ham_int.send_command(MOVE_SEQ, inputSequence=sequence, xDisplacement=xDisplacement, yDisplacement=yDisplacement, zDisplacement=zDisplacement)
    ham_int.wait_on_response(cid, raise_first_exception=True, timeout=120)

slow_iswap_command_list=[{'FirmwareCommand':'R0AA','FirmwareParameter':'wv10000'},
                         {'FirmwareCommand':'R0AA','FirmwareParameter':'wr020'},
                         {'FirmwareCommand':'R0AA','FirmwareParameter':'tv10000'},
                         {'FirmwareCommand':'R0AA','FirmwareParameter':'tr020'},
                         {'FirmwareCommand':'C0AA','FirmwareParameter':'xe1/1'},
                         {'FirmwareCommand':'R0YR','FirmwareParameter':'yv1000'},
                         {'FirmwareCommand':'PXAA','FirmwareParameter':'yr1'},
                         ]

normal_iswap_command_list=[{'FirmwareCommand':'PXAA','FirmwareParameter':'yr4'},
                         {'FirmwareCommand':'R0YR','FirmwareParameter':'yv5000'},
                         {'FirmwareCommand':'C0AA','FirmwareParameter':'xe4/1'},
                         {'FirmwareCommand':'R0AA','FirmwareParameter':'wv55000'},
                         {'FirmwareCommand':'R0AA','FirmwareParameter':'wr170'},
                         {'FirmwareCommand':'R0AA','FirmwareParameter':'tv45000'},
                         {'FirmwareCommand':'R0AA','FirmwareParameter':'tr145'},
                         ]

def firmware_command(ham_int, firmware_command_list):
    cid = ham_int.send_command(FIRMWARECOMMAND, FirmwareCommandList=firmware_command_list)
    ham_int.wait_on_response(cid, raise_first_exception=True, timeout=120)

def slow_iswap_firmware(ham_int):
    firmware_command(ham_int, slow_iswap_command_list)

def normal_iswap_firmware(ham_int):
    firmware_command(ham_int, normal_iswap_command_list)
    
    

def tip_pick_up(ham_int, pos_tuples, **more_options):
    logging.info('tip_pick_up: Pick up tips at ' + '; '.join((labware_pos_str(*pt) if pt else '(skip)' for pt in pos_tuples)) +
            ('' if not more_options else ' with extra options ' + str(more_options)))
    num_channels = len(pos_tuples)
    if num_channels > 8:
        raise ValueError('Can only pick up 8 tips at a time')
    ch_patt = channel_var(pos_tuples)
    labware_poss = compound_pos_str(pos_tuples)
    ham_int.wait_on_response(ham_int.send_command(PICKUP,
        labwarePositions=labware_poss,
        channelVariable=ch_patt,
        **more_options), raise_first_exception=True)

def tip_eject(ham_int, pos_tuples=None, **more_options):
    if pos_tuples is None:
        logging.info('tip_eject: Eject tips to default waste' + ('' if not more_options else ' with extra options ' + str(more_options)))
        more_options['useDefaultWaste'] = 1
        dummy = Tip96('')
        pos_tuples = [(dummy, 0)] * 8
    else:
        logging.info('tip_eject: Eject tips to ' + '; '.join((labware_pos_str(*pt) if pt else '(skip)' for pt in pos_tuples)) +
                ('' if not more_options else ' with extra options ' + str(more_options)))
    num_channels = len(pos_tuples)
    if num_channels > 8:
        raise ValueError('Can only eject up to 8 tips')
    ch_patt = channel_var(pos_tuples)
    labware_poss = compound_pos_str(pos_tuples)
    ham_int.wait_on_response(ham_int.send_command(EJECT,
        labwarePositions=labware_poss,
        channelVariable=ch_patt,
        **more_options), raise_first_exception=True)

default_liq_class = 'Allen_MediaChange_StandardVolume_Water_DispenseJet_Part1'
#default_liq_class = 'StandardVolume_Water_DispenseSurface_Part_no_transport_vol'


def assert_parallel_nones(list1, list2):
    if not (len(list1) == len(list2) and all([(i1 is None) == (i2 is None) for i1, i2 in zip(list1, list2)])):
        raise ValueError('Lists must have parallel None entries')

def aspirate(ham_int, pos_tuples, vols, **more_options):
    list(pos_tuples)
    list(vols)
    assert_parallel_nones(pos_tuples, vols)
    logging.info('aspirate: Aspirate volumes ' + str(vols) + ' from positions [' +
            '; '.join((labware_pos_str(*pt) if pt else '(skip)' for pt in pos_tuples)) +
            (']' if not more_options else '] with extra options ' + str(more_options)))
    if len(pos_tuples) > 8:
        raise ValueError('Can only aspirate with 8 channels at a time')
    if 'liquidClass' not in more_options:
        more_options.update({'liquidClass':default_liq_class})
    ham_int.wait_on_response(ham_int.send_command(ASPIRATE,
        channelVariable=channel_var(pos_tuples),
        labwarePositions=compound_pos_str(pos_tuples),
        volumes=[v for v in vols if v is not None],
        **more_options), raise_first_exception=True)

def aspirate_cLLD(ham_int, pos_tuples, vols, **more_options):
    list(pos_tuples)
    list(vols)
    assert_parallel_nones(pos_tuples, vols)
    logging.info('aspirate: Aspirate volumes ' + str(vols) + ' from positions [' +
            '; '.join((labware_pos_str(*pt) if pt else '(skip)' for pt in pos_tuples)) +
            (']' if not more_options else '] with extra options ' + str(more_options)))
    if len(pos_tuples) > 8:
        raise ValueError('Can only aspirate with 8 channels at a time')
    if 'liquidClass' not in more_options:
        more_options.update({'liquidClass':default_liq_class})
    ham_int.wait_on_response(ham_int.send_command(ASPIRATE,
        channelVariable=channel_var(pos_tuples),
        labwarePositions=compound_pos_str(pos_tuples),
        volumes=[v for v in vols if v is not None],
        capacitiveLLD = 1,
        **more_options), raise_first_exception=True)


def dispense(ham_int, pos_tuples, vols, **more_options):
    assert_parallel_nones(pos_tuples, vols)
    logging.info('dispense: Dispense volumes ' + str(vols) + ' into positions [' +
            '; '.join((labware_pos_str(*pt) if pt else '(skip)' for pt in pos_tuples)) +
            (']' if not more_options else '] with extra options ' + str(more_options)))
    if len(pos_tuples) > 8:
        raise ValueError('Can only aspirate with 8 channels at a time')
    if 'liquidClass' not in more_options:
        more_options.update({'liquidClass':default_liq_class})
    ham_int.wait_on_response(ham_int.send_command(DISPENSE,
        channelVariable=channel_var(pos_tuples),
        labwarePositions=compound_pos_str(pos_tuples),
        volumes=[v for v in vols if v is not None],
        **more_options), raise_first_exception=True)

def tip_pick_up_96(ham_int, tip96, **more_options):
    logging.info('tip_pick_up_96: Pick up tips at ' + tip96.layout_name() +
            ('' if not more_options else ' with extra options ' + str(more_options)))
    labware_poss = compound_pos_str_96(tip96)
    ham_int.wait_on_response(ham_int.send_command(PICKUP96,
        labwarePositions=labware_poss,
        **more_options), raise_first_exception=True)

def tip_eject_96(ham_int, tip96=None, **more_options):
    logging.info('tip_eject_96: Eject tips to ' + (tip96.layout_name() if tip96 else 'default waste') +
            ('' if not more_options else ' with extra options ' + str(more_options)))
    if tip96 is None:
        labware_poss = ''
        more_options.update({'tipEjectToKnownPosition':2}) # 2 is default waste
    else:   
        labware_poss = compound_pos_str_96(tip96)
    ham_int.wait_on_response(ham_int.send_command(EJECT96,
        labwarePositions=labware_poss,
        **more_options), raise_first_exception=True)

def aspirate_96(ham_int, plate96, vol, **more_options):
    logging.info('aspirate_96: Aspirate volume ' + str(vol) + ' from ' + plate96.layout_name() +
            ('' if not more_options else ' with extra options ' + str(more_options)))
    if 'liquidClass' not in more_options:
        more_options.update({'liquidClass':default_liq_class})
    ham_int.wait_on_response(ham_int.send_command(ASPIRATE96,
        labwarePositions=compound_pos_str_96(plate96),
        aspirateVolume=vol,
        **more_options), raise_first_exception=True)

def dispense_96(ham_int, plate96, vol, **more_options):
    logging.info('dispense_96: Dispense volume ' + str(vol) + ' into ' + plate96.layout_name() +
            ('' if not more_options else ' with extra options ' + str(more_options)))
    if 'liquidClass' not in more_options:
        more_options.update({'liquidClass':default_liq_class})
    ham_int.wait_on_response(ham_int.send_command(DISPENSE96,
        labwarePositions=compound_pos_str_96(plate96),
        dispenseVolume=vol,
        **more_options), raise_first_exception=True)




def add_robot_level_log(logger_name=None):
    logger = logging.getLogger(logger_name) # root logger if None
    logger.setLevel(logging.DEBUG)
    with open(os.path.join(user_dir, '.roboid')) as roboid_f:
        robot_id = roboid_f.read()
    robot_log_dir = os.path.join(global_log_dir, robot_id, robot_id + '.log')
    hdlr = logging.FileHandler(robot_log_dir)
    formatter = logging.Formatter('[%(asctime)s] %(name)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)

class StderrLogger:
    def __init__(self, level):
        self.level = level
        self.stderr = sys.stderr

    def write(self, message):
        self.stderr.write(message)
        if message.strip():
            self.level(message.replace('\n', ''))

def add_stderr_logging(logger_name=None):
    logger = logging.getLogger(logger_name) # root logger if None
    sys.stderr = StderrLogger(logger.error)

def normal_logging(ham_int, method_local_dir):
    local_log_dir = os.path.join(method_local_dir, 'log')
    if not os.path.exists(local_log_dir):
        os.mkdir(local_log_dir)
    main_logfile = os.path.join(local_log_dir, 'main.log')
    logging.basicConfig(filename=main_logfile, level=logging.DEBUG, format='[%(asctime)s] %(name)s %(levelname)s %(message)s')
    #add_robot_level_log()
    add_stderr_logging()
    import __main__
    for banner_line in log_banner('Begin execution of ' + __main__.__file__):
        logging.info(banner_line)
    ham_int.set_log_dir(os.path.join(local_log_dir, 'hamilton.log'))


def run_async(funcs):
    def go():
        try:
            iter(funcs)
        except TypeError:
            funcs()
            return
        for func in funcs:
            func()
    func_thread = Thread(target=go, daemon=True)
    func_thread.start()
    return func_thread

def yield_in_chunks(sliceable, n):
    sliceable = list(sliceable)
    start_pos = 0
    end_pos = n
    while start_pos < len(sliceable):
        yield sliceable[start_pos:end_pos]
        start_pos, end_pos = end_pos, end_pos + n

def log_banner(banner_text):
    l = len(banner_text)
    margin = 5
    width = l + 2*margin + 2
    return ['#'*width,
            '#' + ' '*(width - 2) + '#',
            '#' + ' '*margin + banner_text + ' '*margin + '#',
            '#' + ' '*(width - 2) + '#',
            '#'*width]

class Plate6(DeckResource):

    def __init__(self, layout_name):
        self._layout_name = layout_name
        self._num_items = 6
        self.resource_type = DeckResource.types.VESSEL
        self._items = [Vessel(self, i) for i in range(self._num_items)]

    def well_coords(self, idx):
        self._assert_idx_in_range(idx)
        return int(idx)//2, int(idx)%2

    def _alignment_delta(self, start, end):
        [self._assert_idx_in_range(p) for p in (start, end)]
        xs, ys = self.well_coords(start)
        xe, ye = self.well_coords(end)
        return (xe - xs, ye - ys, [DeckResource.align.VERTICAL] if xs == xe and ys != ye else [])

    def position_id(self, idx):
        x, y = self.well_coords(idx)
        return 'AB'[y] + str(x + 1)



class MediaRepAI(DeckResource):

    def __init__(self, layout_name):
        self._layout_name = layout_name
        self._num_items = 16
        self.resource_type = DeckResource.types.VESSEL
        self._items = [Vessel(self, i) for i in range(self._num_items)]

    def well_coords(self, idx):
        self._assert_idx_in_range(idx)
        return int(idx)%2, int(idx)//2

    def _alignment_delta(self, start, end):
        [self._assert_idx_in_range(p) for p in (start, end)]
        xs, ys = self.well_coords(start)
        xe, ye = self.well_coords(end)
        return (xe - xs, ye - ys, [DeckResource.align.VERTICAL] if xs == xe and ys != ye else [])

    def position_id(self, idx):
        return str(idx+1)
    

class RgntResAI(DeckResource):

    def __init__(self, layout_name):
        self._layout_name = layout_name
        self._num_items = 8
        self.resource_type = DeckResource.types.VESSEL
        self._items = [Vessel(self, i) for i in range(self._num_items)]

    def well_coords(self, idx):
        self._assert_idx_in_range(idx)
        return int(1), int(idx)

    def _alignment_delta(self, start, end):
        [self._assert_idx_in_range(p) for p in (start, end)]
        xs, ys = self.well_coords(start)
        xe, ye = self.well_coords(end)
        return (xe - xs, ye - ys, [DeckResource.align.VERTICAL] if xs == xe and ys != ye else [])

    def position_id(self, idx):
        return str(idx+1)


class Plate6_2chAI(DeckResource):

    def __init__(self, layout_name):
        self._layout_name = layout_name
        self._num_items = 12
        self.resource_type = DeckResource.types.VESSEL
        self._items = [Vessel(self, i) for i in range(self._num_items)]

#    def well_coords(self, idx):
#        self._assert_idx_in_range(idx)
#        return int(idx)%2, int(idx)//2

#    def _alignment_delta(self, start, end):
#        [self._assert_idx_in_range(p) for p in (start, end)]
#        xs, ys = self.well_coords(start)
#        xe, ye = self.well_coords(end)
#        return (xe - xs, ye - ys, [DeckResource.align.VERTICAL] if xs == xe and ys != ye else [])

    def position_id(self, idx):
        return 'AABB'[idx%4]+str(idx//4+1)+'AB'[idx%2]
