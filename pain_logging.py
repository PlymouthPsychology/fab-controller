from datetime import datetime
import json

def make_dashdata(app):
    return json.dumps(build_log_entry(app))


def build_log_entry(app):
    return {
        'target_L': app.left.target,
        'target_R': app.right.target,
        'sensor_L': app.left.grams(),
        'sensor_R': app.right.grams(),
        'time': datetime.now().isoformat(),
        'remaining': app.programme_countdown and int(app.programme_countdown) or None,
        'true_L': app.left.steps_from_top,
        'true_R': app.right.steps_from_top,
    }

