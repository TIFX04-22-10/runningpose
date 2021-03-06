# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/15_prepare_data_COCO.ipynb (unless otherwise specified).

__all__ = ['INFO', 'LICENSES', 'CATEGORIES', 'parse_args', 'main', 'get_COCO_keypoints']

# Cell
import detectron2
from detectron2 import model_zoo
from detectron2.config import get_cfg
from detectron2.engine import DefaultPredictor
from detectron2.utils.logger import setup_logger

# Workaround for the relative import error,
# removes the dot (.) infront when converting to .py script.
try:
    from .inference import infer_video
    from .pycoco import pycococreatortools as pycoco
except:
    from inference import infer_video
    from pycoco import pycococreatortools as pycoco

import argparse
import datetime
import glob
import json
import os
import time

import pandas as pd


# Cell
# The INFO section contains high level information about the dataset.
INFO = {
    "description": "Runningpose Dataset",
    "url": "https://github.com/TIFX04-22-10/runningpose",
    "version": "1.0.0",
    "year": 2022,
    "contributor": "svenssona",
    "date_created": datetime.datetime.utcnow().isoformat(' ')
}

# Cell
# The “licenses” section contains a list of image licenses
# that apply to images in the dataset.
LICENSES = [
    {
        "id": 1,
        "name": "Creative Commons Attribution 4.0 International",
        "url": "https://dataworldsupport.atlassian.net/servicedesk/customer/portals"
    }
]

# Cell
# In the case of a person, “keypoints” indicate different body parts.
# The “skeleton” indicates connections between points.
# For example, [20, 19] means "HeadFront" connects to "SpineThoracic2".
CATEGORIES = [
   {
        "supercategory": "person",
        "id": 1,
        "name": "person",
        "keypoints": [
            'RAnkle', # 1         #
            'LAnkle', # 2         #
            'RKnee',  # 3
            'LKnee',  # 4
            'RWrist', # 5
            'LWrist', # 6
            'RElbow', # 7
            'LElbow', # 8
            'RForefoot', # 9
            'RTrochanterMajor', # 10       #
            'LForefoot', # 11
            'LTrochanterMajor', # 12       #
            'WaistBack', # 13
            'RShoulderTop', # 14
            'LShoulderTop', # 15
            'SpineThoracic12', # 16
            'SpineThoracic2', # 17
            'HeadFront' # 18
        ],
        "skeleton": [ # 17 connections in total
            [18, 17], [17, 15], [17, 14], [17, 16], [16, 13], [13, 10], [13, 12],
            [10, 3], [3, 1], [1, 9], [12, 4], [4, 2], [2, 11], [14, 7],
            [7, 5], [15, 8], [8, 6]
        ]
    }
]

# Cell
def parse_args():
    parser = argparse.ArgumentParser(
        description='Reformat to COCO-keypoint json format.'
    )
    parser.add_argument(
        '--image-ext',
        dest='image_ext',
        help='image file name extension (default: mp4)',
        default='mp4',
        type=str
    )
    parser.add_argument(
        '--im_or_folder',
        help='image or folder of images',
        default="richardrun2",
        type=str
    )

    return parser.parse_args()

# Cell
def main(args):
    print(os.getcwd())
    """
    Runs inference on the video files and saves the dataset in json
    file format. Predicts the boundary box and segementation points.
    Then adds the Qualisys keypoint data.

    OBS! Make sure video_name matches csv file for 2D keypoints and
    that they are in the same folder.
    """
    # Create a detectron2 config and DefaultPredictor to run inference on video.
    cfg = get_cfg()
    cfg.merge_from_file(model_zoo.get_config_file(
        "COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml"))
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.7 # Set threshold for this model.
    cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url(
        "COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml")
    predictor = DefaultPredictor(cfg)

    # Load the video folder in which we should predict.
    if os.path.isdir(args.im_or_folder):
        im_list = glob.iglob(args.im_or_folder + '/*.' + args.image_ext)
    else:
        im_list = [args.im_or_folder]

    # Initialize coco_outputs, annotation id and video id:
    coco_output = {
        "info": INFO,
        "licenses": LICENSES,
        "categories": CATEGORIES,
        "images": [],
        "annotations": []
    }
    annotation_id = 0
    video_id = 0 # Increases by 1e4 if we have multiple videos.
    for video_name in im_list:
        print("Processing {}".format(video_name))

        # Make sure video_name matches csv file for 2D keypoints
        # and that they are in the same folder.
        # TODO: Change so that it only works for mp4
        keypoints = get_COCO_keypoints(video_name)

        annotation_id = 1
        for frame_i, im in enumerate(infer_video.read_video(video_name)):
            t = time.time()
            outputs = predictor(im)["instances"].to('cpu')
            print("Frame {} processed in {:.3f}s".format(frame_i, time.time()-t))
            # Filter out the person class from the prediction;
            # 0 is the index for persons.
            outputs = outputs[outputs.pred_classes == 0]

            # Checks if image is "empty or not" and makes sure there
            # is only one person detected.
            if outputs.has("pred_boxes") and len(outputs) == 1:
                # Converts the tensors to a numpy arrays and slice away
                # the person class.
                bbox_tensor = outputs.pred_boxes.tensor.numpy()[0, :]
                pred_masks_tensor = outputs.pred_masks.numpy()[0, :, :]

                # Create the image section, it contains the complete list
                # of images in your dataset.
                image_id = video_id + frame_i
                image_info = pycoco.create_image_info(image_id, video_name, im)
                coco_output["images"].append(image_info)

                # Create the annotations in the single person coco-keypoint format.
                annotation_info = pycoco.create_annotation_info(
                    annotation_id,
                    image_id,
                    pred_masks_tensor,
                    bbox_tensor,
                    keypoints=keypoints[frame_i]
                )

                coco_output["annotations"].append(annotation_info)
                annotation_id += 1

                output_name = video_name.replace(".mp4", "").rstrip()

    with open("{}.json".format(output_name), "w") as output_json_file:
        json.dump(coco_output, output_json_file)

    video_id += 1e4

# Cell
def get_COCO_keypoints(video_name):
    """
    Loads the formated qtm data for the video (.mp4) and reformats it to
    COCO format i.e list: [x, y, v, x, y, v, ... x, y, v], where v is a visual
    parameter (0, 1, 2); whether the keypoint is visual and measured.
        0 = not measured.
        1 = measured but not visual.
        2 = measured and visual.

    Returns a list of list with keypoints for each frame.
    """
    file_path = video_name.replace(".mp4", "_2D_keypoints.csv")
    data_2D = pd.read_csv(file_path, index_col=0)

    keypoints = []
    for i in range(0, data_2D.shape[0], 2):
        x_keypoints = list(data_2D.iloc[i, :])
        y_keypoints = list(data_2D.iloc[i+1, :])
        keypoints_one_frame = []
        while(y_keypoints):
            # Remember that pop() reverses the order of the keypoints.
            keypoints_one_frame.append(x_keypoints.pop())
            keypoints_one_frame.append(y_keypoints.pop())
            # Assume v=2 for lack of better way to do it.
            keypoints_one_frame.append(2)

        keypoints.append(keypoints_one_frame)

    return keypoints

# Cell
try: from nbdev.imports import IN_NOTEBOOK
except: IN_NOTEBOOK=False

if __name__ == '__main__' and not IN_NOTEBOOK:
    setup_logger()
    args = parse_args()
    main(args)