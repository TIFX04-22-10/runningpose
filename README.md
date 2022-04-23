# RunningPose
> A 3D pose estimator for runners. 


This is the implementation of the approach for the candidate project TIFX04-22-10 at Chalmers University of Technology. The approach is described in the [candidate report](). It is an adaption of the machine learning model [VideoPose3D] (https://github.com/facebookresearch/VideoPose3D) made by Meta Research.


## Description
Runningpose predicts keypoints in 3D, and is especially made to be used for gait analysis on running humans using monocular vision. To predict 3D keypoints Detectron2 is first used to predict 2D keypoints. Temporal convolution network (TCN) is then used for lifting, that is predicting 3D keypoints using the 2D keypoints.

Using tranfer learning with a pretrained model for VideoPose3D a model has been trained with a custom dataset, RunningPose dataset. The dataset was made in collaboration with [Qualisys](https://www.qualisys.com) and [Swedish Athletics Association](https://www.friidrott.se).

The model predicts keypoints that has been identified as especially important regarding gait analysis for running humans. One main difference between this model and the pretrained model for VideoPose3D is that a keypoint on each the foot is predicted, wich the VideoPose3D model does not do.

## Results on the RunningPose dataset
The mean per-joint position error (MPJPE) is shown in the table below.



## Quick start
To get started quickly, follow these instructions. This will allow you to do inference on in the wild and produce basic visualizations. For more detailed instructions, plese refer to the original model [VideoPose3D] (https://github.com/facebookresearch/VideoPose3D).

### Dependencies
Make sure you have the following dependencies installed before proceeding:
- Python 3+ distribution
- PyTorch >= 0.4.0

Optional:
- Matplotlib, if you want to visualize predictions. Additionally, you need *ffmpeg* to export MP4 videos, and *imagemagick* to export GIFs.

### Inference
Videos used for inference should only contain one person. The instructions below show how to prepare the trained model, do optional video processing, infer 2D keypoints, create a custom dataset for the videos, and then do the inference and visualize the results.

#### Step 1: setup
Download the [pretrained model]() for generating 3D predictions. Can it not just be left in the correct place?


#### Step 2: (optional): video preprocessing




#### Step 3: inferring 2D keypoints with Detectron




#### Step 4: creating a custom dataset




#### Step 5: rendering a custom video and exporting coordinates








