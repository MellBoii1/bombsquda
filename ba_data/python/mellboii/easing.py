"""we have animateplus at home"""
# oh yeah huge thanks to easing.net
# for making the maths for these
# yeah i dont wanna do math so what
# fuck you bitc
import math

def lerp(a, b, t):
    if isinstance(a, (tuple, list)):
        return tuple(
            lerp(x, y, t)
            for x, y in zip(a, b)
        )
    return a + (b - a) * t

# actual functions for the easing
def linear(t):
    return t

def ease_in_quad(t):
    return t * t

def ease_out_quad(t):
    return 1 - (1 - t) ** 2

def ease_in_out_quad(t):
    if t < 0.5:
        return 2 * t * t
    return 1 - ((-2 * t + 2) ** 2) / 2

def ease_in_out_quart(x):
    if x < 0.5:
        return 8 * x**4
    return 1 - 8 * (1 - x)**4

# enumeration (should make this, y'know, enum)
EASINGS = {
    'ease_in_out_quad': ease_in_out_quad,
    'ease_in_out_quart': ease_in_out_quart,
    'ease_out_quad': ease_out_quad,
    'ease_in_quad': ease_in_quad,
    'linear': linear,
}

def smooth_out(
    keys: dict,
    easing: str = 'ease_in_out_quad',
    divisions: int = 8,
):
    """Given keyframes {time: value}, returns a new dict with
    interpolated in-between keys using the given easing."""
    if easing not in EASINGS:
        raise TypeError(
            f'{easing!r} is an incorrect easing type. Allowed: {list(EASINGS)}'
        )
    ease_func = EASINGS[easing]

    sorted_keys = sorted(keys.items()) 
    our_keys = {}

    for (t0, v0), (t1, v1) in zip(sorted_keys, sorted_keys[1:]):
        our_keys[t0] = v0
        for i in range(1, divisions):
            t = i / divisions
            eased_t = ease_func(t)
            time = lerp(t0, t1, eased_t)
            value = lerp(v0, v1, eased_t)
            our_keys[time] = value

    if sorted_keys:
        # wanna keep the last keyframe here
        our_keys[sorted_keys[-1][0]] = sorted_keys[-1][1]

    # return it sorted nicely
    return dict(sorted(our_keys.items()))
    

def choppify(keys, fps=30):
    """Given keyframes {time: value}, returns a new dict with
    more choppy-ish keyframes based on FPS arg."""
    times = sorted(keys)

    def sample(t):
        for i in range(len(times) - 1):
            t1, t2 = times[i], times[i + 1]

            if t1 <= t <= t2:
                v1 = keys[t1]
                v2 = keys[t2]

                frac = (t - t1) / (t2 - t1)

                # Number interpolation.
                if isinstance(v1, (int, float)):
                    return lerp(v1, v2, frac)

                # Tuple/list interpolation.
                return type(v1)(
                    lerp(a, b, frac)
                    for a, b in zip(v1, v2)
                )

        return keys[times[-1]]

    result = {}
    dt = 1.0 / fps
    duration = times[-1]

    t = 0.0
    while t < duration:
        value = sample(t)

        result[t] = value
        result[min(t + dt - 0.0001, duration)] = value

        t += dt

    result[duration] = keys[duration]
    return result