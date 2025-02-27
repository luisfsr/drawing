# tool_rotate.py
#
# Copyright 2019 Romain F. T.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk, Gdk
import cairo

from .abstract_canvas_tool import AbstractCanvasTool
from .bottombar import DrawingAdaptativeBottomBar

class ToolRotate(AbstractCanvasTool):
	__gtype_name__ = 'ToolRotate'

	def __init__(self, window):
		super().__init__('rotate', _("Rotate"), 'tool-rotate-symbolic', window)
		self.cursor_name = 'not-allowed'
		self.apply_to_selection = False
		self.flip_h = False
		self.flip_v = False

		self.add_tool_action_simple('rotate-clockwise', self.on_right_clicked)
		self.add_tool_action_simple('rotate-counter-cw', self.on_left_clicked)
		self.add_tool_action_simple('rotate-flip-h', self.on_horizontal_clicked)
		self.add_tool_action_simple('rotate-flip-v', self.on_vertical_clicked)

	def try_build_panel(self):
		self.panel_id = 'rotate'
		self.window.options_manager.try_add_bottom_panel(self.panel_id, self)

	def build_bottom_panel(self):
		panel = RotateToolPanel(self.window, self)
		self.angle_btn = panel.angle_btn
		self.angle_btn.connect('value-changed', self.on_angle_changed)
		return panel

	def get_edition_status(self):
		if self.apply_to_selection:
			return _("Rotating the selection")
		else:
			return _("Rotating the canvas")

	def on_tool_selected(self, *args):
		super().on_tool_selected()
		self.flip_h = False
		self.flip_v = False
		self.angle_btn.set_value(0.0)
		self.on_angle_changed()
		# the panel is updated by the window according to self.apply_to_selection

	def get_angle(self):
		return self.angle_btn.get_value_as_int()

	def on_right_clicked(self, *args):
		self.angle_btn.set_value(self.get_angle() + 90)

	def on_left_clicked(self, *args):
		self.angle_btn.set_value(self.get_angle() - 90)

	def on_vertical_clicked(self, *args):
		self.flip_v = not self.flip_v
		self.update_temp_pixbuf()

	def on_horizontal_clicked(self, *args):
		self.flip_h = not self.flip_h
		self.update_temp_pixbuf()

	def on_angle_changed(self, *args):
		angle = self.get_angle()
		angle = angle % 360
		if angle < 0:
			angle += 180
		if True:
		# if not self.apply_to_selection:
			angle = int(angle/90) * 90
		if angle != self.get_angle():
			self.angle_btn.set_value(angle)
		self.update_temp_pixbuf()

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'is_selection': self.apply_to_selection,
			'is_preview': True,
			'angle': self.get_angle(),
			'flip_h': self.flip_h,
			'flip_v': self.flip_v
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		angle = operation['angle']
		flip_h = operation['flip_h']
		flip_v = operation['flip_v']
		if operation['is_selection']:
			source_pixbuf = self.get_selection_pixbuf()
		else:
			source_pixbuf = self.get_main_pixbuf()
		# TODO rotations plus fines (pour la sélection seulement)
		# passer par un source_pixbuf.copy() si on ne fait plus de rotate_simple
		new_pixbuf = source_pixbuf.rotate_simple(angle)
		if flip_h:
			new_pixbuf = new_pixbuf.flip(True)
		if flip_v:
			new_pixbuf = new_pixbuf.flip(False)
		self.get_image().set_temp_pixbuf(new_pixbuf)
		self.common_end_operation(operation['is_preview'], operation['is_selection'])

	############################################################################
################################################################################

class RotateToolPanel(DrawingAdaptativeBottomBar):
	__gtype_name__ = 'RotateToolPanel'

	def __init__(self, window, rotate_tool):
		super().__init__()
		self.window = window
		# knowing the tool is needed because the panel doesn't compact the same
		# way if it's applied to the selection
		self.rotate_tool = rotate_tool
		builder = self.build_ui('tools/ui/tool_rotate.ui')
		self.angle_btn = builder.get_object('angle_btn')
		self.more_btn = builder.get_object('more_btn')
		self.angle_box = builder.get_object('angle_box')
		self.rotate_box = builder.get_object('rotate_box')
		self.flip_box = builder.get_object('flip_box')

	def init_adaptability(self):
		super().init_adaptability()
		temp_limit_size = self.centered_box.get_preferred_width()[0] + \
		                    self.cancel_btn.get_preferred_width()[0] + \
		                     self.apply_btn.get_preferred_width()[0]
		self.set_limit_size(temp_limit_size)

	def update_for_new_tool(self, tool):
		self.set_compact(self.is_narrow)

	def toggle_options_menu(self):
		if self.more_btn.get_visible():
			self.more_btn.set_active(not self.more_btn.get_active())

	def set_compact(self, state):
		super().set_compact(state)
		if self.rotate_tool.apply_to_selection:
			self.more_btn.set_visible(state)
			self.angle_box.set_visible(True)
			self.rotate_box.set_visible(not state)
			self.flip_box.set_visible(not state)
		else:
			self.more_btn.set_visible(False)
			self.angle_box.set_visible(False)
			self.rotate_box.set_visible(True)
			self.flip_box.set_visible(True)

	############################################################################
################################################################################

