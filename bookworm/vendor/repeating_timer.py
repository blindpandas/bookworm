import threading


class RepeatingTimer(threading.Thread):
    """
    Call a function after a specified number of seconds, it will then
    repeat again after the specified number of seconds

    Note: If the function provided takes time to execute, this time is NOT taken from the next wait period

     t = RepeatingTimer(30.0, f, args=[], kwargs={})
     t.start()
     t.cancel() # stop the timer's actions
    """

    def __init__(self, interval, function, daemon=True, *args, **kwargs):
        threading.Thread.__init__(self)
        self.daemon = daemon
        self.interval = float(interval)
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.finished = threading.Event()

    def cancel(self):
        """Stop the timer if it hasn't finished yet"""
        log.debug("Stopping repeater for %s" % (self.function,))
        self.finished.set()

    stop = cancel

    def run(self):
        while not self.finished.is_set():
            self.finished.wait(self.interval)
            if not self.finished.is_set():  # In case someone has canceled while waiting
                try:
                    self.function(*self.args, **self.kwargs)
                except:
                    log.exception(
                        "Execution failed. Function: %r args: %r and kwargs: %r"
                        % (self.function, self.args, self.kwargs)
                    )
