import math
import random
from settings import *


av = lambda x: sum(x)/SMOOTHING_WINDOW


# more complex function probably not needed
# # pre-calculate decay function weights to smooth sensor input
# _tmp = [i**2 for i in range(SMOOTHING_WINDOW)]
# SMOOTHING_CURVE = [scale_to_new_range(i, (min(_tmp), max(_tmp))) for i in _tmp]  # scale it back to 0..1


# def smoother(x):
#     if not x:
#         return 0
#     return sum([i*j for i, j in zip(x, SMOOTHING_CURVE)])/len(x) or 0


# def smooth_current_sensor_values(func=av):
#     """Calculate the current sensor readings, perhaps using smoothing function."""
#     while True:
#         newvals = {
#             'left': func(app.measurements['left']),
#             'right': func(app.measurements['right']),
#         }
#         app.smoothed.update(newvals)
#         gevent.sleep(SENSOR_SMOOTHED_CALC_INTERVAL)



