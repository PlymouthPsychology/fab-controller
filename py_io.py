from fakeworld import pin_states

def digital_read(pin): 
    return pin_states[pin]


def digital_write(pin, val): 
    pin_states[pin] = val
    return (pin, val)

