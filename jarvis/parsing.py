"""Short-lived parser processes with a deadline, not an operating-system sandbox."""
import multiprocessing as mp
import queue
import time


def _parse(path,results):
    try:
        from .artifacts import extract
        results.put(('ok',extract(path)))
    except Exception as e:
        results.put(('error',f'{type(e).__name__}: {e}'))


def safe_extract(path,cancel,timeout=30):
    ctx=mp.get_context('spawn')
    results=ctx.Queue()
    process=ctx.Process(target=_parse,args=(str(path),results),daemon=True)
    process.start()
    deadline=time.monotonic()+timeout
    try:
        while time.monotonic()<deadline:
            if cancel.is_set():
                raise InterruptedError('Document reading stopped')
            try:
                status,text=results.get(timeout=.1)
                if status=='error':
                    raise ValueError(text)
                return text
            except queue.Empty:
                if not process.is_alive():
                    raise RuntimeError('Document parser exited without a result')
        raise TimeoutError('Document parsing exceeded 30 seconds; file skipped')
    finally:
        process.join(.3)
        if process.is_alive():
            process.terminate()
        process.join(3)
        results.close()
        results.join_thread()
