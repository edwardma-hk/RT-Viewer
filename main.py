import glob
import os

from collections import defaultdict
from natsort import os_sorted
from os import PathLike
from pydicom import dcmread
from rt_utils import RTStructBuilder

from rt_viewer import RTViewer

DATA_DIR = 'data/patient_2'

def find_rs_structure_file(search_dir: str | PathLike[str]) -> str | None:
    """
    Find the RS Structure DICOM file in a given directory
    :param search_dir: Search directory
    :return: The path of RS Structure DICOM file or None
    """
    result = glob.glob(f'{search_dir}/rs.*.dcm', recursive=True)
    return result[0] if len(result) > 0 else None


def main():
    rt_struct_path = find_rs_structure_file(DATA_DIR)
    rt_struct = RTStructBuilder.create_from(
        dicom_series_path=DATA_DIR,
        rt_struct_path=rt_struct_path
    ) if rt_struct_path else None

    dicom_series = defaultdict(list)

    for filename in os_sorted(os.listdir(DATA_DIR)):
        filepath = os.path.join(DATA_DIR, filename)

        try:
            # Load the DICOM file
            dicom_data = dcmread(filepath)

            # Get the Series Instance UID
            series_uid = dicom_data.SeriesInstanceUID

            # Append the file path to the corresponding series
            if dicom_data.Modality == 'CT' or dicom_data.Modality == 'MR' or dicom_data.Modality == 'PET':
                dicom_series[series_uid].append(dicom_data)

        except Exception as e:
            print(f"Error reading {filename}: {e}")

    # Display the number of slices for each image set
    for series_uid, dicom_files in dicom_series.items():
        rt_viewer = RTViewer(series_uid, dicom_files, rt_struct)
        rt_viewer.show()
        continue


if __name__ == '__main__':
    main()
