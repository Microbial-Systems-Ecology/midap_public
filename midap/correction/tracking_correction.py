from copy import deepcopy
from pathlib import Path

import h5py
import napari
import numpy as np
import pandas as pd
from napari.components.viewer_model import ViewerModel
from napari.layers import Image, Labels, Layer
from napari.qt import QtViewer
from napari.utils.events.event import WarningEmitter
from packaging.version import parse as parse_version
from qtpy.QtWidgets import (
    QGridLayout,
    QDoubleSpinBox,
    QPushButton,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
    QLabel,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from typing import Optional
from qtpy.QtCore import Qt
from qtpy.QtGui import QFont
import qdarkstyle
from textwrap import dedent

import markdown

NAPARI_GE_4_16 = parse_version(napari.__version__) > parse_version("0.4.16")


def copy_layer_le_4_16(layer: Layer, name: str = ""):
    res_layer = deepcopy(layer)
    # this deepcopy is not optimal for labels and images layers
    if isinstance(layer, (Image, Labels)):
        res_layer.data = layer.data

    res_layer.metadata["viewer_name"] = name

    res_layer.events.disconnect()
    res_layer.events.source = res_layer
    for emitter in res_layer.events.emitters.values():
        emitter.disconnect()
        emitter.source = res_layer
    return res_layer


def copy_layer(layer: Layer, name: str = ""):
    if NAPARI_GE_4_16:
        return copy_layer_le_4_16(layer, name)

    res_layer = Layer.create(*layer.as_layer_data_tuple())
    res_layer.metadata["viewer_name"] = name
    return res_layer


def get_property_names(layer: Layer):
    klass = layer.__class__
    res = []
    for event_name, event_emitter in layer.events.emitters.items():
        if isinstance(event_emitter, WarningEmitter):
            continue
        if event_name in ("thumbnail", "name"):
            continue
        if (
            isinstance(getattr(klass, event_name, None), property)
            and getattr(klass, event_name).fset is not None
        ):
            res.append(event_name)
    return res


class own_partial:
    """
    Workaround for deepcopy not copying partial functions
    (Qt widgets are not serializable)
    """

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        return self.func(*(self.args + args), **{**self.kwargs, **kwargs})

    def __deepcopy__(self, memodict={}):
        return own_partial(
            self.func,
            *deepcopy(self.args, memodict),
            **deepcopy(self.kwargs, memodict),
        )


class QtViewerWrap(QtViewer):
    def __init__(self, main_viewer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_viewer = main_viewer

    def _qt_open(
        self,
        filenames: list,
        stack: bool,
        plugin: str = None,
        layer_type: str = None,
        **kwargs,
    ):
        """for drag and drop open files"""
        self.main_viewer.window._qt_viewer._qt_open(
            filenames, stack, plugin, layer_type, **kwargs
        )


class GenericBox(QWidget):
    """
    A Generic box with the right background color etx
    """
    def __init__(self):
        """
        Inits the widget
        """
        # proper init
        super().__init__()

        # style sheet
        self.setStyleSheet("QWidget { "
                           "background-color : #414851; "
                           "border-radius: 3%; }")


class SelectionBox(GenericBox):
    """
    A box displaying the selection box
    """

    def __init__(self, labels: np.ndarray, track_df: pd.DataFrame):
        """
        Inits the widget
        :param labels: An array of labels corresponding to the images
        :param track_df: The tracking data frame indicating track IDs, cell divisions etc.
        """
        # proper init
        super().__init__()

        # set attributes
        self.labels = labels
        self.track_df = track_df

        # add the subsections
        layout = QVBoxLayout()
        self.label = QLabel()
        self.label.setTextFormat(Qt.RichText)
        self.label.setText(self.get_selection_label())
        layout.addWidget(self.label)

        # apply layout
        self.setLayout(layout)

    def get_selection_label(self):

        label = """
        <h2><u> Selection </u></h2>
        <style type="text/css">
        .tg  {border-collapse:collapse;border-spacing:0;}
        .tg td{border-color:black;border-style:solid;border-width:1px;font-family:Arial, sans-serif;font-size:14px;
          overflow:hidden;padding:2px 2px;word-break:normal;}
        .tg .tg-syad{background-color:#414851;border-color:inherit;color:#ffffff;text-align:left;vertical-align:top;width:100px;}
        .tg .tg-tibk{background-color:#414851;border-color:inherit;color:#ffffff;text-align:right;vertical-align:top;width:35px;}
        </style>
        <table class="tg">
        <tbody>
          <tr>
            <td class="tg-syad">Current Selection:</td>
            <td class="tg-tibk">0</td>
          </tr>
        </tbody>
        </table>
        """

        return label


class FrameInfo(GenericBox):
    """
    A class to display the Frame info
    """

    def __init__(self, labels: np.ndarray, track_df: pd.DataFrame):
        """
        Inits the widget
        :param labels: An array of labels corresponding to the images
        :param track_df: The tracking data frame indicating track IDs, cell divisions etc.
        """
        # proper init
        super().__init__()

        # set attributes
        self.labels = labels
        self.track_df = track_df

        # set necessary attributes
        layout = QVBoxLayout()
        self.label = QLabel()
        self.label.setTextFormat(Qt.RichText)
        layout.addWidget(self.label)

        # finalize
        self.setLayout(layout)
        self.setFixedHeight(170)

    def update_info(self, current_frame: int):
        """
        Updates the info box for a new frame and selection
        :param current_frame: The index of the current frame (left viewer)
        """

        # get infos
        left_frame = current_frame
        right_frame = current_frame + 1
        left_n_cells = np.sum(self.track_df["frame"] == left_frame)
        right_n_cells = np.sum(self.track_df["frame"] == right_frame)
        if left_frame == 0:
            left_orphans = "N/A"
        else:
            left_orphans = sum(self.track_df["first_frame"] == left_frame)
        right_orphans = sum(self.track_df["first_frame"] == right_frame)
        left_dying = sum(self.track_df["last_frame"] == left_frame)
        if right_frame == len(self.labels) - 1:
            right_dying = "N/A"
        else:
            right_dying = sum(self.track_df["last_frame"] == right_frame)

        # to table
        frame_info = f"""
        <h2><u> Frames </u></h2>
        <style type="text/css">
        .tg  {{border-collapse:collapse;border-spacing:0;}}
        .tg td{{border-color:black;border-style:solid;border-width:1px;font-family:Arial, sans-serif;font-size:14px;
          overflow:hidden;padding:2px 2px;word-break:normal;}}
        .tg th{{border-color:black;border-style:solid;border-width:1px;font-family:Arial, sans-serif;font-size:14px;
          font-weight:normal;overflow:hidden;padding:2px 2px;word-break:normal;}}
        .tg .tg-syad{{background-color:#414851;border-color:inherit;color:#ffffff;text-align:left;vertical-align:top;width:80px;}}
        .tg .tg-tibk{{background-color:#414851;border-color:inherit;color:#ffffff;text-align:right;vertical-align:top;
        width:35px;}}
        </style>
        <table class="tg">
        <thead>
          <tr>
            <th class="tg-syad"></th>
            <th class="tg-tibk"><b>Left</b></th>
            <th class="tg-tibk"><b>Right</b></th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td class="tg-syad"># Frame:</td>
            <td class="tg-tibk">{left_frame}</td>
            <td class="tg-tibk">{right_frame}</td>
          </tr>
          <tr>
            <td class="tg-syad"># Cells:</td>
            <td class="tg-tibk">{left_n_cells}</td>
            <td class="tg-tibk">{right_n_cells}</td>
          </tr>
          <tr>
            <td class="tg-syad"># Orphans:</td>
            <td class="tg-tibk">{left_orphans}</td>
            <td class="tg-tibk">{right_orphans}</td>
          </tr>
          <tr>
            <td class="tg-syad"># Dying:</td>
            <td class="tg-tibk">{left_dying}</td>
            <td class="tg-tibk">{right_dying}</td>
          </tr>
        </tbody>
        </table>
        """

        # update label text
        self.label.setText(frame_info)


class InfoBox(QWidget):
    """
    Infobox with all the frames etc.
    """
    def __init__(self, labels: np.ndarray, track_df: pd.DataFrame):
        """
        Inits the widget
        :param labels: An array of labels corresponding to the images
        :param track_df: The tracking data frame indicating track IDs, cell divisions etc.
        """
        # proper init
        super().__init__()

        # set attributes
        self.labels = labels
        self.track_df = track_df

        # add the subsections
        layout = QVBoxLayout()

        # define some constants
        width = 250

        # frame stuff
        self.frame_info = FrameInfo(labels=labels, track_df=track_df)
        self.frame_info.setFixedWidth(width)
        layout.addWidget(self.frame_info)

        # Selection stuff
        self.selection_box = SelectionBox()
        self.selection_box.setFixedWidth(width)
        layout.addWidget(self.selection_box)


        # General Stuff

        # finalize
        self.setLayout(layout)
        self.setFixedWidth(200)

    def update_info(self, current_frame: int, selection: Optional[int]):
        """
        Updates the info box for a new frame and selection
        :param current_frame: The index of the current frame (left viewer)
        :param selection: The label (track ID) of the current selection, can be None
        """

        # update frame
        self.frame_info.update_info(current_frame)


class MultipleViewerWidget(QWidget):
    """The main widget of the example."""

    def __init__(self, viewer: napari.Viewer, images: np.ndarray, labels: np.ndarray, track_df: pd.DataFrame):
        """
        Inits the widget
        :param viewer: The napari viewer to use
        :param images: An array of images
        :param labels: An array of labels corresponding to the images
        :param track_df: The tracking data frame indicating track IDs, cell divisions etc.
        """
        super().__init__()

        # check if we have at least to images
        if len(images) < 2:
            raise ValueError("The viewer needs at least the track of 2 images!")
        # we need at least 1 tracked cell
        if len(track_df) == 0:
            raise ValueError("No cell tracks in the track data frame!")

        # the main viewer
        self.main_viewer = viewer

        # The secondary viewer (do not change the title)
        self.side_viewer = ViewerModel(title="model1")
        self._block = False
        self.qt_viewer1 = QtViewerWrap(viewer, self.side_viewer)

        # The info box with al
        self.info_box = InfoBox(labels=labels, track_df=track_df)

        # The napari qt viewer is already in a layout (box)
        # we add the parent to a temp layout to remove it from the window
        tmp_layout = QGridLayout()
        tmp_layout.addWidget(self.main_viewer.window._qt_viewer.parent())
        tmp_widget = QWidget()
        tmp_widget.setLayout(tmp_layout)
        # now we add just the viewer to the grid layout
        # this way the two viewers will alway be the same size
        layout = QGridLayout()
        # add stretch factor to ensure even resize
        layout.setRowStretch(0, 1)
        layout.setColumnStretch(0, 1)
        layout.addWidget(self.main_viewer.window._qt_viewer, 0, 0)
        layout.setColumnStretch(1, 1)
        layout.addWidget(self.qt_viewer1, 0, 1)
        # no stretch factor for the status widget
        layout.setColumnStretch(2, 0)
        layout.addWidget(self.info_box, 0, 2)
        self.setLayout(layout)

        # create the image layers
        self.current_frame = 0
        self.n_frames = len(images)
        self.images = images
        self.labels = labels

        # the special names are layer that are differently named in both viewer, other layers are the same and copied
        self.special_names = ["Image", "Labels", "Selection"]

        # the image layers
        self.main_img_layer = self.main_viewer.add_image(data=self.images[self.current_frame],
                                                         name="Image",
                                                         rgb=False,
                                                         contrast_limits=[0,1],
                                                         scale=(1,1))
        self.side_img_layer = self.side_viewer.add_image(self.images[self.current_frame + 1],
                                                         name="SideImage",
                                                         rgb=False,
                                                         contrast_limits=[0, 1],
                                                         scale=(1, 1))

        # add the label images
        self.main_label_layer = self.main_viewer.add_labels(self.labels[self.current_frame],
                                                            name="Labels",
                                                            num_colors=50)
        self.side_label_layer = self.side_viewer.add_labels(self.labels[self.current_frame+1],
                                                            name="SideLabels",
                                                            num_colors=50)

        # the selection
        self.selection = None
        test_select = np.zeros_like(self.labels[self.current_frame])
        self.main_select_layer = self.main_viewer.add_labels(test_select,
                                                             name="Selection",
                                                             color={1: "yellow"},
                                                             opacity=1.0)
        self.side_select_layer = self.side_viewer.add_labels(test_select,
                                                             name="SideSelection",
                                                             color={1: "yellow",
                                                                    2: "orange"},
                                                             opacity=1.0)

        # info box update
        self.info_box.update_info(current_frame=self.current_frame, selection=self.selection)

        # connect the special layers
        self.main_img_layer.events.visible.connect(self._visibility_chane)
        self.main_label_layer.events.visible.connect(self._visibility_chane)
        self.main_select_layer.events.visible.connect(self._visibility_chane)

        # sync layers (one directional because the tools are only for the main viewer)
        self.main_viewer.layers.events.inserted.connect(self._layer_added)
        self.main_viewer.layers.events.removed.connect(self._layer_removed)
        self.main_viewer.layers.events.moved.connect(self._layer_moved)
        self.main_viewer.layers.selection.events.active.connect(self._layer_selection_changed)

        # sync status and resets (one directional)
        self.main_viewer.events.reset_view.connect(self._reset_view)
        self.side_viewer.events.status.connect(self._status_update)

        # sync dims (just for completion, should not be relevant)
        self.main_viewer.dims.events.current_step.connect(self._point_update)
        self.side_viewer.dims.events.current_step.connect(self._point_update)
        self.main_viewer.dims.events.order.connect(self._order_update)

        # sync camera
        self.main_viewer.camera.events.zoom.connect(self._viewer_zoom)
        self.side_viewer.camera.events.zoom.connect(self._viewer_zoom)
        self.main_viewer.camera.events.center.connect(self._viewer_center)
        self.side_viewer.camera.events.center.connect(self._viewer_center)
        self.main_viewer.camera.events.angles.connect(self._viewer_angles)
        self.side_viewer.camera.events.angles.connect(self._viewer_angles)

        # key binds
        self.main_viewer.bind_key('Left', self.left_arrow_key_bind)
        self.main_viewer.bind_key('Right', self.right_arrow_key_bind)

        # mouse clicks
        self.main_select_layer.mouse_drag_callbacks.append(self.track_clicked)
        self.side_select_layer.mouse_drag_callbacks.append(self.track_clicked)

    def _status_update(self, event):
        """
        Updates the status of the viewer (message displayer in the lower left corner) only needs to sync in 1 direction
        :param event: The event that triggered the status change
        """
        self.main_viewer.status = event.value

    def _reset_view(self):
        """
        Syncs the reset of the view one-directional
        """
        self.side_viewer.reset_view()

    def _layer_selection_changed(self, event):
        """
        Syncs the reset of the view one-directional
        """
        if self._block:
            return

        if event.value is None:
            self.side_viewer.layers.selection.active = None
            return

        # catch special names
        if (name := event.value.name) in self.special_names:
            name = f"Side{name}"

        self.side_viewer.layers.selection.active = self.side_viewer.layers[name]

    def _point_update(self, event):
        """
        Syncs the point updates of the view one-directional
        :param event: The trigger event
        """
        for model in [self.main_viewer, self.side_viewer]:
            if model.dims is event.source:
                continue
            model.dims.current_step = event.value

    def _order_update(self):
        """
        Order sync for the dims (one-directional)
        """
        order = list(self.main_viewer.dims.order)
        if len(order) <= 2:
            self.side_viewer.dims.order = order
            return

        order[-3:] = order[-2], order[-3], order[-1]
        self.side_viewer.dims.order = order

    def _layer_added(self, event):
        """
        Add layer to additional viewers and connect all required events
        :param event: The event that trigger the layer addition
        """
        self.side_viewer.layers.insert(event.index, copy_layer(event.value, "model1"))

        for name in get_property_names(event.value):
            getattr(event.value.events, name).connect(own_partial(self._property_sync, name))

        if isinstance(event.value, Labels):
            event.value.events.set_data.connect(self._set_data_refresh)
            self.side_viewer.layers[event.value.name].events.set_data.connect(self._set_data_refresh)

        self.side_viewer.layers[event.value.name].events.data.connect(self._sync_data)

        event.value.events.name.connect(self._sync_name)

        self._order_update()

    def _sync_name(self, event):
        """
        Sync the name of layers (if not special)
        :param event: The event that triggered the rename
        """

        if (name := event.source.name) not in self.special_names:
            index = self.main_viewer.layers.index(event.source)
            self.side_viewer.layers[index].name = name

    def _sync_data(self, event):
        """
        Sync data modification from additional viewers  (not special layers)
        :param event: The event that changed the data
        """
        if self._block or (name := event.source.name) in self.special_names:
            return
        for model in [self.main_viewer, self.side_viewer]:
            layer = model.layers[name]
            if layer is event.source:
                continue
            try:
                self._block = True
                layer.data = event.source.data
            finally:
                self._block = False

    def _set_data_refresh(self, event):
        """
        Synchronize data refresh between layers (not special layers)
        :param event: Event that triggered the refresh
        """
        if self._block or (name := event.source.name) in self.special_names:
            return
        for model in [self.main_viewer, self.side_viewer]:
            layer = model.layers[name]
            if layer is event.source:
                continue
            try:
                self._block = True
                layer.refresh()
            finally:
                self._block = False

    def _layer_removed(self, event):
        """
        Remove layer in all viewers
        :param event: Event that triggered the removeal
        """
        self.side_viewer.layers.pop(event.index)

    def _layer_moved(self, event):
        """
        Update order of layers
        :param event: Event that triggered the move
        """
        dest_index = (
            event.new_index
            if event.new_index < event.index
            else event.new_index + 1
        )
        self.side_viewer.layers.move(event.index, dest_index)

    def _property_sync(self, name, event):
        """
        Sync layers properties (except the name)
        :param name: Name of the property
        :param event: event that triggered sync
        """
        if event.source not in self.main_viewer.layers:
            return
        try:
            # catch special names
            if (layer_name := event.source.name) in self.special_names:
                layer_name = f"Side{name}"
            self._block = True
            setattr(
                self.side_viewer.layers[layer_name],
                name,
                getattr(event.source, name),
            )
        finally:
            self._block = False

    def _visibility_chane(self, event):
        """
        Syncs the change of visibility from the main to the side special layers
        :param event: The event for the change
        """
        # catch special names
        if (name := event.source.name) in self.special_names:
            name = f"Side{name}"
        self.side_viewer.layers[name].visible = event.source.visible

    def _viewer_zoom(self, event):
        """
        Syncs the zoom between all the viewers
        :param event: The camera event
        """
        self.main_viewer.camera.zoom = event.source.zoom
        self.side_viewer.camera.zoom = event.source.zoom

    def _viewer_center(self, event):
        """
        Syncs the center between all the viewers
        :param event: The camera event
        """
        self.main_viewer.camera.center = event.source.center
        self.side_viewer.camera.center = event.source.center

    def _viewer_angles(self, event):
        """
        Syncs the angles between all the viewers
        :param event: The camera event
        """
        self.main_viewer.camera.angles = event.source.angles
        self.side_viewer.camera.angles = event.source.angles

    def change_frame(self, frame: int):
        """
        Changes the current frame to frame
        :param frame: The int of the new frame of the main viewer
        """

        # catch our of bounds
        if frame == self.n_frames:
            frame -= 1

        # update
        self.main_img_layer.data = self.images[frame]
        self.main_label_layer.data = self.labels[frame]

        self.side_img_layer.data = self.images[frame + 1]
        self.side_label_layer.data = self.labels[frame + 1]

        self.current_frame = frame

        # selection
        self.update_selection(selection=self.selection)

        # info
        self.info_box.update_info(current_frame=self.current_frame, selection=self.selection)

    def left_arrow_key_bind(self, *args):

        """
        Key bind for the left arrow key (decrease frame number)
        """
        if self.current_frame == 0:
            self.main_viewer.status = "Already at first image"
            return
        self.change_frame(self.current_frame - 1)

    def right_arrow_key_bind(self, *args):
        """
        Key bind for the right arrow key (increase frame number)
        """

        if self.current_frame + 2 == self.n_frames:
            self.main_viewer.status = "Already at last image"
            return
        self.change_frame(self.current_frame + 1)

    def track_clicked(self, layer, event):
        """
        Handle for the mouse clicks on the tracks
        :param event: The event of the mouse click
        """
        # Mouse down
        yield
        # Mouse up
        data_coordinates = layer.world_to_data(event.position)
        x, y = np.round(data_coordinates).astype(int)
        # a click into nothing-ness
        if x < 0 or x >= self.labels.shape[1]:
            return
        if y < 0 or y >= self.labels.shape[2]:
            return
        # get the val if
        if "Side" in layer.name:
            val = self.labels[self.current_frame + 1][x, y]
        else:
            val = self.labels[self.current_frame][x, y]
        # click on the same selection (unselect)
        if val == self.selection:
            self.update_selection(None)
        # normal update
        else:
            self.update_selection(val)

    def update_selection(self, selection=None):
        """
        Updates the selection to the new value
        :param selection: The new selection value
        """

        if selection is None or selection == 0:
            # Nothin is selected
            self.selection = None
            self.main_select_layer.data = np.zeros_like(self.main_select_layer.data)
            self.side_select_layer.data = np.zeros_like(self.side_select_layer.data)
        else:
            # there might be something
            self.selection = selection

            # we update main
            main_label = self.labels[self.current_frame]
            new_data = np.where(main_label == selection, 1, 0)
            self.main_select_layer.data = new_data

            # update side
            side_data = self.labels[self.current_frame + 1]
            new_data = np.where(side_data == selection, 1, 0)
            self.side_select_layer.data = new_data

            # TODO: add kids


def main():
    # read in the data
    path = Path("../../../Tests/tracking_tool/test_data/PH")
    with h5py.File(path.joinpath("label_stack_delta.h5")) as f:
        labels = f["label_stack"][:].astype(int)
    with h5py.File(path.joinpath("raw_inputs_delta.h5")) as f:
        imgs = f["raw_inputs"][:]
    table = pd.read_csv(path.joinpath("track_output_delta.csv"))

    view = napari.Viewer()
    # create the multi view and make it central
    multi_view = MultipleViewerWidget(view, images=imgs, labels=labels, track_df=table)
    view.window._qt_window.setCentralWidget(multi_view)
    napari.run()

if __name__ == "__main__":
    main()

