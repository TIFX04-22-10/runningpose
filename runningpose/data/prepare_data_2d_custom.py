# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/13_prepare_data_2d_custom.ipynb (unless otherwise specified).

__all__ = ['output_prefix_2d', 'decode', 'coco_metadata', 'h36m_metadata', 'suggest_metadata']

# Cell
import argparse
import os
import sys
from glob import glob

import numpy as np

# Cell
output_prefix_2d = 'data_2d_custom_'

# Cell
def decode(filename):
    """Decodes the 2D data and returns a list with a dictionary and the following metadata."""
    print('Processing {}'.format(filename))
    data = np.load(filename, allow_pickle=True)
    boundary_box = data['boxes']
    key_points = data['keypoints']
    metadata = data['metadata'].item()

    results_boundary_box = []
    results_key_points = []
    for i in range(len(boundary_box)):
        if len(boundary_box[i][1]) == 0 or len(key_points[i][1]) == 0:
            # No bbox/keypoints detected for this frame -> will be interpolated.
            # 4 bounding box coordinates.
            results_boundary_box.append(np.full(4, np.nan, dtype=np.float32))
            # 17 COCO keypoints
            results_key_points.append(np.full((17, 4), np.nan, dtype=np.float32))
            continue
        best_match = np.argmax(boundary_box[i][1][:, 4])
        best_boundary_box = boundary_box[i][1][best_match, :4]
        best_key_point = key_points[i][1][best_match].T.copy()
        results_boundary_box.append(best_boundary_box)
        results_key_points.append(best_key_point)

    boundary_box = np.array(results_boundary_box, dtype=np.float32)
    key_points = np.array(results_key_points, dtype=np.float32)
    key_points = key_points[:, :, :2] # Extract (x,y)

    # Fix missing bboxes/keypoints by linear interpolation
    mask = ~np.isnan(boundary_box[:, 0])
    indices = np.arange(len(boundary_box))
    for i in range(4):
        boundary_box[:, i] = np.interp(
            indices, indices[mask], boundary_box[mask, i]
        )

    for i in range(17):
        for j in range(2):
            key_points[:, i, j] = np.interp(
                indices, indices[mask], key_points[mask, i, j]
            )

    print('{} total frames processed'.format(len(boundary_box)))
    print('{} frames were interpolated'.format(np.sum(~mask)))
    print('----------')

    return [{
        'start_frame': 0, # Inclusive
        'end_frame': len(key_points), # Exclusive
        'bounding_boxes': boundary_box,
        'keypoints': key_points,
    }], metadata

# Cell
coco_metadata = {
    'layout_name': 'coco',
    'num_joints': 17,
    'keypoints_symmetry': [
        [1, 3, 5, 7, 9, 11, 13, 15],
        [2, 4, 6, 8, 10, 12, 14, 16],
    ]
}

# Cell
h36m_metadata = {
    'layout_name': 'h36m',
    'num_joints': 17,
    'keypoints_symmetry': [
        [4, 5, 6, 11, 12, 13],
        [1, 2, 3, 14, 15, 16],
    ]
}

# Cell
def suggest_metadata(name):
    """Returns the metadata for a specific dataset."""
    names = []
    for metadata in [coco_metadata, h36m_metadata]:
        if metadata['layout_name'] in name:
            return metadata
        names.append(metadata['layout_name'])
    raise KeyError('Cannot infer keypoint layout from name "{}". Tried {}.'.format(name, names))

# Cell
try: from nbdev.imports import IN_NOTEBOOK
except: IN_NOTEBOOK=False

if __name__ == '__main__' and not IN_NOTEBOOK:
    if os.path.basename(os.getcwd()) != 'data':
        print('This script must be launched from the "data" directory')
        exit(0)

    parser = argparse.ArgumentParser(description='Custom dataset creator')
    parser.add_argument(
        '-i', '--input', type=str, default='',
        metavar='PATH', help='detections directory'
    )
    parser.add_argument(
        '-o', '--output', type=str, default='',
        metavar='PATH', help='output suffix for 2D detections'
    )
    args = parser.parse_args()

    if not args.input:
        print('Please specify the input directory')
        exit(0)

    if not args.output:
        print('Please specify an output suffix (e.g. detectron_pt_coco)')
        exit(0)

    print('Parsing 2D detections from', args.input)

    metadata = suggest_metadata('coco')
    metadata['video_metadata'] = {}

    output = {}
    file_list = glob(args.input + '/*.npz')
    for f in file_list:
        canonical_name = os.path.splitext(os.path.basename(f))[0]
        data, video_metadata = decode(f)
        output[canonical_name] = {}
        output[canonical_name]['custom'] = [data[0]['keypoints'].astype('float32')]
        metadata['video_metadata'][canonical_name] = video_metadata

    print('Saving...')
    np.savez_compressed(
        output_prefix_2d + args.output, positions_2d=output, metadata=metadata
    )
    print('Done.')