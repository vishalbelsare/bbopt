# ROE

Roe is a random optimization engine for Python.

To use roe, just add

    # Roe boilerplate:
    from roe import BlackBox
    bb = BlackBox(file=__file__)
    if __name__ == "__main__":
        bb.run(backend=<your backend here>)

to the top of your file, then call

    x = bb.param(name="x", <your parameters here>)

for each of the tunable parameters in your model, and finally add

    bb.maximize(x)      or      bb.minimize(x)

to set the value being optimized. Then, run

    python <your file here>

to train your model, and just

    import <your module here>

to serve it.
