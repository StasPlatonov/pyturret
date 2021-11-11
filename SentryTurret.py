from MotionDetector import MotionDetector
from TurretController import TurretController
from Settings import Settings
from Utils import Utils
import cv2
import enum
import datetime
import random
from playsound import playsound

import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s [%(thread)d] %(name)s[%(levelname)s]: %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


class SentryTurretState(enum.Enum):
    STATE_UNKNOWN = 0
    STATE_INIT = 1
    STATE_ACTIVATED = 2
    STATE_WARNING = 3
    STATE_DETECTED = 4
    STATE_OUT_OF_AMMO = 5


class SentrySoundType(enum.Enum):
    SND_INIT = 0
    SND_ACTIVATE = 1
    SND_PING = 2
    SND_SHOOT_1 = 3
    SND_SHOOT_2 = 4
    SND_OUT_OF_AMMO = 5


class SentryTurret(object):

    def __init__(self, args):
        self.Args = args
        self.NeedExit = False
        self.Settings = Settings("Settings.xml")
        self.Detector = MotionDetector(self.Settings)
        self.ScreenDimensions = self.Detector.get_dimensions()
        self.Turret = TurretController(self.Settings)
        self.StartTime = Utils.millis()
        self.CurrentTime = self.StartTime
        self.LastTime = self.StartTime
        self.WarningTime = self.StartTime
        self.LastShootTime = self.StartTime
        self.LastPingTime = self.StartTime
        self.State = SentryTurretState.STATE_UNKNOWN
        self.Ammo = self.Settings.ShooterAmmo

        self.Sounds = dict()
        self.Sounds = {SentrySoundType.SND_INIT: "data/turret_init.wav",
                       SentrySoundType.SND_ACTIVATE: "data/turret_activate.wav",
                       SentrySoundType.SND_PING: "data/turret_ping.wav",
                       SentrySoundType.SND_SHOOT_1: "data/turret_shoot_1.wav",
                       SentrySoundType.SND_SHOOT_2: "data/turret_shoot_2.wav",
                       SentrySoundType.SND_OUT_OF_AMMO: "data/turret_out_of_ammo.wav"}

        self.set_state(SentryTurretState.STATE_INIT)
    # ------------------------------------------------------------------------------------------

    def process_input(self):
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            self.NeedExit = True
        if key == ord("r"):
            self.Detector.reset()
    # ------------------------------------------------------------------------------------------

    def play_sound(self, sound_id):
        if not self.Settings.SoundEnabled:
            return

        if sound_id not in self.Sounds.keys():
            logger.error("Failed to find sound " + str(sound_id))
            return

        playsound(self.Sounds.get(sound_id), False)
    # ------------------------------------------------------------------------------------------

    def run(self):
        logger.info("Starting...")

        while not self.NeedExit:
            self.update()
            self.draw()

        logger.info("Stopping...")
        # cleanup the camera and close any open windows
        self.Detector.stop()
    # ------------------------------------------------------------------------------------------

    def was_motion_within(self, time):
        return self.CurrentTime - self.Detector.get_last_motion_time() < time
    # ------------------------------------------------------------------------------------------

    def update(self):
        self.CurrentTime = Utils.millis()
        delta = self.CurrentTime - self.LastTime
        self.LastTime = self.CurrentTime

        # Wait for some time after initializing and activate then
        if self.State == SentryTurretState.STATE_INIT:
            if self.CurrentTime - self.StartTime > self.Settings.InitTime:
                self.set_state(SentryTurretState.STATE_ACTIVATED)

        self.process_input()

        self.Detector.update(delta)

        # Reset detection
        #if self.CurrentTime - self.Detector.get_last_motion_time() > 3000:
        #    self.Detector.reset()

        # Activated state
        if self.State == SentryTurretState.STATE_ACTIVATED:
            # Just ping with some interval
            if self.CurrentTime - self.LastPingTime > self.Settings.ActivatedPingRate:
                self.play_sound(SentrySoundType.SND_PING)
                self.LastPingTime = self.CurrentTime

            if self.Detector.is_detected():
                self.set_state(SentryTurretState.STATE_WARNING)

        # Warning state
        if self.State == SentryTurretState.STATE_WARNING:
            # Just ping with some interval
            if self.CurrentTime - self.LastPingTime > self.Settings.WarningPingRate:
                self.play_sound(SentrySoundType.SND_PING)
                self.LastPingTime = self.CurrentTime

            if self.CurrentTime - self.WarningTime > self.Settings.WarningTime:
                if self.Detector.is_detected():
                    #if self.was_motion_within(1000):
                    self.set_state(SentryTurretState.STATE_DETECTED)
                else:
                    self.set_state(SentryTurretState.STATE_ACTIVATED)

        # Detected state
        if self.State == SentryTurretState.STATE_DETECTED:
            if not self.Detector.is_detected():
                self.set_state(SentryTurretState.STATE_ACTIVATED)

            if self.CurrentTime - self.LastShootTime > self.Settings.ShooterRate:
                if self.Ammo == 0:
                    self.set_state(SentryTurretState.STATE_OUT_OF_AMMO)
                else:
                    self.shoot()

        self.update_turret(delta)
    # ------------------------------------------------------------------------------------------

    def update_turret(self, delta):
        # Get target coordinates and calculate yaw pitch angles
        target = self.Detector.get_target()

        (scr_width, scr_height) = self.Detector.get_real_dimensions()

        yaw = \
            self.Settings.TurretYawMin + \
            (self.Settings.TurretYawMax - self.Settings.TurretYawMin) / scr_width * target.X
        pitch = \
            self.Settings.TurretPitchMin + \
            (self.Settings.TurretPitchMax - self.Settings.TurretPitchMin) / -scr_height * \
            (target.Y - scr_height)

        self.Turret.set_yaw(yaw)
        self.Turret.set_pitch(pitch)

        # Update turret itself
        self.Turret.update(delta)
    # ------------------------------------------------------------------------------------------

    def shoot(self):
        if self.Ammo > 0:
            snd = random.randint(0, 1)
            if snd == 0:
                self.play_sound(SentrySoundType.SND_SHOOT_1)
            elif snd == 1:
                self.play_sound(SentrySoundType.SND_SHOOT_2)

            self.Ammo -= 1
            self.LastShootTime = self.CurrentTime + random.randint(0, self.Settings.ShooterRate / 4)
    # ------------------------------------------------------------------------------------------

    def set_state(self, state):
        if self.State == state:
            return

        logger.info("Switching to state " + self.get_state_text(state))

        if self.State == SentryTurretState.STATE_INIT:
            if state == SentryTurretState.STATE_ACTIVATED:
                self.Detector.set_active(True)

        if state == SentryTurretState.STATE_INIT:
            self.play_sound(SentrySoundType.SND_INIT)
            self.Detector.set_active(False)

        if state == SentryTurretState.STATE_WARNING:
            self.WarningTime = self.CurrentTime
            self.play_sound(SentrySoundType.SND_ACTIVATE)

        if state == SentryTurretState.STATE_OUT_OF_AMMO:
            logger.info("Out of ammo")
            self.play_sound(SentrySoundType.SND_OUT_OF_AMMO)

        self.State = state
    # ------------------------------------------------------------------------------------------

    @staticmethod
    def get_state_text(state):
        if state == SentryTurretState.STATE_INIT:
            return "INITIALIZING"
        if state == SentryTurretState.STATE_ACTIVATED:
            return "ACTIVATED"
        if state == SentryTurretState.STATE_WARNING:
            return "WARNING"
        if state == SentryTurretState.STATE_DETECTED:
            return "DETECTED"
        if state == SentryTurretState.STATE_OUT_OF_AMMO:
            return "OUT OF AMMO"
        return "Unknown"
    # ------------------------------------------------------------------------------------------

    @staticmethod
    def get_state_color(state):
        if state == SentryTurretState.STATE_ACTIVATED:
            return (0, 255, 0)
        if state == SentryTurretState.STATE_WARNING:
            return (0, 255, 255)
        if state == SentryTurretState.STATE_DETECTED:
            return (0, 0, 255)
        if state == SentryTurretState.STATE_OUT_OF_AMMO:
            return (0, 0, 255)
        return (255, 255, 255)
    # ------------------------------------------------------------------------------------------

    def draw(self):
        self.Detector.draw()

        self.Detector.draw_text("State:", 4, 20, 0.5, (255, 255, 255), 1)
        self.Detector.draw_text(
            SentryTurret.get_state_text(self.State), 70, 20, 0.5, SentryTurret.get_state_color(self.State), 2)

        self.Detector.draw_text("Ammo:", 4, 40, 0.5, (255, 255, 255), 1)
        self.Detector.draw_text(
            str(self.Ammo), 70, 40, 0.5,
            (0, 255, 0) if self.Ammo > 50 else (0, 255, 255) if self.Ammo > 15 else (0, 0, 255), 2)

        target = self.Detector.get_target()
        self.Detector.draw_text("Target: {:2.1f} {:2.1f}".format(target.X, target.Y), 4, 60, 0.5, (255, 255, 255), 1)

        (yaw, pitch) = self.Turret.get_yaw_pitch()
        (r_yaw, r_pitch) = self.Turret.read_yaw_pitch()
        self.Detector.draw_text("YP: {:2.1f}({:2.1f}) {:2.1f}({:2.1f})".format(yaw, r_yaw, pitch, r_pitch), 4, 80, 0.5, (0, 0, 0), 1)

        #print(str(self.Detector.get_dimensions()[1]) + " " + str(self.Detector.get_height()))
        self.Detector.draw_text(
            datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
            10, self.Detector.get_real_dimensions()[1] - 10,
            0.35,
            (255, 255, 255),
            1)

        self.Detector.flush()
    # ------------------------------------------------------------------------------------------
