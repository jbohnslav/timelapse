import cv2
import argparse
import time
from datetime import datetime
import os
import traceback

settings = [(cv2.CAP_PROP_BRIGHTNESS, 100),
            (cv2.CAP_PROP_CONTRAST, 135)]

properties = {'brightness': cv2.CAP_PROP_BRIGHTNESS,
              'contrast': cv2.CAP_PROP_CONTRAST}

def set_res(cap, width:int, height: int):
    # https://docs.opencv.org/3.4/d4/d15/group__videoio__flags__base.html#gaeb8dd9c89c10a5c63c139bf7c4f5704d
    try:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if actual_width != width or actual_height != height:
            raise ValueError('attempted to set width={}, height={}, actual: width={}, height={}'.format(
                width, height, actual_width, actual_height
            ))

    except Exception as e:
        print(e)
        print('Resolution not supported. w: {}, h: {}'.format(width, height))

def set_max_res(cap):
    widths = [320, 640, 640, 800, 1280, 1440, 1920]
    heights = [240, 360, 480, 600, 720, 900, 1080]
    for width, height in zip(widths, heights):
        set_res(cap, width, height)

def acquisition_loop(args):
    cam = cv2.VideoCapture(args.opencv_id)

    t0 = time.perf_counter()
    first_frame = True
    last_frame_acq = time.perf_counter()
    frame_num = 0
    
    print('initial camera settings')
    for prop, value in properties.items():
        print('{}: {}'.format(prop, cam.get(value)))
        
        
    
    for setting in settings:
        cam.set(setting[0], setting[1])

    if args.preview:
        cv2.namedWindow('preview', cv2.WINDOW_NORMAL)
        font = cv2.FONT_HERSHEY_SIMPLEX
    if args.save:
        starttime = datetime.now().strftime('%y%m%d_%H%M%S')
        savedir = os.path.join(args.save_path, 'timelapse_{}'.format(starttime))
        os.makedirs(savedir)

    try:

        set_max_res(cam)
        
        # it takes a few frames to set brightness, etc
        for i in range(100):
            ret, frame = cam.read()
            # don't do anything with this
        
        while True:
            if time.perf_counter() - last_frame_acq > 1 / args.fps:
                ret, frame = cam.read()
                last_frame_acq = time.perf_counter()

                time_string = datetime.now().strftime('%y%m%d_%H%M%S_%f')
                frame_string = '{}_{:07d}'.format(time_string, frame_num)

                if args.save:
                    fname = os.path.join(savedir, frame_string + '.jpg')

                    cv2.imwrite(fname, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 99])

                if args.preview:
                    height = frame.shape[0]
                    cv2.putText(frame, frame_string, (10, height - 20), font, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                    cv2.imshow('preview', frame)
                    key = cv2.waitKey(1)
                    if key == 27 or key == 113:
                        # escape or q
                        raise KeyboardInterrupt
                frame_num += 1



            total_elapsed = time.perf_counter() - t0
            elapsed_minutes = total_elapsed / 60
            if elapsed_minutes > args.duration:
                break

    except Exception as e:
        print(traceback.format_exc())
        print('Error: {}'.format(e))
        
    finally:
        cv2.destroyAllWindows()
        cam.release()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Acquire time lapse images from USB webcam.')
    parser.add_argument('-d', '--duration', type=int, required=True,
                        help='duration of acquisition in minutes')
    parser.add_argument('--opencv_id', type=int, default=0,
                        help='which integer value the webcam is')
    parser.add_argument('--fps', type=float, default=1.0,
                        help='number of images to acquire per second')
    parser.add_argument('--preview', default=False, action='store_true',
                        help='Whether or not to show preview')
    parser.add_argument('--save', default=False, action='store_true',
                        help='Whether or not to save to disk')
    parser.add_argument('--save_path', type=str, default=None,
                        help='directory to write images to')

    args = parser.parse_args()
    if args.fps > 60:
        raise ValueError('Make fps < 60, not: {}'.format(args.fps))

    if not args.preview and not args.save:
        raise ValueError('Without previewing or saving, script does nothing')

    if args.save_path is None and args.save:
        args.save_path = os.getcwd()

    acquisition_loop(args)
