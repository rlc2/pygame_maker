#!/usr/bin/python -Wall

# pygame_maker utility script

import os
import re
import sys
import stat
import shutil
import argparse
from pkg_resources import resource_stream

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

Run the $$NAME$$.py script from the $$NAME$$ directory to start the game.

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
APP_SCRIPT="""#!/usr/bin/env python

import pygame_maker.game_engine
# use the default game engine, or subclass and customize it
engine = pygame_maker.game_engine.GameEngine()
engine.run()
"""
DEMO_INSTRUCTIONS="""Demo project folder 'demo' created.

To run the demo:
$ cd demo
$ ./demo.py
"""

GAME_SETTINGS_FILE="game_settings.yaml"

GAME_NAME_RE=re.compile('\$\$NAME\$\$')
WIDTH_RE=re.compile('\$\$WIDTH\$\$')
HEIGHT_RE=re.compile('\$\$HEIGHT\$\$')

class PyGameMakerInitError(Exception):
    pass

class PyGameMakerAppError(Exception):
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
    template_resource = resource_stream('pygame_maker', 'script_data/game_settings.tmpl')
    for settings_line in template_resource:
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
    settings_path = os.path.join(base_name, GAME_SETTINGS_FILE)
    with open(settings_path, "w") as settings_f:
        settings_f.write(create_game_settings_from_template(top_dir, base_name,
            dimensions))
    app_path = os.path.join(base_name, "{}.py".format(base_name))
    with open(app_path, "w") as app_f:
        app_f.write(APP_SCRIPT)
    os.chmod(app_path, stat.S_IRWXU)
    instructions = GAME_NAME_RE.sub(base_name, INIT_INSTRUCTIONS)
    print(instructions)

def demo_project(args):
    base_name = 'demo'
    create_project_tree(base_name)
    for folder in GAME_FOLDERS:
        if folder in DEMO_FILES.keys():
            for demo_file in DEMO_FILES[folder]:
                resource_path = "script_data/{}".format(demo_file)
                demo_resource = resource_stream('pygame_maker', resource_path)
                new_path = os.path.join(base_name, folder)
                new_file = os.path.join(new_path, demo_file)
                with open(new_file, "w") as new_f:
                    new_f.write(demo_resource.read())
    settings_path = os.path.join(base_name, GAME_SETTINGS_FILE)
    with open(settings_path, "w") as settings_f:
        settings_f.write(create_game_settings_from_template(top_dir, base_name,
            "640x480"))
    demo_app_path = os.path.join(base_name, 'demo.py')
    with open(demo_app_path, "w") as demo_f:
        demo_f.write(APP_SCRIPT)
    os.chmod(demo_app_path, stat.S_IRWXU)
    print(DEMO_INSTRUCTIONS)

def run_project(args):
    import yaml
    import subprocess
    from pygame_maker import game_engine
    # find the game's project name
    game_name = ""
    if os.path.exists(GAME_SETTINGS_FILE):
        with open(GAME_SETTINGS_FILE, "r") as settings_f:
            yaml_info = yaml.load(settings_f)
            if yaml_info:
                if 'game_name' in yaml_info:
                    game_name = yaml_info['game_name']
                else:
                    print("ERROR: No game name found in {}".format(GAME_SETTINGS_FILE))
                    exit(1)
            else:
                print("ERROR: Empty or corrupted {} file found.".format(GAME_SETTINGS_FILE))
                exit(1)
    else:
        print("ERROR: '{}' not found.".format(GAME_SETTINGS_FILE))
        exit(1)
    # look for a customized game engine script named after the game itself
    game_engine_script_name = "./{}.py".format(game_name)
    if os.path.exists(game_engine_script_name):
        subprocess.call(game_engine_script_name)
    else:
        game = game_engine.GameEngine()
        game.run()

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
parser_run = subparsers.add_parser('run', help='Run the game in the current directory')
parser_run.set_defaults(func=run_project)

args = parser.parse_args()
args.func(args)

