from pyfirmata import ArduinoDue, util
import time
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s [%(thread)d] %(name)s[%(levelname)s]: %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


class TurretController(object):

    def __init__(self, settings):
        self.Settings = settings
        self.Yaw = 0
        self.TargetYaw = 0
        self.Pitch = 0
        self.TargetPitch = 0
        try:
            self.Board = ArduinoDue(self.Settings.TurretPort)

            # set up pins as digital pings with PWM
            self.YawPin = self.Board.get_pin('d:' + str(self.Settings.YawPin) + ':p')
            self.PitchPin = self.Board.get_pin('d:' + str(self.Settings.PitchPin) + ':p')

            # For analog ports
            #it = util.Iterator(self.Board)
            #it.start()

        except Exception as e:
            self.Board = None
            logger.error("Failed to initialize: " + str(e))
    # ------------------------------------------------------------------------------------------

    def move_servos(self, yaw, pitch):
        self.YawPin.write(yaw)
        self.PitchPin.write(pitch)
    # ------------------------------------------------------------------------------------------

    def set_yaw(self, value):
        #logger.info("Set yaw to {}".format(value))
        self.TargetYaw = value
    # ------------------------------------------------------------------------------------------

    def set_pitch(self, value):
        #logger.info("Set pitch to {}".format(value))
        self.TargetPitch = value
    # ------------------------------------------------------------------------------------------

    def update(self, delta):
        if self.TargetYaw != self.Yaw:
            if self.Board is not None:
                #self.Board.digital[self.Settings.YawPin].write(self.TargetYaw)
                self.YawPin.write(self.TargetYaw)
            self.Yaw = self.TargetYaw

        if self.TargetPitch != self.Pitch:
            if self.Board is not None:
                #self.Board.digital[self.Settings.PitchPin].write(self.TargetPitch)
                self.PitchPin.write(self.TargetPitch)
            self.Pitch = self.TargetPitch
    # ------------------------------------------------------------------------------------------

    def get_yaw_pitch(self):
        return self.Yaw, self.Pitch
    # ------------------------------------------------------------------------------------------

    def read_yaw_pitch(self):
        yaw = 0
        pitch = 0
        if self.Board is not None:
            yaw = self.Board.digital[self.Settings.YawPin].read()
        if self.Board is not None:
            pitch = self.Board.digital[self.Settings.PitchPin].read()
        return yaw, pitch
    # ------------------------------------------------------------------------------------------
