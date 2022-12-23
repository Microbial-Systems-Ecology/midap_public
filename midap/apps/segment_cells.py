import argparse

from typing import Optional, Union
from pathlib import Path

# to get all subclasses
from midap.segmentation import *
from midap.segmentation import base_segmentator

### Functions
#############

def main(path_model_weights: Union[str,Path], path_pos: Union[str, Path], path_channel: str, segmentation_class: str,
         postprocessing: bool, network_name: Optional[str]=None, just_select=False):


    # get the right subclass
    class_instance = None
    for subclass in base_segmentator.SegmentationPredictor.__subclasses__():
        if subclass.__name__ == segmentation_class:
            class_instance = subclass

    # throw an error if we did not find anything
    if class_instance is None:
        raise ValueError(f"Chosen class does not exist: {segmentation_class}")

    # get the Predictor
    pred = class_instance(path_model_weights=path_model_weights, postprocessing=postprocessing,
                          model_weights=network_name)

    # set the paths
    path_channel = Path(path_pos).joinpath(path_channel)
    # TODO this should not be hardcoded
    path_cut = path_channel.joinpath("cut_im")

    # now we select the segmentor
    pred.set_segmentation_method(path_cut)
    # make sure that if this is a path, we have it absolute
    if pred.model_weights is not None and (weight_path := Path(pred.model_weights).absolute()).exists():
        pred.model_weights = str(weight_path)

    # if we just want to set the method we are done here
    if just_select:
        return pred.model_weights

    # run the stack if we want to
    pred.run_image_stack(path_channel)
    return pred.model_weights

# Main
######

if __name__ == "__main__":

    # arg parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("--path_model_weights", type=str, required=True, help="Path to the model weights that will be used "
                                                                              "for the segmentation.")
    parser.add_argument("--path_pos", type=str, required=True, help="Path to the current identifier folder to work on.")
    parser.add_argument("--path_channel", type=str, required=True, help="Name of the current channel to process.")
    parser.add_argument("--segmentation_class", type=str,
                        help="Name of the class used for the cell segmentation. Must be defined in a file of "
                             "midap.segmentation and a subclass of midap.segmentation.SegmentationPredictor")
    parser.add_argument("--postprocessing", action="store_true", help="Flag for postprocessing.")
    args = parser.parse_args()

    # run
    main(**vars(args))
