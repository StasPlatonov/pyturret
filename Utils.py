import time


class Utils(object):

    @staticmethod
    def millis():
        return round(time.time() * 1000)
    # ------------------------------------------------------------------------------------------
