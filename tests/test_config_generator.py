import os
import shutil
import subprocess
import tempfile

# pylint: disable=invalid-name

TEMP_DIR = tempfile.gettempdir()
META_TOPOLOGY_FILE_NAMES = ["meta_topology/clos_3pod_3leaf_3spine_4super.yaml",
                            "meta_topology/2c_3x2.yaml"]
GRAPHICS_FILE_NAME = TEMP_DIR + "/rift_test_graphics.html"
CONFIG_FILE_NAME = TEMP_DIR + "/rift_test_configuration.yaml"
SCRIPTS_DIR_NAME = TEMP_DIR + "/rift_test_configuration_scripts"

def cleanup():
    if os.path.exists(GRAPHICS_FILE_NAME):
        os.remove(GRAPHICS_FILE_NAME)
    if os.path.exists(CONFIG_FILE_NAME):
        os.remove(CONFIG_FILE_NAME)
    if os.path.exists(SCRIPTS_DIR_NAME):
        shutil.rmtree(SCRIPTS_DIR_NAME)

def test_config_generator():
    for meta_topology_file_name in META_TOPOLOGY_FILE_NAMES:
        cleanup()
        return_code = subprocess.call(["tools/config_generator.py",
                                       meta_topology_file_name,
                                       CONFIG_FILE_NAME])
        assert return_code == 0
        assert os.path.isfile(CONFIG_FILE_NAME)
        assert not os.path.isfile(GRAPHICS_FILE_NAME)
        assert not os.path.isdir(SCRIPTS_DIR_NAME)
        cleanup()

def test_config_generator_with_graphics():
    for meta_topology_file_name in META_TOPOLOGY_FILE_NAMES:
        cleanup()
        return_code = subprocess.call(["tools/config_generator.py",
                                       "--graphics", GRAPHICS_FILE_NAME,
                                       meta_topology_file_name,
                                       CONFIG_FILE_NAME])
        assert return_code == 0
        assert os.path.isfile(CONFIG_FILE_NAME)
        assert os.path.isfile(GRAPHICS_FILE_NAME)
        assert not os.path.isdir(SCRIPTS_DIR_NAME)
        cleanup()

def test_config_generator_netns():
    for meta_topology_file_name in META_TOPOLOGY_FILE_NAMES:
        cleanup()
        return_code = subprocess.call(["tools/config_generator.py",
                                       "--netns-per-node",
                                       meta_topology_file_name,
                                       SCRIPTS_DIR_NAME])
        assert return_code == 0
        assert not os.path.isfile(CONFIG_FILE_NAME)
        assert not os.path.isfile(GRAPHICS_FILE_NAME)
        assert os.path.isdir(SCRIPTS_DIR_NAME)
        assert os.path.isfile(SCRIPTS_DIR_NAME + "/start.sh")
        cleanup()

def test_config_generator_netns_with_graphics():
    for meta_topology_file_name in META_TOPOLOGY_FILE_NAMES:
        cleanup()
        return_code = subprocess.call(["tools/config_generator.py",
                                       "--netns-per-node",
                                       "--graphics", GRAPHICS_FILE_NAME,
                                       meta_topology_file_name,
                                       SCRIPTS_DIR_NAME])
        assert return_code == 0
        assert not os.path.isfile(CONFIG_FILE_NAME)
        assert os.path.isfile(GRAPHICS_FILE_NAME)
        assert os.path.isdir(SCRIPTS_DIR_NAME)
        assert os.path.isfile(SCRIPTS_DIR_NAME + "/start.sh")
        cleanup()
