import OriginExt
import multiprocessing as mp
import os
import time


if __name__ == '__main__':
    this_dir = os.path.dirname(os.path.abspath(__file__))

    in_file = os.path.join(this_dir, 'Origin_digest_template.opj')
    out_file = os.path.join(this_dir, 'Origin_digest_template_mod.opj')

    app = OriginExt.Application()

    result = mp.Queue()
    proc = mp.Process(target = app.Load, args = (out_file))

    proc.start()
    proc.join(timeout = 10)
    if proc.is_alive():
        print("Load timed out.")
        proc.terminate()
    else:
        print("Finished loading")