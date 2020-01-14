#!/usr/bin/env python3
"""
ui.py - UI stuff for Subtext console client.
"""
import curses

WHITE_FG = None
CYAN_FG = None
YELLOW_FG = None
MAGENTA_FG = None
RED_FG = None
PURPLE_FG = None
WHITE_BG = None
CYAN_BG = None
YELLOW_BG = None
MAGENTA_BG = None
RED_BG = None
PURPLE_BG = None

def init():
	global WHITE_FG, CYAN_FG, YELLOW_FG, MAGENTA_FG, RED_FG, PURPLE_FG
	global WHITE_BG, CYAN_BG, YELLOW_BG, MAGENTA_BG, RED_BG, PURPLE_BG
	
	WHITE_FG = curses.color_pair(1)
	CYAN_FG = curses.color_pair(2)
	YELLOW_FG = curses.color_pair(3)
	MAGENTA_FG = curses.color_pair(4)
	RED_FG = curses.color_pair(5)
	PURPLE_FG = curses.color_pair(6)

	WHITE_BG = curses.color_pair(7)
	CYAN_BG = curses.color_pair(8)
	YELLOW_BG = curses.color_pair(9)
	MAGENTA_BG = curses.color_pair(10)
	RED_BG = curses.color_pair(11)
	PURPLE_BG = curses.color_pair(12)

class UIElement:
	"""
	Base UI element class.
	"""
	def __init__(self):
		self.highlighted = False
		self.active = False
	def interactable(self):
		"""
		Check if this UIElement is interactable.
		"""
		return True
	def draw(self, win, y, x) -> (int, int):
		"""
		Draws this UI element to the given window, at the specified location.
		Returns the height and width of the element.
		"""
		win.move(y, x)
		return (1, 1)
	def on_pre_refresh(self, win, y, x):
		"""
		Called right before win.refresh() if the element is active.
		"""
		pass
	def on_enter(self):
		"""
		Called when the element is highlighted.
		"""
		self.highlighted = True
	def on_leave(self):
		"""
		Called when the element is un-highlighted.
		"""
		self.highlighted = False
	def on_activate(self):
		"""
		Called when the element is activated.
		"""
		self.active = True
	def on_deactivate(self):
		"""
		Called when the element is deactivated.
		"""
		self.active = False
	def on_key(self, key) -> bool:
		"""
		Called when a key is pressed while this element is highlighted/active.
		Returns True if the key event should be "consumed".
		"""
		return False

class Button(UIElement):
	"""
	A button.
	"""
	def __init__(self, text, on_press=None):
		super().__init__()
		self.text = text
		self.on_press = on_press
	def draw(self, win, y, x) -> (int, int):
		super().draw(win, y, x)
		win.addstr("[{}]".format(self.text), (CYAN_FG if self.active else 0) | (curses.A_REVERSE if self.highlighted else 0) | curses.A_BOLD)
		return (1, len(self.text) + 2)
	def on_activate(self):
		super().on_activate()
		if self.on_press:
			self.on_press()
		self.on_deactivate()

class TextField(UIElement):
	"""
	A text field.
	"""
	def __init__(self, label, text=""):
		super().__init__()
		self.label = label
		self.text = text
	def draw(self, win, y, x) -> (int, int):
		super().draw(win, y, x)
		win.addstr("{}: ".format(self.label))
		win.addstr("[{:<32s}]".format(self.text), (CYAN_FG if self.active else 0) | (curses.A_REVERSE if self.highlighted else 0) | curses.A_BOLD)
		return (1, len(self.label) + 4 + max(32, len(self.text)))
	def on_activate(self):
		super().on_activate()
		curses.curs_set(2)
	def on_deactivate(self):
		super().on_deactivate()
		curses.curs_set(0)
	def on_pre_refresh(self, win, y, x):
		super().on_pre_refresh(win, y, x)
		win.move(y, x + len(self.label) + 3 + len(self.text))
	def on_key(self, key) -> bool:
		super().on_key(key)
		if not self.active:
			return False
		if key >= 32 and key <= 126:
			self.text = self.text + chr(key)
			return True
		elif key == curses.KEY_BACKSPACE:
			self.text = self.text[:-1]
			return True
		return False

class ObscuredTextField(TextField):
	"""
	A text field that doesn't show its contents.
	"""
	def draw(self, win, y, x) -> (int, int):
		super(TextField, self).draw(win, y, x)
		win.addstr("{}: ".format(self.label))
		win.addstr("[{:<32s}]".format('*' * len(self.text)), (CYAN_FG if self.active else 0) | (curses.A_REVERSE if self.highlighted else 0) | curses.A_BOLD)
		return (1, len(self.label) + 4 + max(32, len(self.text)))

class Label(UIElement):
	"""
	A piece of non-interactable text.
	"""
	def __init__(self, text, attr=0):
		super().__init__()
		self.text = text
		self.attr = attr
	def interactable(self):
		return False
	def draw(self, win, y, x) -> (int, int):
		super().draw(win, y, x)
		win.addstr(y, x, self.text, self.attr)
		return (1, len(self.text))
	def on_activate(self):
		super().on_activate()
		self.on_deactivate()

class UIManager:
	"""
	Base UI manager class.
	"""
	def __init__(self, win):
		self.win = win
	def add(self, element):
		"""
		Add an element to this UIManager.
		"""
		raise NotImplementedError()
	def draw(self):
		"""
		Redraw this UIManager.
		"""
		raise NotImplementedError()
	def key(self, key):
		"""
		Process a key event.
		"""
		raise NotImplementedError()
	def run(self):
		"""
		Start event loop.
		"""
		while True:
			self.draw()
			self.key(self.win.getch())

class Form(UIManager):
	def __init__(self, win):
		self.win = win
		self.finished = False
		self.drawables = []
		self.interactables = []
	def finish(self):
		self.finished = True
	def add(self, element):
		
		self.drawables.append(element)
		if element.interactable():
			if element.active:
				element.on_deactivate()
			if element.highlighted:
				element.on_leave()
			if len(self.interactables) == 0:
				element.on_enter()
			self.interactables.append(element)
	def draw(self):
		self.win.clear()
		y = 0
		active = None
		for element in self.drawables:
			h, _ = element.draw(self.win, y, 0)
			if element.active:
				active = (element, y, 0)
			y += h
		if active:
			active[0].on_pre_refresh(self.win, active[1], active[2])
		self.win.refresh()
	def key(self, key):
		active_i = -1
		highlight_i = -1
		for i, element in enumerate(self.interactables):
			if element.active:
				active_i = i
			if element.highlighted:
				highlight_i = i
			if element.active or element.highlighted:
				if element.on_key(key):
					return
		
		if active_i >= 0:
			if key == ord('\n'):
				self.interactables[active_i].on_deactivate()
				if not self.interactables[active_i].highlighted:
					self.interactables[active_i].on_enter()
		elif highlight_i >= 0:
			if key == curses.KEY_UP and highlight_i > 0:
				self.interactables[highlight_i].on_leave()
				self.interactables[highlight_i - 1].on_enter()
			elif key == curses.KEY_DOWN and highlight_i < len(self.interactables) - 1:
				self.interactables[highlight_i].on_leave()
				self.interactables[highlight_i + 1].on_enter()
			elif key == ord('\n'):
				self.interactables[highlight_i].on_activate()
		
	def run(self):
		while not self.finished:
			self.draw()
			self.key(self.win.getch())
