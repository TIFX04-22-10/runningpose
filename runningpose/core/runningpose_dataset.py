# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/18_runningpose_dataset.ipynb (unless otherwise specified).

__all__ = ['RunningposeDataset', 'runningpose_skeleton', 'runningpose_cameras_intrinsic_params',
           'runningpose_cameras_extrinsic_params']

# Cell
import numpy as np
import copy
from .skeleton import Skeleton
from .mocap_dataset import MocapDataset
from .camera import normalize_screen_coordinates

# Cell
class RunningposeDataset(MocapDataset):
    """Runningpose pose estimation dataset."""
    def __init__(self, path):
        super().__init__(fps=85, skeleton=runningpose_skeleton)
        self.cameras = copy.deepcopy(runningpose_cameras_extrinsic_params)

        for cameras in self._cameras.values():
            for i, cam in enumerate(cameras):
                cam.update(runningpose_cameras_intrinsic_params[i])
                for k, v in cam.items():
                    if k not in ["id", "res_w", "res_h"]:
                        cam[k] = np.array(v, dtype='float32')

        # Normalize camera frame.
        cam['center'] = normalize_screen_coordinates(
            cam['center'], w=cam['res_w'], h=cam['res_h']).astype('float32')
        cam['focal_length'] = cam['focal_length']/cam['res_w']*2
        if 'translation' in cam:
            cam['translation'] = cam['translation']/1000 # Milimeters to meters.
        # Add intrinsic parameters vector.
        cam['intrinsic'] = np.concatenate(
            (cam['focal_length'], cam['center'],
            cam['radial_distortion'], cam['tangential_distortion']))

        # Load serialized dataset.
        data = np.load(path, allow_pickle=True)['positions_3d'].item()

        self._data = {}
        for subject, actions in data.items():
            self._data[subject] = {}
            for action_name, positions in actions.items():
                self._data[subject][action_name] = {
                    'positions': positions,
                    'cameras': self._cameras[subject],
                }

# Cell
runningpose_skeleton = Skeleton( #TODO: fix skeleton
       parents=[2, 3, 9, 11, 6, 7, 13, 14, 0, 12, 1, 12, 15, 16, 16, 16, 17, -1],
       joints_left=[1, 3, 5, 7, 10, 11, 14],
       joints_right=[0, 2, 4, 6, 8, 9, 13]
)
#'RAnkle', 'LAnkle','RKnee', 'LKnee', 'RWrist', 'LWrist', 'RElbow', 'LElbow', 'RForefoot2', 'RThigh2', 'LForefoot2',
#'LThigh2', 'WaistBack', 'RShoulderTop', 'LShoulderTop', 'SpineThoracic12', 'SpineThoracic2', 'HeadFront'

# Cell
runningpose_cameras_intrinsic_params = [
    {
        'id': 'miqusVideo1',
        'center': [60818.726563, 32822.339844],
        'focal_length': [107467.257813, 107467.640625],
        'radial_distortion': [-0.045952, 0.137059, 0.000000],
        'tangential_distortion': [0.000110, 0.000532],
        'res_w': 1920,
        'res_h': 1080,
        'azimuth': 70, # Only used for visualization
    },
    {
        'id': 'miqusVideo2',
        'center': [61535.457031, 529684.667969],
        'focal_length': [106897.671875, 106903.906250],
        'radial_distortion': [-0.044311, 0.129243,0.000000],
        'tangential_distortion': [0.000380, 0.000067],
        'res_w': 1920,
        'res_h': 1080,
        'azimuth': 70, # Only used for visualization
    },
    {
        'id': 'miqusVideo3',
        'center': [60224.542969, 33399.539063],
        'focal_length': [107180.078125, 107196.359375],
        'radial_distortion': [-0.044245,0.134407, 0.000000],
        'tangential_distortion': [0.000612, 0.000214],
        'res_w': 1920,
        'res_h': 1080,
        'azimuth': 70, # Only used for visualization
    }
]

# Cell
runningpose_cameras_extrinsic_params = [
    {   # Miqus video camera 1
        'rotation': np.array([
            [0.735354, 0.677463, 0.017256],
            [-0.104186, 0.087855, 0.990670],
            [0.669627, -0.730291, 0.135186]
        ]),
        'translation': [6643.345215, -2730.456543, 1153.752808],
    },
    {   # Miqus video camera 2
        'rotation': np.array([
            [0.997871, -0.064902, 0.006349],
            [-0.006020, 0.005255, 0.999968],
            [-0.064933, -0.997878 , 0.004853]
        ]),
        'translation': [-697.331482, -2968.999268, 1121.579468],
    },
    {   # Miqus video camera 3
        'rotation': np.array([
            [-0.641654, 0.766908, 0.011533],
            [-0.137808, -0.130067, 0.981882],
            [0.754513, 0.628438, 0.189144]
        ]),
        'translation': [14351.271484, 3795.722412, 1504.888672],
    },
]