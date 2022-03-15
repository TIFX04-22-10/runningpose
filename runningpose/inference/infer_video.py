# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/14_infer_video.ipynb (unless otherwise specified).

__all__ = ['parse_args', 'get_resolution', 'read_video', 'main']

# Cell
import detectron2
from detectron2.utils.logger import setup_logger
from detectron2.config import get_cfg
from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor

import subprocess as sp
import numpy as np
import time
import argparse
import sys
import os
import glob

# Cell
def parse_args():
    parser = argparse.ArgumentParser(description='End-to-end inference')
    parser.add_argument(
        '--cfg',
        dest='cfg',
        help='cfg model file (/path/to/model_config.yaml)',
        default=None,
        type=str
    )
    parser.add_argument(
        '--output-dir',
        dest='output_dir',
        help='directory for visualization pdfs (default: /tmp/infer_simple)',
        default='/tmp/infer_simple',
        type=str
    )
    parser.add_argument(
        '--image-ext',
        dest='image_ext',
        help='image file name extension (default: mp4)',
        default='mp4',
        type=str
    )
    parser.add_argument(
        'im_or_folder', help='image or folder of images', default=None
    )
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    return parser.parse_args()

# Cell
def get_resolution(filename):
    """Returns the width and height for a given video file."""
    command = ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
               '-show_entries', 'stream=width,height', '-of', 'csv=p=0', filename]
    pipe = sp.Popen(command, stdout=sp.PIPE, bufsize=-1)
    for line in pipe.stdout:
        w, h = line.decode().strip().split(',')
        return int(w), int(h)

# Cell
def read_video(filename):
    """Loads a given video file and returns it as a data generator."""
    w, h = get_resolution(filename)

    command = ['ffmpeg',
            '-i', filename,
            '-f', 'image2pipe',
            '-pix_fmt', 'bgr24',
            '-vsync', '0',
            '-vcodec', 'rawvideo', '-']

    pipe = sp.Popen(command, stdout=sp.PIPE, bufsize=-1)
    while True:
        data = pipe.stdout.read(w*h*3)
        if not data:
            break
        yield np.frombuffer(data, dtype='uint8').reshape((h, w, 3))

# Cell
def main(args):
    """
    Runs inference on the video files and saves the dataset in .npz file format.
    Predicts the boundary box and the coco keypoints.
    """
    # Create a detectron2 config and a detectron2 DefaultPredictor to run inference on video.
    cfg = get_cfg()
    cfg.merge_from_file(model_zoo.get_config_file(args.cfg))
    cfg.MODEL.ROI_HEADS.SCORE_TRESH_TEST = 0.7 # Set threshold for this model.
    cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url(args.cfg)
    predictor = DefaultPredictor(cfg)

    # Load the video folder in which we should predict.
    if os.path.isdir(args.im_or_folder):
        im_list = glob.iglob(args.im_or_folder + '/*.' + args.image_ext)
    else:
        im_list = [args.im_or_folder]

    for video_name in im_list:
        out_name = os.path.join(args.output_dir, os.path.basename(video_name))
        print("Processing {}".format(video_name))

        # Initialize results:
        boundary_boxes = []
        segments = [] # Sets to None.
        keypoints = []
        for frame_i, im in enumerate(read_video(video_name)):
            t = time.time()
            outputs = predictor(im)['instances'].to('cpu')
            print("Frame {} processed in {:.3f}s".format(frame_i, time.time()-t))

            # Checks if image is "empty or not".
            has_bbox = False
            if outputs.has('pred_boxes'):
                bbox_tensor = outputs.pred_boxes.tensor.numpy()
                if len(bbox_tensor) > 0:
                    has_bbox = True
                    scores = outputs.scores.numpy()[:, None]
                    bbox_tensor = np.concatenate((bbox_tensor, scores), axis=1)

            if has_bbox:
                kps = outputs.pred_keypoints.numpy()
                kps_xy = kps[:, :, :2]
                kps_prob = kps[:, :, 2:3]
                kps_logit = np.zeros_like(kps_prob) # Dummy variable.
                kps = np.concatenate((kps_xy, kps_logit, kps_prob), axis=2)
                kps = kps.transpose(0, 2, 1)
            else:
                kps = []
                bbox_tensor = []

            # Mimic Detectron1 format
            cls_boxes = [[], bbox_tensor]
            cls_keyps = [[], kps]

            boundary_boxes.append(cls_boxes)
            segments.append(None)
            keypoints.append(cls_keyps)

        # Video resolution.
        metadata = {
            'w': im.shape[1],
            'h': im.shape[0],
        }

        np.savez_compressed(out_name, boxes=boundary_boxes, segments=segments, keypoints=keypoints, metadata=metadata)

# Cell
try: from nbdev.imports import IN_NOTEBOOK
except: IN_NOTEBOOK=False

if __name__ == '__main__' and not IN_NOTEBOOK:
    setup_logger()
    args = parse_args()
    main(args)