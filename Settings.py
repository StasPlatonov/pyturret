import xml.etree.ElementTree as ET
#from xml.dom import minidom

import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s [%(thread)d] %(name)s[%(levelname)s]: %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


class Settings(object):

    def __init__(self, source):
        self.Source = source
        self.Debug = False
        self.InitTime = 0
        self.WarningTime = 0
        self.DetectorMinArea = 2000
        self.DetectorTraceMaxObject = True
        self.ActivatedPingRate = 2000
        self.WarningPingRate = 500
        self.ShooterRate = 1000
        self.ShooterAmmo = 100

        self.TurretPort = "COM1"
        self.TurretYawMin = -45
        self.TurretYawMax = 45
        self.TurretPitchMin = -30
        self.TurretPitchMax = 30
        self.YawPin = 0
        self.PitchPin = 1

        self.SoundEnabled = False

        self.load()
    # ------------------------------------------------------------------------------------------

    def load(self):
        try:
            tree = ET.parse(self.Source)
            settings_item = tree.getroot()

            self.Debug = True if settings_item.attrib['debug'] == "1" else False
            self.InitTime = int(settings_item.attrib['init_time'])
            self.WarningTime = int(settings_item.attrib['warning_time'])
            self.ActivatedPingRate = int(settings_item.attrib['activated_ping_rate'])
            self.WarningPingRate = int(settings_item.attrib['warning_ping_rate'])

            det_item = settings_item.find('detector')
            self.DetectorMinArea = int(det_item.attrib['min_area'])
            self.DetectorTraceMaxObject = True if det_item.attrib['trace_max_object'] == "1" else False

            shooter_item = settings_item.find('shooter')
            self.ShooterRate = int(shooter_item.attrib['rate'])
            self.ShooterAmmo = int(shooter_item.attrib['ammo'])

            turret_item = settings_item.find('turret')
            self.TurretPort = turret_item.attrib['port']
            self.TurretYawMin = int(turret_item.attrib['yaw_min'])
            self.TurretYawMax = int(turret_item.attrib['yaw_max'])
            self.TurretPitchMin = int(turret_item.attrib['pitch_min'])
            self.TurretPitchMax = int(turret_item.attrib['pitch_max'])
            self.YawPin = int(turret_item.attrib['yaw_pin'])
            self.PitchPin = int(turret_item.attrib['pitch_pin'])

            sound_item = settings_item.find('sound')
            self.SoundEnabled = True if sound_item.attrib['enabled'] == "1" else False
        except Exception as e:
            logger.error("Failed to load settings: " + str(e))
    # ------------------------------------------------------------------------------------------
