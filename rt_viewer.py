import matplotlib.pyplot as plt
import numpy as np

from matplotlib.widgets import Slider
from pydicom import FileDataset
from rt_utils import RTStruct
from skimage.measure import find_contours
from skimage.morphology import remove_small_holes, remove_small_objects


class RTViewer:
    current_slice = 0
    fig = None
    axes = None
    image_display = None
    slice_slider = None
    rt_struct = None
    roi_mask = None
    ROI_NAME = 'Liver'

    def __init__(self, series_uid: str, dicom_files: list[FileDataset], rt_struct: RTStruct = None):
        self.dicom_files = dicom_files
        self.number_of_slice = len(dicom_files)

        if rt_struct.series_data[0].SeriesInstanceUID == series_uid:
            self.rt_struct = rt_struct

        if self.number_of_slice == 0:
            print('Number of slice is zero')
            return

        if rt_struct is not None:
            # Loading the 3D Mask from within the RT Struct
            self.roi_mask = rt_struct.get_roi_mask_by_name("Liver")

        self.fig, self.axes = plt.subplots()
        plt.subplots_adjust(bottom=0.2)

        self.current_slice = 0
        self.image_display = self.axes.imshow(self.dicom_files[self.current_slice].pixel_array, cmap="gray")
        self.axes.set_title(f"Slice {self.current_slice + 1}/{self.number_of_slice}")
        self.axes.axis("off")

        # Add slider
        ax_slider = plt.axes((0.2, 0.05, 0.6, 0.03))
        self.slice_slider = Slider(ax_slider, "Slice", 0, self.number_of_slice - 1, valinit=0, valstep=1)

        self.slice_slider.on_changed(self.update)
        self.fig.canvas.mpl_connect("key_press_event", self.update_slice)

    def update(self, val: float) -> None:
        """
        Update function for slider
        :param val: default argument
        :return: None
        """
        self.current_slice = int(self.slice_slider.val)
        self.image_display.set_data(self.dicom_files[self.current_slice].pixel_array)
        self.axes.set_title(f"Slice {self.current_slice + 1}/{self.number_of_slice}")
        self.overlay_roi_contour(self.current_slice)
        self.fig.canvas.draw()

    def update_slice(self, event) -> None:
        """
        Keyboard navigation (Up/Down arrows)
        :param event: Event
        :return: None
        """
        if event.key == "down" or event.key == 'right':
            self.current_slice = min(self.current_slice + 1, self.number_of_slice - 1)
        elif event.key == "up" or event.key == 'left':
            self.current_slice = max(self.current_slice - 1, 0)
        self.slice_slider.set_val(self.current_slice)  # Sync slider position
        self.image_display.set_data(self.dicom_files[self.current_slice].pixel_array)
        self.axes.set_title(f"Slice {self.current_slice + 1}/{self.number_of_slice}")
        self.overlay_roi_contour(self.current_slice)
        self.fig.canvas.draw()

    def overlay_roi_contour(self, min_size=32):
        """Overlay contours extracted from the ROI mask for the given slice."""
        # Remove previously drawn contour lines.
        # Note: We avoid removing the primary image artist.
        if self.roi_mask is None:
            return

        for line in self.axes.lines[:]:
            line.remove()

        # Get the 2D mask for the current slice and convert to uint8.
        mask_slice = self.roi_mask[:, :, -self.current_slice - 1].astype(np.uint8) > 0
        mask_clean = remove_small_objects(remove_small_holes(mask_slice, area_threshold=min_size), min_size=min_size)

        # Use skimage's find_contours to extract contour lines at a value of 0.5.
        contours = find_contours(mask_clean, level=0.5)
        for contour in contours:
            # find_contours returns (row, col) coordinates. We swap them to (x, y) for plotting.
            self.axes.plot(contour[:, 1], contour[:, 0], color="red", linewidth=2)

    def show(self):
        print(f"Series UID: {self.dicom_files[0].SeriesInstanceUID}")
        print(f"Number of slices: {self.number_of_slice}")

        if self.rt_struct is not None:
            # View all the ROI names from within the image
            print(f'RT Structure UID: {self.rt_struct.series_data[0].SeriesInstanceUID}')
            print(f'ROI name: {self.rt_struct.get_roi_names()}')

        print("-" * 40)

        plt.show()
