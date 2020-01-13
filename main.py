#!/usr/bin/env python3
"""
Simple TUI client for Subtext.
"""
import subtext
import json
import curses

def __main__():
	stdscr = curses.initscr()
	
	# Set up terminal for TUI
	curses.noecho()
	curses.raw()
	curses.start_color()
	curses.curs_set(0)
	stdscr.keypad(True)
	
	scr_h, scr_w = stdscr.getmaxyx()
	
	# Create windows
	status_win = curses.newwin(1, scr_w, 0, 0)
	main_win = curses.newwin(scr_h - 4, scr_w, 1, 0)
	compose_win = curses.newwin(3, scr_w, scr_h - 4, 0)
	
	# White on blue - status window
	curses.init_pair(1, 0x0f, 0x04)
	
	main_win.refresh()
	main_win.getch()

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
		print(exc)
