import unittest
import pocoy.model as model
from pocoy.model import Monitor
from unittest.mock import MagicMock

workspace = MagicMock()
workspace.get_number = lambda: 0
screen = MagicMock()
screen.get_workspaces = lambda: [workspace]
monitor = Monitor(primary=True)
model.monitors.primaries = {0: monitor}
model.monitors.by_workspace = {0: [monitor]}


class ModelTestCase(unittest.TestCase):

	def test_read_user_config(self):
		model.read_user_config(DEFAULTS, screen)
		primary: Monitor = model.monitors.get_primary(workspace)
		self.assertEqual(primary.nmaster, 1)
		self.assertEqual(primary.mfact, 0.55)
		self.assertEqual(primary.function_key, 'T')


DEFAULTS = {
	'workspaces': [
		{
			'monitors': [
				{'nmaster': 1, 'mfact': 0.55, 'function': 'T'},
				{'nmaster': 1, 'mfact': 0.55, 'function': None}
			]
		},
		{
			'monitors': [
				{'nmaster': 1, 'mfact': 0.55, 'function': None},
				{'nmaster': 1, 'mfact': 0.55, 'function': None}
			]
		}
	]
}


if __name__ == '__main__':
	unittest.main()
