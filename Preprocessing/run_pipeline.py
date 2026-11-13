from Normalize import Normalization
from Validation import Valid_file
from Separate_Data import Separate_Dataset
from Export_Feature import Exported_Feature


def main():
    try:
        cry_folder = r"D:\2026-2027\CryCare\Implementation\Dataset\Cry"
        non_cry = r"D:\2026-2027\CryCare\Implementation\Dataset\Non-Cry"
        output = r"D:\2026-2027\CryCare\Implementation\output\out_test"
        Normalization(cry_folder, prefix="Cry")
        Normalization(non_cry,  prefix="Non_Cry")
        Validation = Valid_file(Normalized_input_dir=r"D:\2026-2027\CryCare\Implementation\output\out_test", windows_output_dir=r"D:\2026-2027\CryCare\Implementation\output\out_test2")
        Separated = Separate_Dataset(Validation)
        Exported_Feature(Separated)
    except Exception as e:
        print(f"error: {e}")

if __name__ == "__main__":
    main()
    