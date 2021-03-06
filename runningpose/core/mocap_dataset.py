# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/03_mocap_dataset.ipynb (unless otherwise specified).

__all__ = ['MocapDataset']

# Cell
import numpy as np

from .skeleton import Skeleton

# Cell
class MocapDataset:
    """
    Motion capture dataset base class.

    Attributes:
    skeleton -- A skeleton model also known as a kinematic model.
    fps -- Frames per second.
    data -- Must be filled by subclass.
    cameras -- Must be filled by subclass.
    """

    def __init__(self, fps, skeleton):
        self._skeleton = skeleton
        self._fps = fps
        self._data = None
        self._cameras = None

    def remove_joints(self, joints_to_remove):
        """
        Removes specific joints and re-asigns the remaining joints in
        the dataset.
        """
        kept_joints = self._skeleton.remove_joints(joints_to_remove)
        for subject in self._data.keys():
            for action in self._data[subject].keys():
                data = self._data[subject][action]
                if "positions" in data:
                    data["positions"] = data["positions"][:, kept_joints]

    # Bunch of getters.
    def __getitem__(self, key):
        return self._data[key]

    def subjects(self):
        return self._data.keys()

    def fps(self):
        return self._fps

    def skeleton(self):
        return self._skeleton

    def cameras(self):
        return self._cameras