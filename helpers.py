import json

def _validate_json_program(jsondata):
    istriple = lambda i: len(i)==3
    try:
        prog = json.loads(jsondata['data'])
        # do some checking of prog here
        assert sum(map(istriple, prog))==len(prog), "Program not made of triples."
        return prog

    except Exception, e:
        emit('log', "Program error: " + str(e), broadcast=True)
        return False


def _schedule_program_for_execution(prog):
    # clear everything from the queue
    stopall()

    # work through the program, spawning future targets
    cumtime = 0
    for duration, left, right in prog:
        app.blocks.append(gevent.spawn_later(cumtime, _set_block_targets, *(left, right)))
        cumtime = cumtime + duration

    # make sure we end up back at a target of zero
    app.blocks.append(gevent.spawn_later(cumtime, _set_block_targets, *(0, 0)))
