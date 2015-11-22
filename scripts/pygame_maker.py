#!/usr/bin/python -Wall

# pygame_maker utility script

import os
import re
import sys
import shutil
import argparse

YAML_STUB_TEMPLATE="""# Create a list of the $$ITEM$$ used in the game
# This file will be interpreted as YAML (http://yaml.org)
# TODO: Link to documentation for $$ITEM$$ fields
"""

GAME_FOLDERS=[
    'backgrounds',
    'sprites',
    'sounds',
    'objects',
    'rooms',
]

INIT_INSTRUCTIONS="""New project folder '$$NAME$$' created.

Edit the .yaml files in the subdirectories inside the new project folder to
create the game.

TO-DO:
 * Make the new game init command produce something playable (if you try to
   play the game now it will fail, because no room was defined)
 * Create documentation
 * Add pointers to documentation
 * Create a GUI game editor that reads and writes the .yaml files
"""

DEMO_FILES = {
    "sprites": ["demo_sprites.yaml", "ball2.png", "pokey.png"],
    "sounds": ["demo_sounds.yaml", "explosion.wav", "Pop.wav"],
    "objects": ["demo_objects.yaml"],
    "rooms": ["demo_rooms.yaml"]
}
DEMO_INSTRUCTIONS="""Demo project folder 'demo' created.

To run the demo:
$ cd demo
$ game_engine.py
"""

GAME_SETTINGS_TEMPLATE="script_data/game_settings.tmpl"
GAME_NAME_RE=re.compile('\$\$NAME\$\$')
WIDTH_RE=re.compile('\$\$WIDTH\$\$')
HEIGHT_RE=re.compile('\$\$HEIGHT\$\$')

class PyGameMakerInitError(Exception):
    pass

def create_help_text_from_template(item_name):
    help_text = re.sub('\$\$ITEM\$\$', item_name, YAML_STUB_TEMPLATE)
    return(help_text)

def create_game_settings_from_template(top_dir, game_name, dimension_string):
    minfo = re.search("(\d+)x(\d+)", dimension_string)
    if not minfo:
        raise(PyGameMakerInitError("Invalid dimensions '{}' (expected <width>x<height>)"))
    width = minfo.group(1)
    height = minfo.group(2)
    output_data = ""
    with open(os.path.join(top_dir, GAME_SETTINGS_TEMPLATE), "r") as gstemplate_f:
        for settings_line in gstemplate_f:
            output_line = str(settings_line)
            gninfo = GAME_NAME_RE.search(settings_line)
            if gninfo:
                output_line = GAME_NAME_RE.sub(game_name, settings_line)
            winfo = WIDTH_RE.search(output_line)
            if winfo:
                output_line = WIDTH_RE.sub(width, output_line)
            hinfo = HEIGHT_RE.search(output_line)
            if hinfo:
                output_line = HEIGHT_RE.sub(height, output_line)
            output_data += output_line
    return(output_data)

def create_project_tree(base_name):
    os.mkdir(base_name)
    for folder in GAME_FOLDERS:
        new_subfolder = os.path.join(base_name, folder)
        os.mkdir(new_subfolder)

def init_project(args):
    base_name = args.project_name
    dimensions = args.dimensions
    create_project_tree(base_name)
    for folder in GAME_FOLDERS:
        new_subfolder = os.path.join(base_name, folder)
        yaml_stub_name = os.path.join(new_subfolder, "{}.yaml".format(folder))
        with open(yaml_stub_name, "w") as yaml_f:
            yaml_f.write(create_help_text_from_template(folder))
    settings_path = os.path.join(base_name, 'game_settings.yaml')
    with open(settings_path, "w") as settings_f:
        settings_f.write(create_game_settings_from_template(top_dir, base_name,
            dimensions))
    instructions = GAME_NAME_RE.sub(base_name, INIT_INSTRUCTIONS)
    print(instructions)

def demo_project(args):
    base_name = 'demo'
    create_project_tree(base_name)
    script_data_path = os.path.join(top_dir, 'script_data')
    for folder in GAME_FOLDERS:
        if folder in DEMO_FILES.keys():
            for demo_file in DEMO_FILES[folder]:
                src_path = os.path.join(script_data_path, demo_file)
                new_path = os.path.join(base_name, folder)
                if os.path.exists(src_path):
                    shutil.copy(src_path, new_path)
    settings_path = os.path.join(base_name, 'game_settings.yaml')
    with open(settings_path, "w") as settings_f:
        settings_f.write(create_game_settings_from_template(top_dir, base_name,
            "640x480"))
    print(DEMO_INSTRUCTIONS)

script_full_path = os.path.abspath(sys.argv[0])
script_path = os.path.dirname(script_full_path)
top_dir = os.path.dirname(script_path)

parser = argparse.ArgumentParser(description='PyGame Maker utility script')
parser.add_argument('--verbose', action='count', help='Increase verbosity')
subparsers = parser.add_subparsers(help='Command name')
parser_init = subparsers.add_parser('init', help='Make a new game folder in the current directory')
parser_init.add_argument('project_name', help='Supply the name of the new game')
parser_init.add_argument('dimensions', help='Supply the screen dimensions as <width>x<height>, e.g. 640x480')
parser_init.set_defaults(func=init_project)
parser_demo = subparsers.add_parser('demo', help='Create the demo game folder in the current directory')
parser_demo.set_defaults(func=demo_project)

args = parser.parse_args()
args.func(args)

