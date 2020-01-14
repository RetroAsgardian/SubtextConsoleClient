#!/usr/bin/env python3
"""
Simple TUI client for Subtext.
"""
import subtext
import json
import curses
import ui

def __main__():
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
	
	# Subtext color palette in ANSI 256-color
	COLOR_BLACK = 0x00
	COLOR_WHITE = 0x0f
	COLOR_CYAN = 0x51
	COLOR_YELLOW = 0xdc
	COLOR_MAGENTA = 0xc6
	COLOR_RED = 0xc5
	COLOR_PURPLE = 0x8d
	
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
	
	compose_win.bkgd(' ', WHITE_FG)
	compose_win.clear()
	for x in range(0, scr_w):
		compose_win.addstr(0, x, '\u2500', PURPLE_FG)
	compose_win.refresh()
	
	status_win.addstr(0, 0, "SETUP")
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
	
	nav_cmd = False
	while True:
		if nav_cmd:
			status_win.bkgd(' ', PURPLE_BG)
			status_win.clear()
			status_win.addstr(0, 0, "[NAV]")
		else:
			status_win.bkgd(' ', PURPLE_FG | curses.A_UNDERLINE)
			status_win.clear()
		status_win.addstr(0, 6, "WELCOME")
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
		main_win.refresh()
		
		key = main_win.getch()
		if nav_cmd:
			nav_cmd = False
			if key == ord('Q'):
				client.logout()
				return
		else:
			if key == curses.KEY_F1:
				nav_cmd = True

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
