#!/usr/bin/env python3
"""
Simple TUI client for Subtext.
"""
import subtext
import json
import curses
import ui

# Subtext color palette in ANSI 256-color
COLOR_BLACK = 0x00
COLOR_WHITE = 0x0f
COLOR_CYAN = 0x51
COLOR_YELLOW = 0xdc
COLOR_MAGENTA = 0xc6
COLOR_RED = 0xc5
COLOR_PURPLE = 0x8d

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

# windows 3.1 moment
# this is used to store event data
# it's kinda hacky, but it works
EPARAM = None

class Page:
	"""
	A page in the client.
	"""
	def __init__(self, status_win, main_win, compose_win, client: subtext.Client, crypto: subtext.Encryption, user: subtext.User):
		self.status_win = status_win
		self.main_win = main_win
		self.compose_win = compose_win
		self.client = client
		self.crypto = crypto
		self.user = user
	def draw(self):
		"""
		Draw the page.
		"""
		pass
	def on_key(self, key):
		"""
		Handle a keypress.
		"""
		pass

class FriendsPage(Page):
	def __init__(self, status_win, main_win, compose_win, client: subtext.Client, crypto: subtext.Encryption, user: subtext.User):
		super().__init__(status_win, main_win, compose_win, client, crypto, user)
		self.friends = list(self.user.get_friends())
		self.pos = 0
		self.scroll_pos = 0
	def draw(self):
		self.status_win.addstr(0, 0, "FRIENDS")
		self.status_win.refresh()
		
		self.main_win.clear()
		if len(self.friends) > 0:
			i = 0
			for friend in self.friends:
				if i >= self.main_win.getmaxyx()[0]:
					break
				if friend.name is None:
					friend.refresh()
				self.main_win.addstr(i, 0, friend.name, curses.A_REVERSE if self.pos == i else 0)
				i += 1
		else:
			self.main_win.addstr(0, 0, "You don't have any friends.")
	def on_key(self, key):
		global EPARAM
		# TODO scrolling
		if (key == curses.KEY_UP or key == ord('j')) and self.pos > 0:
			self.pos -= 1
		elif (key == curses.KEY_DOWN or key == ord('k')) and self.pos < len(self.friends) - 1:
			self.pos += 1
		elif key == ord('u'): # Unfriend
			self.friends[self.pos].unfriend()
			EPARAM = 0
			curses.ungetch(curses.KEY_F32) # Refresh

class BoardsPage(Page):
	def __init__(self, status_win, main_win, compose_win, client: subtext.Client, crypto: subtext.Encryption, user: subtext.User):
		super().__init__(status_win, main_win, compose_win, client, crypto, user)
		self.boards = list(self.client.get_boards())
		self.pos = 0
		self.scroll_pos = 0
	def draw(self):
		self.status_win.addstr(0, 0, "BOARDS")
		self.status_win.refresh()
		
		self.main_win.clear()
		if len(self.boards) > 0:
			i = 0
			for board in self.boards:
				if i >= self.main_win.getmaxyx()[0]:
					break
				if board.name is None:
					board.refresh()
				self.main_win.addstr(i, 0, board.name, curses.A_REVERSE if self.pos == i else 0)
				i += 1
		else:
			self.main_win.addstr(0, 0, "You're not in any boards.")
	def on_key(self, key):
		global EPARAM
		# TODO scrolling
		if (key == curses.KEY_UP or key == ord('j')) and self.pos > 0:
			self.pos -= 1
		elif (key == curses.KEY_DOWN or key == ord('k')) and self.pos < len(self.boards) - 1:
			self.pos += 1
		elif key == ord('\n'):
			EPARAM = self.boards[self.pos]
			curses.ungetch(curses.KEY_F33) # View board

class FriendRequestsPage(Page):
	def __init__(self, status_win, main_win, compose_win, client: subtext.Client, crypto: subtext.Encryption, user: subtext.User):
		super().__init__(status_win, main_win, compose_win, client, crypto, user)
		self.friend_requests = list(self.user.get_friend_requests())
		self.pos = 0
		self.scroll_pos = 0
	def draw(self):
		self.status_win.addstr(0, 0, "FRIEND REQUESTS")
		self.status_win.refresh()
		
		self.main_win.clear()
		if len(self.friend_requests) > 0:
			i = 0
			for friend_request in self.friend_requests:
				if i >= self.main_win.getmaxyx()[0]:
					break
				if friend_request.name is None:
					friend_request.refresh()
				self.main_win.addstr(i, 0, friend_request.name, curses.A_REVERSE if self.pos == i else 0)
				i += 1
		else:
			self.main_win.addstr(0, 0, "You don't have any friend requests.")
	def on_key(self, key):
		global EPARAM
		# TODO scrolling
		if (key == curses.KEY_UP or key == ord('j')) and self.pos > 0:
			self.pos -= 1
		elif (key == curses.KEY_DOWN or key == ord('k')) and self.pos < len(self.friend_requests) - 1:
			self.pos += 1
		elif key == ord('a') or key == ord('\n'): # Accept friend request
			self.friend_requests[self.pos].accept_friend_request()
			EPARAM = 0
			curses.ungetch(curses.KEY_F32) # Refresh
		elif key == ord('r'): # Reject friend request
			self.friend_requests[self.pos].reject_friend_request()
			EPARAM = 0
			curses.ungetch(curses.KEY_F32) # Refresh

class BoardPage(Page):
	def __init__(self, status_win, main_win, compose_win, client: subtext.Client, crypto: subtext.Encryption, user: subtext.User, board: subtext.Board):
		super().__init__(status_win, main_win, compose_win, client, crypto, user)
		self.board = board
		if self.board.last_update is None:
			board.refresh()
		self.last_update = self.board.last_update
		self.messages = []
		for msg in self.board.get_messages(type="Message"):
			if len(self.messages) >= 50:
				break
			if msg.content is None:
				msg.refresh()
			try:
				data, trust = self.crypto.decrypt(msg.content)
				if msg.author.name is None:
					msg.author.refresh()
				self.messages.insert(0, (data.decode('utf-8') or "(Cannot decrypt)", trust, msg.author.name))
			except:
				if msg.author.name is None:
					msg.author.refresh()
				self.messages.insert(0, ("(Cannot decrypt)", False, msg.author.name))
		self.pos = 0
		self.scroll_pos = 0
		self.compose = False
		self.compose_text = ''
	def draw(self):
		self.status_win.addstr(0, 0, "BOARD {}".format(self.board.name))
		self.status_win.refresh()
		
		self.main_win.clear()
		if len(self.messages) > 0:
			i = 0
			for msg in self.messages:
				if i >= self.main_win.getmaxyx()[0]:
					break
				self.main_win.addstr(i, 0, '{}: {}'.format(msg[2], msg[0]), (0 if msg[1] else YELLOW_FG) | (curses.A_REVERSE if self.pos == i else 0))
				i += 1
		else:
			self.main_win.addstr(0, 0, "No messages")
		
		if self.compose:
			self.compose_win.bkgd(' ', PURPLE_BG)
			self.compose_win.clear()
			self.compose_win.addstr(0, 0, self.compose_text)
			self.compose_win.addstr(' ', curses.A_REVERSE)
		else:
			self.compose_win.bkgd(' ', PURPLE_FG)
			self.compose_win.clear()
			for x in range(0, self.compose_win.getmaxyx()[1]):
				self.compose_win.addstr(0, x, '\u2500')
		self.compose_win.refresh()
		
	def on_key(self, key):
		global EPARAM
		if not self.compose:
			# TODO scrolling
			if (key == curses.KEY_UP or key == ord('j')) and self.pos > 0:
				self.pos -= 1
			elif (key == curses.KEY_DOWN or key == ord('k')) and self.pos < len(self.messages) - 1:
				self.pos += 1
			elif key == curses.KEY_F1:
				self.compose = True
			self.board.refresh()
			if self.board.last_update > self.last_update:
				EPARAM = 0
				curses.ungetch(curses.KEY_F32) # Refresh
		else:
			if key == curses.KEY_F1:
				self.compose = False
				self.compose_text = ''
			elif key == ord('\n'):
				self.compose = False
				if len(self.compose_text) > 0:
					self.board.send_message(self.crypto.encrypt(
						self.compose_text.encode('utf-8'),
						['{}@{}'.format(user.id, user.ctx.instance_id) for user in self.board.members]
					), type="Message")
					EPARAM = 0
					curses.ungetch(curses.KEY_F32) # Refresh
				self.compose_text = ''
			elif key == curses.KEY_BACKSPACE:
				self.compose_text = self.compose_text[:-1]
			elif key >= 0x20 and key <= 0x7e:
				self.compose_text = self.compose_text + chr(key)
	

def __main__():
	global WHITE_FG, CYAN_FG, YELLOW_FG, MAGENTA_FG, RED_FG, PURPLE_FG
	global WHITE_BG, CYAN_BG, YELLOW_BG, MAGENTA_BG, RED_BG, PURPLE_BG
	global EPARAM
	
	stdscr = curses.initscr()
	
	# Set up terminal for TUI
	curses.noecho()
	curses.raw()
	curses.start_color()
	curses.curs_set(0)
	
	scr_h, scr_w = stdscr.getmaxyx()
	
	# Create windows
	status_win = curses.newwin(1, scr_w, 0, 0)
	main_win = curses.newwin(scr_h - 4, scr_w, 1, 0)
	compose_win = curses.newwin(3, scr_w, scr_h - 3, 0)
	
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
	
	ui.init()
	
	# Set up color pairs
	curses.init_pair(1, COLOR_WHITE, COLOR_BLACK)
	curses.init_pair(2, COLOR_CYAN, COLOR_BLACK)
	curses.init_pair(3, COLOR_YELLOW, COLOR_BLACK)
	curses.init_pair(4, COLOR_MAGENTA, COLOR_BLACK)
	curses.init_pair(5, COLOR_RED, COLOR_BLACK)
	curses.init_pair(6, COLOR_PURPLE, COLOR_BLACK)
	
	curses.init_pair(7, COLOR_BLACK, COLOR_WHITE)
	curses.init_pair(8, COLOR_BLACK, COLOR_CYAN)
	curses.init_pair(9, COLOR_BLACK, COLOR_YELLOW)
	curses.init_pair(10, COLOR_BLACK, COLOR_MAGENTA)
	curses.init_pair(11, COLOR_BLACK, COLOR_RED)
	curses.init_pair(12, COLOR_BLACK, COLOR_PURPLE)
	
	
	# Set up windows
	status_win.bkgd(' ', PURPLE_FG | curses.A_UNDERLINE)
	status_win.clear()
	
	main_win.bkgd(' ', WHITE_FG)
	main_win.clear()
	
	compose_win.bkgd(' ', PURPLE_FG)
	compose_win.clear()
	for x in range(0, scr_w):
		compose_win.addstr(0, x, '\u2500')
	compose_win.refresh()
	
	status_win.addstr(0, 0, "LOGIN")
	status_win.refresh()
	
	status_win.keypad(True)
	main_win.keypad(True)
	compose_win.keypad(True)
	
	def hostname_form() -> str:
		form = ui.Form(main_win)
		hostname_field = ui.TextField("Hostname")
		error_label = ui.Label("", YELLOW_FG)
		
		def ok():
			try:
				client = subtext.Client(hostname_field.text)
				form.finish()
			except BaseException as e:
				error_label.text = str(e)
		
		def quit():
			hostname_field.text = ""
			form.finish()
		
		form.add(hostname_field)
		form.add(ui.Button("OK", ok))
		form.add(ui.Button("Quit", quit))
		form.add(error_label)
		
		form.run()
		
		return hostname_field.text
	
	hostname = hostname_form()
	if hostname == "":
		return
	
	client = subtext.Client(hostname)
	
	def login_form():
		form = ui.Form(main_win)
		username_field = ui.TextField("Username")
		password_field = ui.ObscuredTextField("Password")
		error_label = ui.Label("", YELLOW_FG)
		
		def login():
			try:
				client.login(username_field.text, password_field.text)
				form.finish()
			except BaseException as e:
				error_label.text = str(e)
		
		def create():
			try:
				user_id = client.create_user(username_field.text, password_field.text)
				client.login(user_id, password_field.text)
				form.finish()
			except BaseException as e:
				error_label.text = str(e)
		
		form.add(username_field)
		form.add(password_field)
		form.add(ui.Button("Log in", login))
		form.add(ui.Button("Create", create))
		form.add(ui.Button("Quit", form.finish))
		form.add(error_label)
		
		form.run()
	
	login_form()
	
	user = client.get_user()
	crypto = subtext.Encryption(user)
	
	# Wait up to 2 seconds for a keypress
	curses.halfdelay(20)
	
	nav_cmd = False
	page = None
	while True:
		if nav_cmd:
			status_win.bkgd(' ', PURPLE_BG)
			status_win.clear()
		else:
			status_win.bkgd(' ', PURPLE_FG | curses.A_UNDERLINE)
			status_win.clear()
		
		if page is None:
			status_win.addstr(0, 0, "WELCOME")
			status_win.refresh()
			
			main_win.clear()
			main_win.addstr(0, 0, "You are logged in as ")
			main_win.addstr(str(user.id), MAGENTA_FG | curses.A_BOLD)
			main_win.addstr("@{}".format(client.instance_id))
			main_win.addstr(2, 0, "F1 to begin nav command")
			main_win.addstr(3, 0, "F1 Q - Log out and quit")
			main_win.addstr(4, 0, "F1 f - Friend list")
			main_win.addstr(5, 0, "F1 b - Board list")
			main_win.addstr(6, 0, "F1 F - Friend request list")
			main_win.addstr(7, 0, "F1 B - Blocked user list")
			main_win.addstr(8, 0, "F1 c - Compose message")
			main_win.addstr(9, 0, "F1 R - Refresh view")
			main_win.addstr(10, 0, "F1 h - Show help/welcome page")
			main_win.refresh()
		else:
			page.draw()
		
		try:
			key = main_win.getch()
		except:
			key = None
		if nav_cmd:
			if key is not None:
				nav_cmd = False
			if key == ord('Q'):
				client.logout()
				return
			elif key == ord('f'):
				page = FriendsPage(status_win, main_win, compose_win, client, crypto, user)
			elif key == ord('b'):
				page = BoardsPage(status_win, main_win, compose_win, client, crypto, user)
			elif key == ord('F'):
				page = FriendRequestsPage(status_win, main_win, compose_win, client, crypto, user)
			elif key == ord('R'):
				if page is not None:
					if isinstance(page, BoardPage):
						page = page.__class__(status_win, main_win, compose_win, client, crypto, user, page.board)
					else:
						page = page.__class__(status_win, main_win, compose_win, client, crypto, user)
			elif key == ord('h'):
				page = None
			elif key == ord('c'):
				# The page would never normally recieve F1
				page.on_key(curses.KEY_F1)
		elif key == curses.KEY_F32: # Refresh event
			# Prevent an event from being fired by the user pressing the F32 key
			# Yes, there is an F32 key
			if EPARAM is not None:
				if page is not None:
					if isinstance(page, BoardPage):
						page = page.__class__(status_win, main_win, compose_win, client, crypto, user, page.board)
					else:
						page = page.__class__(status_win, main_win, compose_win, client, crypto, user)
				EPARAM = None
		elif key == curses.KEY_F33: # View board event
			if EPARAM is not None:
				page = BoardPage(status_win, main_win, compose_win, client, crypto, user, EPARAM)
				EPARAM = None
		else:
			if key == curses.KEY_F1:
				nav_cmd = True
			elif page is not None:
				page.on_key(key)

# Elaborate wrapper to ensure terminal is reset even if __main__() throws an exception
if __name__ == "__main__":
	exc = None
	
	try:
		__main__()
	except BaseException as e:
		exc = e
	
	curses.curs_set(2)
	curses.echo()
	curses.noraw()
	curses.endwin()
	
	if exc:
		raise exc
