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
		compose_win.addch(0, x, curses.ACS_HLINE, PURPLE_FG)
	compose_win.refresh()
	
	status_win.addstr(0, 0, "SETUP")
	status_win.refresh()
	
	main_win.keypad(True)
	
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
				error_label.text = str(type(e)) + " " + str(e)
		
		form.add(username_field)
		form.add(password_field)
		form.add(ui.Button("Log in", login))
		form.add(ui.Button("Quit", form.finish))
		form.add(error_label)
		
		form.run()
	
	login_form()
	
	client.logout()

# Elaborate wrapper
if __name__ == "__main__":
	exc = None
	
	try:
		__main__()
	except BaseException as e:
		exc = e
	
	# Reset terminal settings
	curses.curs_set(2)
	curses.echo()
	curses.noraw()
	curses.endwin()
	
	if exc:
		raise exc
