from ..networks.deltav1 import unet_track
from .base_tracking import Tracking
import tensorflow as tf

class DeltaV1Tracking(Tracking):
    """
    A class for cell tracking using the U-Net Delta V2 model
    """

    def __init__(self, *args, **kwargs):
        """
        Initializes the DeltaV2Tracking using the base class init
        :param args: Arguments used for the base class init
        :param kwargs: Keyword arguments used for the basecalss init
        """

        # base class init
        super().__init__(*args, **kwargs)

    def load_model(self):
        """
        Loads model for inference/tracking.
        """

        # we get the model
        model = unet_track(self.input_size, constant_input=None)
        model.load_weights("../model_weights/model_weights_tracking/unet_moma_track_multisets.hdf5")

        # now we create a Delta2 conform model, this is similiar to what was done before DeltaV2
        inputs = tf.keras.layers.Input(shape=self.input_size, dtype='float32')
        intermediate = model(inputs)
        outputs = tf.reduce_sum(tf.where(intermediate[...,:2] > 0.8, 1.0, 0.0), keepdims=True, axis=-1)

        self.model = tf.keras.Model(inputs=inputs, outputs=outputs)
