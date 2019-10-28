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
import gi, poco
import poco.messages as messages
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from poco.view import NavigatorWindow
from poco.hint import HintStatus
from poco.commands import Command
from poco.commands import CommandHistory
from poco.commands import CommandInput

HINT_LAUNCH_KEYS = [Gdk.KEY_Tab, Gdk.KEY_ISO_Left_Tab]
HINT_LEFT = [Gdk.KEY_Left]
HINT_RIGHT = [Gdk.KEY_Right]
HINT_NAVIGATION_KEYS = HINT_LAUNCH_KEYS + HINT_LEFT + HINT_RIGHT
HINT_OPERATION_KEYS = [Gdk.KEY_Shift_L, Gdk.KEY_Shift_R, Gdk.KEY_Return] + HINT_NAVIGATION_KEYS

HISTORY_NAVIGATION_KEYS = [Gdk.KEY_Up, Gdk.KEY_Down]


# TODO chain commands
class Reading:

	def __init__(self, configurations=None, windows=None):
		self.started = False
		self.command_mode = False
		self.configurations = configurations
		self.cmd_handler_ids = []
		self.view = None
		self.windows = windows
		self.hint_status = HintStatus(self)
		self.command_history = CommandHistory()
		self._create_and_install_view()
		self.clean_state()
		messages.clean()

	def clean_state(self):
		self.started = False
		self.command_mode = False
		for handler_id in self.cmd_handler_ids:
			self.view.entry.disconnect(handler_id)
		self.cmd_handler_ids.clear()
		self.hint_status.clear_state()

	def _create_and_install_view(self):
		self.view = NavigatorWindow(self, self.windows)
		self.view.connect("focus-out-event", self._focus_out_callback)
		self.view.connect("key-press-event", self._window_key_press_callback)

	#
	# PUBLIC API
	#
	def reload(self, e_time):
		self.clean_state()
		self.view.close()
		self._create_and_install_view()

	def set_command_mode(self):
		self.command_mode = True

		self.view.update()

		r_id = self.view.entry.connect("key-release-event", self.on_entry_key_release)
		p_id = self.view.entry.connect("key-press-event", self.on_entry_key_press)
		a_id = self.view.entry.connect("activate", self.on_command, None)

		self.cmd_handler_ids.extend([r_id, p_id, a_id])

	def in_command_mode(self):
		return self.command_mode

	#
	# CALLBACKS
	#
	def _focus_out_callback(self, widget, event):
		self.end()

	def _window_key_press_callback(self, widget, event):
		ctrl = (event.state & Gdk.ModifierType.CONTROL_MASK)

		if event.keyval == Gdk.KEY_Escape or (ctrl and event.keyval == Gdk.KEY_bracketleft):
			self.escape(CommandInput(time=event.time, keyval=event.keyval))
			return

		if self.in_command_mode():
			return

		if event.keyval == Gdk.KEY_colon and not ctrl:
			self.colon(CommandInput(time=event.time, keyval=event.keyval))
			return True

		if event.keyval == Gdk.KEY_Return:
			self.enter(CommandInput(time=event.time, keyval=event.keyval))
			return True

	def on_entry_key_release(self, widget, event):
		if event.keyval in HINT_OPERATION_KEYS:
			return False

		if not self.view.entry.get_text().strip():
			self.clean_state()
			self.show(Gtk.get_current_event_time())
			return True

		if self.configurations.is_auto_hint():
			self.hint_status.hint(CommandInput(text=self.view.get_command()).parse())
		else:
			self.hint_status.clear_state()

		if self.hint_status.hinting:
			self.view.hint(self.hint_status.hints, self.hint_status.highlight_index, self.hint_status.should_auto_hint())
		else:
			self.view.clean_hints()

	def on_entry_key_press(self, widget, event):
		if event.keyval in HISTORY_NAVIGATION_KEYS:
			self.command_history.navigate_history(-1 if event.keyval == Gdk.KEY_Up else 1, self.view.get_command())
			self.view.set_command(self.command_history.current_command())
			self.view.clean_hints()
			self.hint_status.clear_state()
			return True
		else:
			self.command_history.reset_history_pointer()

		if event.keyval not in HINT_NAVIGATION_KEYS:
			return False

		if not self.hint_status.hinting and event.keyval in HINT_LAUNCH_KEYS:
			self.hint_status.hint(CommandInput(text=self.view.get_command()).parse())

		if self.hint_status.hinting:
			shift_mask = event.state & Gdk.ModifierType.SHIFT_MASK
			right = event.keyval in HINT_RIGHT or (event.keyval in HINT_LAUNCH_KEYS and not shift_mask )
			self.hint_status.cycle(1 if right else -1)
			if len(self.hint_status.hints) == 1:
				self.view.clean_hints()
			else:
				self.view.hint(self.hint_status.hints, self.hint_status.highlight_index, self.hint_status.should_auto_hint())
			self.view.set_command(self.hint_status.mount_input())

		return True

	def on_command(self, pane_owner, current):
		if not self.command_mode:
			return

		gtk_time = Gtk.get_current_event_time()
		cmd = self.view.get_command()

		if self.hint_status.should_auto_hint():
			self.hint_status.cycle(1)
			cmd = self.hint_status.mount_input()

		self.command_history.append(cmd)

		if Command.has_multiple_commands(cmd):
			raise Exception('TODO: iterate multiple commands')

		command_input = CommandInput(time=gtk_time, text=cmd).parse()
		command = Command.get_matching_command(command_input)

		if command:
			poco.service.execute(command.function, command_input)
		else:
			self.clean_state()
			self.show(gtk_time, error_message='Not an editor command: ' + cmd)

	# TODO: remove from here
	def execute(self, cmd):
		self.windows.read_screen()
		command_input = CommandInput(time=None, text=cmd).parse()
		command = Command.get_matching_command(command_input)
		command.function(command_input)

	#
	# COMMANDS
	#
	def start(self, c_in):
		self.started = True
		messages.clean()

	def show(self, e_time, error_message=None):
		# TODO move to view
		self.view.present_with_time(e_time)
		self.view.get_window().focus(e_time)
		if error_message:
			messages.add(error_message, 'error')
		self.view.update()

	def end(self):
		messages.clean()
		self.clean_state()
		self.view.hide()

	# TODO: remove from command format
	def colon(self, c_in):
		self.set_command_mode()

	def enter(self, c_in):
		messages.clean()
		self.show(c_in.time)

	def escape(self, c_in):
		self.end()
