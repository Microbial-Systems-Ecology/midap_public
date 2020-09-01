import argparse

import sys
sys.path.append('../src')

from unet_prediction import SegmentationPredictor

parser = argparse.ArgumentParser()
parser.add_argument("--path_pos")
parser.add_argument("--path_channel")
#parser.add_argument("--channel")
parser.add_argument("--postprocessing")
args = parser.parse_args()

pred = SegmentationPredictor(postprocessing=args.postprocessing)
path_cut = '/' + args.path_channel + '/xy1/phase/'
path_seg = '/' + args.path_channel + '/seg_im/'

pred.select_weights(args.path_pos, path_cut, path_seg)
pred.run_image_stack(args.path_pos, path_cut, path_seg)
