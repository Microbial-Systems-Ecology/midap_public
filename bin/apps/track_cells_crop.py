import numpy as np
import glob

import argparse
import os
import re

from midap.tracking.tracking import Tracking
from midap.utils import get_logger

parser = argparse.ArgumentParser()
parser.add_argument('--path', type=str, required=True, help='path to folder for one with specific channel')
parser.add_argument("--loglevel", type=int, default=7, help="Loglevel of the script.")
args = parser.parse_args()

# logging
logger = get_logger(__file__, args.loglevel)
logger.info(f"Starting tracking for: {args.path}")

# Load data
images_folder = os.path.join(args.path, 'cut_im')
segmentation_folder = os.path.join(args.path, 'seg_im')
output_folder = os.path.join(args.path, 'track_output')
model_file = '../model_weights/model_weights_tracking/unet_pads_track.hdf5'

# glob all the cut images and segmented images
img_names_sort = np.sort(glob.glob(os.path.join(images_folder, '*frame*.png')))
seg_names_sort = np.sort(glob.glob(os.path.join(segmentation_folder, '*frame*.png')))

# Parameters:
crop_size = (128, 128)
target_size = (512, 512)
input_size = crop_size + (4,)
num_time_steps = len(img_names_sort)

# Process
tr = Tracking(img_names_sort, seg_names_sort, model_file,
              input_size, target_size, crop_size)
tr.track_all_frames_crop()

# Reduce results file for storage if there is a tracking result
if sum([res.size for res in tr.results_all]) > 0:
    logger.info("Saving results of tracking...")
    # the first might be emtpy
    results_all_red = np.zeros(
        (len(tr.results_all), ) + tr.results_all[0].shape[1:3] + (2,))

    for t in range(len(tr.results_all)):
        for ix, cell_id in enumerate(tr.results_all[t]):
            if cell_id[:, :, 0].sum() > 0:
                results_all_red[t, cell_id[:, :, 0] > 0, 0] = ix+1
            if cell_id[:, :, 1].sum() > 0:
                results_all_red[t, cell_id[:, :, 1] > 0, 1] = ix+1

    # Save data
    np.savez(os.path.join(output_folder, 'inputs_all_red.npz'),
             inputs_all=np.array(tr.inputs_all))
    np.savez(os.path.join(output_folder, 'results_all_red.npz'),
             results_all_red=np.array(results_all_red))
