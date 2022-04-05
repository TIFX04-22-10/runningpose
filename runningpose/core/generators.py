# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/08_generators.ipynb (unless otherwise specified).

__all__ = ['ChunkedGenerator', 'UnchunkedGenerator']

# Cell
from itertools import zip_longest
import numpy as np

# Cell
class ChunkedGenerator:
    """
    Batched data generator, used for training.
    The sequences are split into equal-length chunks and padded as necessary.

    Arguments:
    batch_size -- The batch size to use for training.
    cameras -- List of cameras, one element for each video
        (optional, used for semi-supervised training).

    poses_3d -- List of ground-truth 3D poses, one element for each video
        (optional, used for supervised training).

    poses_2d -- List of input 2D keypoints, one element for each video.

    chunk_length -- Number of output frames to predict for each training
        example (usually 1).

    pad -- 2D input padding to compensate for valid convolutions,
        per side (depends on the receptive field).

    causal_shift -- Asymmetric padding offset when causal convolutions
         are used (usually 0 or "pad").
    shuffle -- Randomly shuffle the dataset before each epoch.
    random_seed -- Initial seed to use for the random generator.
    augment -- Augment the dataset by flipping poses horizontally.

    kps_left and kps_right -- List of left/right 2D keypoints if
        flipping is enabled.

    joints_left and joints_right -- List of left/right 3D joints if
        flipping is enabled.
    """
    def __init__(
            self, batch_size, cameras, poses_3d, poses_2d, chunk_length, pad=0,
            causal_shift=0, shuffle=True,random_seed=47, augment=False,
            kps_left=None, kps_right=None, joints_left=None,
            joints_right=None, endless=False):

        assert poses_3d is None or len(poses_3d) == len(poses_2d), "Number of 3D poses and 2D poses differ."
        assert cameras is None or len(cameras) == len(poses_2d)

        # Build lineage info
        pairs = [] # (seq_idx, start_frame, end_frame, flip) tuples
        for i in range(len(poses_2d)):
            n_chunks = (poses_2d[i].shape[0] + chunk_length - 1) // chunk_length
            offset = (n_chunks * chunk_length - poses_2d[i].shape[0]) // 2
            bounds = np.arange(n_chunks+1)*chunk_length - offset
            augment_vector = np.full(len(bounds - 1), False, dtype=bool)
            pairs += zip(np.repeat(
                i, len(bounds - 1)), bounds[:-1], bounds[1:], augment_vector)
            if augment:
                pairs += zip(np.repeat(
                    i, len(bounds - 1)), bounds[:-1], bounds[1:], ~augment_vector)

        # Initialize buffers
        if cameras is not None:
            self.batch_cam = np.empty((batch_size, cameras[0].shape[-1]))
        if poses_3d is not None:
            self.batch_3d = np.empty((
                batch_size, chunk_length,
                poses_3d[0].shape[-2], poses_3d[0].shape[-1]
            ))
        self.batch_2d = np.empty((
            batch_size, chunk_length + 2*pad,
            poses_2d[0].shape[-2], poses_2d[0].shape[-1]
        ))

        # Initialize instance variables.
        self.num_batches = (len(pairs) + batch_size - 1) // batch_size
        self.batch_size = batch_size
        self.random = np.random.RandomState(random_seed)
        self.pairs = pairs
        self.shuffle = shuffle
        self.pad = pad
        self.causal_shift = causal_shift
        self.endless = endless
        self.state = None

        self.cameras = cameras
        self.poses_3d = poses_3d
        self.poses_2d = poses_2d

        self.augment = augment
        self.kps_left = kps_left
        self.kps_right = kps_right
        self.joints_left = joints_left
        self.joints_right = joints_right

        def num_frames(self):
            """Returns the total number of frames that we train on."""
            return self.num_batches * self.batch_size

        def random_state(self):
            """Returns the random state used by the chunked generator."""
            return self.random

        def set_random_state(self, random):
            """Sets the random state for the chunked generator."""
            self.random = random

        def augment_enabled(self):
            """Returns a boolean if we use data-augmentation or not."""
            return self.augment

        def next_pairs(self):
            """Returns the next pairs or None. Can also shuffle the data."""
            if self.state is None:
                if self.shuffle:
                    pairs = self.random.permutation(self.pairs)
                else:
                    pairs = self.pairs
                return 0, pairs
            else:
                return self.state

        def next_epoch(self):
            """
            Sets up the next forward pass + backward pass for all the
            training samples.
            Returns (or yields) a generator object.
            """
            enabled = True
            while enabled:
                start_idx, pairs = self.next_pairs()
                for batch_index in range(start_idx, self.num_batches):
                    chunks = pairs[
                        batch_index*batch_size : (batch_index+1)*self.batch_size
                    ]
                    for i, (seq_idx, start_3d, end_3d, flip) in enumerate(chunks):
                        start_2d = start_3d - self.pad - self.causal_shift
                        end_2d = end_3d + self.pad - self.causal_shift

                        # 2D poses
                        seq_2d = self.poses_2d[seq_idx]
                        low_2d = max(start_2d, 0)
                        high_2d = min(end_2d, seq_2d.shape[0])
                        pad_left_2d = low_2d - start_2d
                        pad_right_2d = end_2d - high_2d
                        if pad_left_2d != 0 or pad_right_2d != 0:
                            self.batch_2d[i] = np.pad(
                                seq_2d[low_2d:high_2d],
                                ((pad_left_2d, pad_right_2d),
                                (0, 0), (0, 0)), 'edge'
                            )
                        else:
                            self.batch_2d[i] = seq_2d[low_2d:high_2d]

                        if flip:
                            # Flip 2D keypoints
                            self.batch_2d[i, :, :, 0] *= -1
                            self.batch_2d[
                                i, :, self.kps_left + self.kps_right
                            ] = self.batch_2d[
                                i, :, self.kps_right + self.kps_left
                            ]

                        # 3D poses
                        if self.poses_3d is not None:
                            seq_3d = self.poses_3d[seq_idx]
                            low_3d = max(start_3d, 0)
                            high_3d = min(end_3d, seq_3d.shape[0])
                            pad_left_3d = low_3d - start_3d
                            pad_right_3d = end_3d - high_3d
                            if pad_left_3d != 0 or pad_right_3d != 0:
                                self.batch_3d[i] = np.pad(
                                    seq_3d[low_3d:high_3d],
                                    ((pad_left_3d, pad_right_3d),
                                    (0, 0), (0, 0)), 'edge'
                                )
                            else:
                                self.batch_3d[i] = seq_3d[low_3d:high_3d]

                            if flip:
                                # Flip 3D joints
                                self.batch_3d[i, :, :, 0] *= -1
                                self.batch_3d[
                                    i, :, self.joints_left + self.joints_right
                                ] = self.batch_3d[
                                    i, :, self.joints_right + self.joints_left
                                ]

                        # Cameras
                        if self.cameras is not None:
                            self.batch_cam[i] = self.cameras[seq_idx]
                            if flip:
                                # Flip horizontal distortion coefficients
                                self.batch_cam[i, 2] *= -1
                                self.batch_cam[i, 7] *= -1

                    if self.endless:
                        self.state = (batch_index + 1, pairs)
                    if self.poses_3d is None and self.cameras is None:
                        yield None, None, self.batch_2d[:len(chunks)]
                    elif self.poses_3d is not None and self.cameras is None:
                        yield None, self.batch_3d[:len(chunks)], self.batch_2d[:len(chunks)]
                    elif self.poses_3d is None:
                        yield self.batch_cam[:len(chunks)], None, self.batch_2d[:len(chunks)]
                    else:
                        yield self.batch_cam[:len(chunks)], self.batch_3d[:len(chunks)], self.batch_2d[:len(chunks)]

                if self.endless:
                    self.state = None
                else:
                    enabled = False

# Cell
class UnchunkedGenerator:
    """
    Non-batched data generator, used for testing.
    Sequences are returned one at a time (i.e. batch size = 1),
    without chunking.

    If data augmentation is enabled, the batches contain two sequences
    (i.e. batch size = 2),the second of which is a mirrored version of
    the first.

    Arguments:
    cameras -- list of cameras, one element for each video
        (optional, used for semi-supervised training)

    poses_3d -- list of ground-truth 3D poses, one element for each video
        (optional, used for supervised training)

    poses_2d -- list of input 2D keypoints, one element for each video

    pad -- 2D input padding to compensate for valid convolutions,
        per side (depends on the receptive field)

    causal_shift -- asymmetric padding offset when causal convolutions
        are used (usually 0 or "pad")

    augment -- augment the dataset by flipping poses horizontally

    kps_left and kps_right -- list of left/right 2D keypoints if
        flipping is enabled

    joints_left and joints_right -- list of left/right 3D joints if
        flipping is enabled
    """

    def __init__(
            self, cameras, poses_3d, poses_2d, pad=0, causal_shift=0,
            augment=False, kps_left=None, kps_right=None,
            joints_left=None, joints_right=None):

        assert poses_3d is None or len(poses_3d) == len(poses_2d)
        assert cameras is None or len(cameras) == len(poses_2d)

        self.augment = augment
        self.kps_left = kps_left
        self.kps_right = kps_right
        self.joints_left = joints_left
        self.joints_right = joints_right

        self.pad = pad
        self.causal_shift = causal_shift
        self.cameras = [] if cameras is None else cameras
        self.poses_3d = [] if poses_3d is None else poses_3d
        self.poses_2d = poses_2d

    def num_frames(self):
        """Returns the total number of frames that we test on."""
        count = 0
        for pose in self.poses_2d:
            count += pose.shape[0]
        return count

    def augment_enabled(self):
        """Returns a boolean if we use data augmentation or not."""
        return self.augment

    def set_augment(self, augment):
        """Turn on and turn off data augmentation."""
        self.augment = augment

    def next_epoch(self):
        """
        Sets up the next forward pass for all the test samples.
        Returns (or yields) a generator object.
        """

        for seq_cam, seq_3d, seq_2d in zip_longest(
                self.cameras, self.poses_3d, self.poses_2d):

            batch_cam = None if seq_cam is None else np.expand_dims(seq_cam, axis=0)
            batch_3d = None if seq_3d is None else np.expand_dims(seq_3d, axis=0)
            # a and b are help variables only.
            a, b = self.pad + self.causal_shift, self.pad - self.causal_shift
            batch_2d = np.expand_dims(np.pad(
                seq_2d,((a, b), (0, 0), (0, 0)), 'edge'), axis=0
            )

        if self.augment:
                # Append flipped version
                if batch_cam is not None:
                    batch_cam = np.concatenate((batch_cam, batch_cam), axis=0)
                    batch_cam[1, 2] *= -1
                    batch_cam[1, 7] *= -1

                if batch_3d is not None:
                    batch_3d = np.concatenate((batch_3d, batch_3d), axis=0)
                    batch_3d[1, :, :, 0] *= -1
                    batch_3d[1, :, self.joints_left + self.joints_right] \
                         = batch_3d[1, :, self.joints_right + self.joints_left]

                batch_2d = np.concatenate((batch_2d, batch_2d), axis=0)
                batch_2d[1, :, :, 0] *= -1
                batch_2d[1, :, self.kps_left + self.kps_right] \
                    = batch_2d[1, :, self.kps_right + self.kps_left]

        yield batch_cam, batch_3d, batch_2d