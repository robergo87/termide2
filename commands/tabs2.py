# pylint: disable=C0116,C0115,C0114

from os import listdir, getcwd
from os.path import basename
import subprocess
import json
import curses

from argparse import ArgumentParser
from shared.curses import Listing

# ######################################
# argparse setup
# ######################################

parser = ArgumentParser()
parser.add_argument("sid", type=str)

# ######################################
# callbacks setup
# ######################################


class Tabs(Listing):
    def __init__(self, sid):
        super().__init__()
        self.sid = sid
        self.tid = None

    def call_space(self, *params):
        return subprocess.check_output(
            ["termide", "space", "--sid", self.sid] 
            + 
            list(params)
        )

    def generate(self):
        raw_data = self.call_space("terminals")
        data = json.loads(raw_data)
        current_tid = data.get("current")
        if current_tid != self.tid:
            self.tid = current_tid
            self.selected = current_tid
        return [
            {"path": tabuid, "label": basename(tabuid)}
            for tabuid in data.get("list", [])
        ]

    def default_action(self):
        return self.call_space("terminal-set", "--tid", self.selected, "--focus", "1")

    def draw_single_row(self, row, is_selected, printfunc):
        color = (
            curses.color_pair(1)
            if row["path"] ==  self.tid else
            curses.color_pair(2)
        )
        printfunc(row["label"], color)      

    def row_key(self, row):
        return row["path"]


def execute_cmd(params):
    tabs = Tabs(params.get("sid"))
    tabs.run()
