import argparse
from SentryTurret import SentryTurret


def main():
    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--video", help="path to the video file")
    ap.add_argument("-a", "--min-area", type=int, default=2000, help="minimum area size")
    args = vars(ap.parse_args())

    sentry_turret = SentryTurret(args)

    sentry_turret.run()
# ------------------------------------------------------------------------------------------


if __name__ == '__main__':
    main()
