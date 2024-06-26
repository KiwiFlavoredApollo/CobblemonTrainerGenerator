import logging

import inquirer

from commands.misc import PrintTrainerCommand, CloseCommandPromptCommand, ExportTrainerCommand, ImportTrainerCommand
from commands.pokemon import EditTeamCommand
from commands.trainer import EditTrainerCommand
from exceptions import CommandPromptCloseException
from trainer import Trainer


class TrainerGenerator:
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._trainer = Trainer("trainer")

    def run(self):
        while True:
            try:
                COMMANDS = [
                    ("Print", PrintTrainerCommand()),
                    ("Trainer", EditTrainerCommand()),
                    ("Pokemon", EditTeamCommand()),
                    ("Export", ExportTrainerCommand()),
                    ("Import", ImportTrainerCommand()),
                    ("Close", CloseCommandPromptCommand())
                ]
                answer = inquirer.prompt([inquirer.List("command", "Select command", COMMANDS)])
                answer["command"].execute(self._trainer)
            except CommandPromptCloseException:
                return
