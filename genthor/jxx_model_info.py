import itertools
import copy
from math import pi

try:
    from collections import OrderedDict
except ImportError:
    print "Python 2.7+ OrderedDict collection not available"
    try:
        from ordereddict import OrderedDict
    except ImportError:
        raise ImportError("OrderedDict not available")

MODEL_CATEGORIES = OrderedDict([('test%d'%i, ['test%d'%i] + ['test%d_00%d'%(i,j) for j in range(1,11)]) for i in range(1,6)])

BACKGROUNDS = ['DH-ITALY01SN.jpg',
 'DH-ITALY02SN.jpg',
 'DH-ITALY03SN.jpg',
 'DH-ITALY04SN.jpg',
 'DH-ITALY05SN.jpg',
 'DH-ITALY06SN.jpg',
 'DH-ITALY07SN.jpg',
 'DH-ITALY08SN.jpg',
 'DH-ITALY09SN.jpg',
 'DH-ITALY10SN.jpg',
 'DH-ITALY11SN.jpg',
 'DH-ITALY12SN.jpg',
 'DH-ITALY13SN.jpg',
 'DH-ITALY14SN.jpg',
 'DH-ITALY15SN.jpg',
 'DH-ITALY16SN.jpg',
 'DH-ITALY17SN.jpg',
 'DH-ITALY18SN.jpg',
 'DH-ITALY19SN.jpg',
 'DH-ITALY20SN.jpg',
 'DH-ITALY21SN.jpg',
 'DH-ITALY22SN.jpg',
 'DH-ITALY23SN.jpg',
 'DH-ITALY24SN.jpg',
 'DH-ITALY25SN.jpg',
 'DH-ITALY26SN.jpg',
 'DH-ITALY27SN.jpg',
 'DH-ITALY28SN.jpg',
 'DH-ITALY29SN.jpg',
 'DH-ITALY30SN.jpg',
 'DH-ITALY31SN.jpg',
 'DH-ITALY32SN.jpg',
 'DH-ITALY33SN.jpg',
 'DH-ITALY34SN.jpg',
 'DH-ITALY35SN.jpg',
 'DH201SN.jpg',
 'DH202SN.jpg',
 'DH203SN.jpg',
 'DH204SN.jpg',
 'DH205SN.jpg',
 'DH206SN.jpg',
 'DH207SN.jpg',
 'DH208SN.jpg',
 'DH209SN.jpg',
 'DH210SN.jpg',
 'DH211SN.jpg',
 'DH212SN.jpg',
 'DH213SN.jpg',
 'DH214SN.jpg',
 'DH215SN.jpg',
 'DH216SN.jpg',
 'DH217SN.jpg',
 'DH218SN.jpg',
 'DH219SN.jpg',
 'DH220SN.jpg',
 'DH221SN.jpg',
 'DH222SN.jpg',
 'DH223SN.jpg',
 'DH224SN.jpg',
 'INTERIOR_01ST.jpg',
 'INTERIOR_02ST.jpg',
 'INTERIOR_03ST.jpg',
 'INTERIOR_04ST.jpg',
 'INTERIOR_05ST.jpg',
 'INTERIOR_06ST.jpg',
 'INTERIOR_07ST.jpg',
 'INTERIOR_08ST.jpg',
 'INTERIOR_09ST.jpg',
 'INTERIOR_10ST.jpg',
 'INTERIOR_11ST.jpg',
 'INTERIOR_12ST.jpg',
 'INTERIOR_13ST.jpg',
 'INTERIOR_14ST.jpg',
 'INTERIOR_15ST.jpg',
 'INTERIOR_16ST.jpg',
 'INTERIOR_17ST.jpg',
 'INTERIOR_18ST.jpg',
 'INTERIOR_19ST.jpg',
 'INTERIOR_20ST.jpg',
 'INTERIOR_21ST.jpg',
 'INTERIOR_22ST.jpg',
 'INTERIOR_23ST.jpg',
 'INTERIOR_24ST.jpg',
 'INTERIOR_25ST.jpg',
 'INTERIOR_26ST.jpg',
 'INTERIOR_27ST.jpg',
 'INTERIOR_28ST.jpg',
 'INTERIOR_29ST.jpg',
 'INTERIOR_30ST.jpg',
 'INTERIOR_31ST.jpg',
 'INTERIOR_32ST.jpg',
 'INTERIOR_33ST.jpg',
 'INTERIOR_34ST.jpg',
 'INTERIOR_35ST.jpg',
 'INTERIOR_36ST.jpg',
 'INTERIOR_37ST.jpg',
 'INTERIOR_38ST.jpg',
 'INTERIOR_39ST.jpg',
 'INTERIOR_40ST.jpg',
 'INTERIOR_41ST.jpg',
 'INTERIOR_42ST.jpg',
 'INTERIOR_43ST.jpg',
 'INTERIOR_44ST.jpg',
 'MOUNT_01SN.jpg',
 'MOUNT_02SN.jpg',
 'MOUNT_03SN.jpg',
 'MOUNT_04SN.jpg',
 'MOUNT_05SN.jpg',
 'MOUNT_06SN.jpg',
 'MOUNT_07SN.jpg',
 'MOUNT_08SN.jpg',
 'MOUNT_09SN.jpg',
 'MOUNT_10SN.jpg',
 'MOUNT_11SN.jpg',
 'MOUNT_12SN.jpg',
 'MOUNT_13SN.jpg',
 'MOUNT_14SN.jpg',
 'MOUNT_15SN.jpg',
 'MOUNT_16SN.jpg',
 'MOUNT_17SN.jpg',
 'MOUNT_18SN.jpg',
 'MOUNT_19SN.jpg',
 'MOUNT_20SN.jpg',
 'MOUNT_21SN.jpg',
 'MOUNT_22SN.jpg',
 'MOUNT_23SN.jpg',
 'MOUNT_24SN.jpg',
 'MOUNT_25SN.jpg',
 'MOUNT_26SN.jpg',
 'MOUNT_27SN.jpg',
 'MOUNT_28SN.jpg',
 'MOUNT_29SN.jpg',
 'MOUNT_30SN.jpg',
 'MOUNT_31SN.jpg',
 'MOUNT_32SN.jpg',
 'MOUNT_33SN.jpg']

