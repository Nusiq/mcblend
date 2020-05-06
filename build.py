'''
Builds project and creates the release file.
Release file name follows the naming convension pattern:
'mcblend_VERSION.zip'
'''
import zipfile
import os
import re

SRC_PATH = 'mcblend'


def main():
    '''Main function.'''
    # Get version number
    init_path = 'mcblend/__init__.py'

    version = None
    with open(init_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith('"version"'):
                version = '.'.join(
                    re.findall('\\d+', line.split(':')[-1])
                )
                break

    if version is None:
        raise Exception("Unable to read project version.")

    # Create mapping SOURCE:TARGET (in zip file)
    file_mapping = {'LICENSE': 'LICENSE'}
    for dir_name, _, files in os.walk(SRC_PATH):
        for file_name in files:
            match = False
            if re.fullmatch(r'\w+\.py', file_name):
                match = True
            if match:
                file_mapping[os.path.join(dir_name, file_name)] = (
                    os.path.join(
                        'mcblend', dir_name[len(SRC_PATH) + 1:], file_name
                    )
                )


    # Create the zip file
    output_path = f'mcblend_{version}.zip'
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for k, v in file_mapping.items():
            zipf.write(k, v)

    # This output is caputured while tesing
    print(f'Project build in {output_path}')

if __name__ == "__main__":
    main()
