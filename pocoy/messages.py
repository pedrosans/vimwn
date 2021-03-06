"""
Copyright 2017 Pedro Santos

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


# TODO: simplify, no multiple options to report like to append or return from a command
class Message:

	def __init__(self, content, level):
		self.content = content
		self.level = level
		self.indentation = ''

	def get_content(self, size_in_chars):
		return self.content

	def get_icon(self, size_in_px):
		return None


ENTER_TO_CONTINUE = 'Press ENTER or type command to continue'
memory = []
prompt_placeholder = None


def add_error(content: str):
	add(Message(content, 'error'))


def add(message: Message = None, text: str = None):
	global prompt_placeholder
	memory.append(message if message else Message(text, None))
	prompt_placeholder = ENTER_TO_CONTINUE


def clean():
	global prompt_placeholder
	prompt_placeholder = None
	del memory[:]


def clean_placeholder():
	global prompt_placeholder
	prompt_placeholder = None


def has_message():
	return memory or prompt_placeholder


def has_standard_output():
	return True if memory else False


def get():
	return memory


def print_to_console():
	for m in memory:
		print(m.get_content(1000))


def to_string():
	output = ''
	for m in memory:
		output += '\n' + m.get_content(100)
	return output
