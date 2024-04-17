import json
import logging

import inquirer

from commands.interface import Command
from exceptions import PokemonCreationFailedException, EditTeamCommandCloseException, \
    EditSlotCommandCloseException, PokemonLevelInvalidException, PokemonNotExistSlotException
from pokemonfactory import RandomizedPokemonFactory, assert_valid_pokemon_level, \
    get_pokemon_name, select_random_nature, select_random_moveset
from pokemonwikiapi import PokeApi as PokemonWikiApi


class EditTeamCommand(Command):
    def execute(self, trainer):
        try:
            self._edit_team(trainer)
        except EditTeamCommandCloseException:
            pass

    def _edit_team(self, trainer):
        while True:
            team = trainer.properties["team"]
            buttons = [
                ("Return", CloseEditTeamCommand()),
                (self._get_button_name(team, 0), self._get_button_command(team, 0)),
                (self._get_button_name(team, 1), self._get_button_command(team, 1)),
                (self._get_button_name(team, 2), self._get_button_command(team, 2)),
                (self._get_button_name(team, 3), self._get_button_command(team, 3)),
                (self._get_button_name(team, 4), self._get_button_command(team, 4)),
                (self._get_button_name(team, 5), self._get_button_command(team, 5)),
                ("Team Level", EditTeamLevelCommand()),
            ]
            answer = inquirer.prompt([inquirer.List("button", "Select Pokemon", buttons)])
            answer["button"].execute(trainer)

    def _get_button_name(self, team, slot):
        try:
            self._assert_exist_pokemon(team, slot)
            cap_name = self._get_capitalized_pokemon_name(team, slot)
            return self._prepend_slot_number(cap_name, slot)
        except PokemonNotExistSlotException:
            return self._prepend_slot_number("Empty", slot)

    def _assert_exist_pokemon(self, team, slot):
        try:
            team[slot]
        except IndexError:
            raise PokemonNotExistSlotException

    def _prepend_slot_number(self, string, slot):
        delimiter = " "
        return delimiter.join(["[{}]".format(slot + 1), string])

    def _get_capitalized_pokemon_name(self, team, slot):
        name = get_pokemon_name(team[slot])
        return name.capitalize()

    def _get_button_command(self, team, slot):
        try:
            self._assert_exist_pokemon(team, slot)
            return EditSlotCommand(slot)
        except PokemonNotExistSlotException:
            return AddPokemonCommand()


class ConfirmAddPokemonCommand(Command):
    def execute(self, trainer):
        answer = inquirer.prompt([inquirer.Confirm("add", message="Add Pokemon?", default=False)])
        if answer["add"]:
            AddPokemonCommand().execute(trainer)


class AddPokemonCommand(Command):
    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def execute(self, trainer):
        try:
            name = self._get_pokemon_name()
            self._assert_not_empty_string(name)
            pokemon = RandomizedPokemonFactory(PokemonWikiApi()).create(name)
            trainer.properties["team"].append(pokemon)
        except PokemonCreationFailedException as e:
            self._logger.debug(e.message)

    def _get_pokemon_name(self):
        answer = inquirer.prompt([inquirer.Text("name", "Pokemon Name")])
        return answer["name"].lower()

    def _assert_not_empty_string(self, string):
        if string == "":
            raise PokemonCreationFailedException("Empty string is given for Pokemon name")


class EditSlotCommand(Command):
    def __init__(self, slot):
        self._slot = slot

    def execute(self, trainer):
        try:
            self._edit_slot(trainer)
        except EditSlotCommandCloseException:
            pass

    def _edit_slot(self, trainer):
        while True:
            COMMANDS = [
                ("Return", CloseEditSlotCommand()),
                ("Print", PrintPokemonCommand(self._slot)),
                ("Level", EditPokemonLevelCommand(self._slot)),
                ("Ability", EditPokemonAbilityCommand(self._slot)),
                ("Nature", EditPokemonNatureCommand(self._slot)),
                ("Moveset", EditPokemonMovesetCommand(self._slot)),
                ("Remove", RemovePokemonCommand(self._slot))
            ]
            answer = inquirer.prompt([inquirer.List("command", "Select action", COMMANDS)])
            answer["command"].execute(trainer)


class CloseEditSlotCommand(Command):
    def execute(self, trainer):
        raise EditSlotCommandCloseException


class RemovePokemonCommand(Command):
    def __init__(self, slot):
        self._slot = slot

    def execute(self, trainer):
        answer = inquirer.prompt([inquirer.Confirm("remove", message="Remove this pokemon?", default=False)])
        if answer["remove"]:
            team = trainer.properties["team"]
            team.pop(self._slot)

        CloseEditSlotCommand().execute(trainer)


class CloseEditTeamCommand(Command):
    def execute(self, trainer):
        raise EditTeamCommandCloseException


class EditPokemonLevelCommand(Command):
    def __init__(self, slot):
        self._slot = slot

    def execute(self, trainer):
        try:
            team = trainer.properties["team"]
            pokemon = team[self._slot]
            level = self._ask_pokemon_level(pokemon)
            assert_valid_pokemon_level(level)
            pokemon["level"] = level
        except PokemonLevelInvalidException:
            pass

    def _ask_pokemon_level(self, pokemon):
        answer = inquirer.prompt([inquirer.Text("level", "Pokemon Level", default=pokemon["level"])])
        return int(answer["level"])


class EditPokemonAbilityCommand(Command):
    def __init__(self, slot):
        self._slot = slot

    def execute(self, trainer):
        team = trainer.properties["team"]
        pokemon = team[self._slot]
        name = get_pokemon_name(pokemon)
        ability = self._ask_pokemon_ability(name)
        pokemon["ability"] = ability

    def _ask_pokemon_ability(self, name):
        abilities = PokemonWikiApi().get_pokemon_abilities(name)
        answer = inquirer.prompt([inquirer.List("ability", "Pokemon Ability", abilities)])
        return answer["ability"]


class EditPokemonNatureCommand(Command):
    def __init__(self, slot):
        self._slot = slot

    def execute(self, trainer):
        team = trainer.properties["team"]
        pokemon = team[self._slot]
        self._randomize_nature(pokemon)

    def _randomize_nature(self, pokemon):
        answer = inquirer.prompt([inquirer.Confirm("confirm", message="Randomize nature?", default=False)])
        if answer["confirm"]:
            pokemon["nature"] = select_random_nature()


class EditPokemonMovesetCommand(Command):
    def __init__(self, slot):
        self._slot = slot

    def execute(self, trainer):
        team = trainer.properties["team"]
        pokemon = team[self._slot]
        self._randomize_moveset(pokemon)

    def _randomize_moveset(self, pokemon):
        answer = inquirer.prompt([inquirer.Confirm("confirm", message="Randomize moveset?", default=False)])
        if answer["confirm"]:
            name = get_pokemon_name(pokemon)
            moves = PokemonWikiApi().get_pokemon_moves(name)
            pokemon["moveset"] = select_random_moveset(moves)


class PrintPokemonCommand(Command):
    def __init__(self, slot):
        self._slot = slot

    def execute(self, trainer):
        team = trainer.properties["team"]
        json_pretty = json.dumps(team[self._slot], indent=2)
        print(json_pretty)


class EditTeamLevelCommand(Command):
    def execute(self, trainer):
        try:
            level = self._ask_team_level()
            team = trainer.properties["team"]
            assert_valid_pokemon_level(level)
            for pokemon in team:
                pokemon["level"] = level
        except PokemonLevelInvalidException:
            pass

    def _ask_team_level(self):
        answer = inquirer.prompt([inquirer.Text("level", "Team Level")])
        return int(answer["level"])
