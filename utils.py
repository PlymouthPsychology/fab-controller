from __future__ import division


def scale_to_new_range(x, old, new=(0, 1)):
    OldMin, OldMax = old
    NewMin, NewMax = new
    
    OldRange = (OldMax - OldMin)  
    NewRange = (NewMax - NewMin)  
    NewValue = (((x - OldMin) * NewRange) / OldRange) + NewMin
    
    return NewValue