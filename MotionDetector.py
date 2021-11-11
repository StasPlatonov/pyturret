from Vector2 import Vector2
from Utils import Utils

import cv2
import imutils
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s [%(thread)d] %(name)s[%(levelname)s]: %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


class MotionDetector(object):

    def __init__(self, settings):
        self.Settings = settings
        self.Detected = False
        self.Capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        #self.Capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        #self.Capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.FirstFrame = None
        self.Frame = None
        self.Thresh = None
        self.FrameDelta = None
        self.Contours = None
        self.gray = None
        self.LastMotionTime = Utils.millis()
        self.Target = Vector2()
        self.Targets = []
        self.TargetPathLen = 20
        self.Speed = Vector2()
        self.Active = False

        logger.info("Initialize...")

        (width, height) = self.get_dimensions()
        logger.info("Capture dimensions: {} x {}".format(width, height))
    # ------------------------------------------------------------------------------------------

    def get_dimensions(self):
        return self.Capture.get(cv2.CAP_PROP_FRAME_WIDTH), self.Capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
    # ------------------------------------------------------------------------------------------

    def get_real_dimensions(self):
        return self.Frame.shape[1], self.Frame.shape[0]
    # ------------------------------------------------------------------------------------------

    def stop(self):
        logger.info("Stopping...")
        self.Capture.release()
        cv2.destroyAllWindows()
    # ------------------------------------------------------------------------------------------

    def draw_cross(self, point, size):
        cv2.line(self.Frame, (int(point.X - size / 2), int(point.Y)), (int(point.X + size / 2), int(point.Y)),
                 (0, 255, 0))
        cv2.line(self.Frame, (int(point.X), int(point.Y - size / 2)), (int(point.X), int(point.Y + size / 2)),
                 (0, 255, 0))
    # ------------------------------------------------------------------------------------------

    def draw_text(self, text, x, y, scale, color, thickness):
        cv2.putText(self.Frame, text, (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness)
    # ------------------------------------------------------------------------------------------

    def draw(self):
        self.draw_cross(self.Target, 20)

        for i in range(0, len(self.Targets) - 1):
            target = self.Targets[i]
            next_target = self.Targets[i+1]
            cv2.line(self.Frame, (int(target.X), int(target.Y)), (int(next_target.X), int(next_target.Y)),
                     (0, 255, 0), 2)
    # ------------------------------------------------------------------------------------------

    def flush(self):
        # show the frame and record if the user presses a key
        cv2.imshow("Sentry Turret", self.Frame)
        #cv2.resizeWindow("Sentry Turret", 640, 480)
        #print(str(self.Frame.shape[0]) + " | " + str(self.get_dimensions()[1]))

        if self.Settings.Debug:
            if self.Thresh is not None:
                cv2.imshow("Thresh", self.Thresh)
            if self.FrameDelta is not None:
                cv2.imshow("Frame Delta", self.FrameDelta)
    # ------------------------------------------------------------------------------------------

    def draw_contour(self, x, y, w, h, area):
        cv2.rectangle(self.Frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(
            self.Frame, "{}".format(area),
            (int(x + w / 2), int(y + h / 2)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    # ------------------------------------------------------------------------------------------

    def reset(self):
        logger.info("Reset")
        self.FirstFrame = None
    # ------------------------------------------------------------------------------------------

    def get_last_motion_time(self):
        return self.LastMotionTime
    # ------------------------------------------------------------------------------------------

    def is_detected(self):
        return self.Detected
    # ------------------------------------------------------------------------------------------

    def set_active(self, active):
        self.Active = active
    # ------------------------------------------------------------------------------------------

    # TODO: add prediction
    def get_target(self):
        return self.Target
    # ------------------------------------------------------------------------------------------

    def update(self, delta):
        _, self.Frame = self.Capture.read()

        prev_detected = self.Detected
        self.Detected = False

        # resize the frame, convert it to grayscale, and blur it
        self.Frame = imutils.resize(image=self.Frame, width=500)

        if not self.Active:
            return

        self.gray = cv2.cvtColor(self.Frame, cv2.COLOR_BGR2GRAY)
        self.gray = cv2.GaussianBlur(self.gray, (21, 21), 0)

        # if the first frame is None, initialize it
        if self.FirstFrame is None:
            self.FirstFrame = self.gray
            return

        # compute the absolute difference between the current frame and first frame
        self.FrameDelta = cv2.absdiff(self.FirstFrame, self.gray)

        self.Thresh = cv2.threshold(self.FrameDelta, 50, 255, cv2.THRESH_BINARY)[1]
        # dilate the thresholded image to fill in holes, then find contours on thresholded image
        self.Thresh = cv2.dilate(self.Thresh, None, iterations=2)

        cntrs = cv2.findContours(self.Thresh.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)#RETR_EXTERNAL
        contours = imutils.grab_contours(cntrs)

        summ = Vector2()
        count = 0

        if len(contours) > 0:
            # Use only largest contour or all contours, depending on settings
            if self.Settings.DetectorTraceMaxObject:
                max_contour = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(max_contour)
                if area >= self.Settings.DetectorMinArea:
                    (x, y, w, h) = cv2.boundingRect(max_contour)
                    self.draw_contour(x, y, w, h, area)
                    summ.X = x + w / 2
                    summ.Y = y + h / 2
                    count = 1
                    self.Detected = True
                    self.LastMotionTime = Utils.millis()
            else:
                # loop over the contours
                for contour in contours:
                    # if the contour is too small, ignore it
                    area = cv2.contourArea(contour)
                    if area < self.Settings.DetectorMinArea:
                        continue

                    (x, y, w, h) = cv2.boundingRect(contour)
                    self.draw_contour(x, y, w, h, area)

                    self.Detected = True
                    self.LastMotionTime = Utils.millis()

                    summ.add(x + w / 2, y + h / 2)
                    count += 1

        self.update_targets(summ, count)
    # ------------------------------------------------------------------------------------------

    def update_targets(self, summ, count):
        prev_target = self.Target

        if count > 0:
            self.Target = Vector2(summ.X / count, summ.Y / count)
            self.Targets.append(self.Target)
            if len(self.Targets) > self.TargetPathLen:
                self.Targets.pop(0)
        else:
            if len(self.Targets) > 0:
                self.Targets.pop(0)

        self.Speed = (self.Target.X - prev_target.X, self.Target.Y - prev_target.Y)
    # ------------------------------------------------------------------------------------------
