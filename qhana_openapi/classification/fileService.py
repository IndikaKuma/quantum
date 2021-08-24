"""
Author: Daniel Fink
Email: daniel-fink@outlook.com
"""

import codecs
import os
import urllib.request


class FileService:
    """
    A service class for all kind of file access like downloads,
    file deletion, folder deletion, ...
    """

    @classmethod
    def delete_if_exist(cls, *file_paths):
        for file_path in file_paths:
            if os.path.exists(file_path):
                os.remove(file_path)

    @classmethod
    def create_folder_if_not_exist(cls, folder_path):
        os.makedirs(folder_path, exist_ok=True)

    @classmethod
    def download_to_file(cls, url, file_path):

        with urllib.request.urlopen(url) as f:
            content_as_text = f.read().decode('utf-8')
            text_file = None
            if type(content_as_text) == str:
                text_file = codecs.open(file_path, 'w', 'utf-8')
            else:
                text_file = open(file_path, 'wb')
            text_file.write(content_as_text)
            text_file.close()
