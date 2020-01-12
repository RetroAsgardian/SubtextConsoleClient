#!/usr/bin/env python3
"""
subtext - Official Python client API for Subtext.
"""
from .common import ContextError, Context, SubtextObj
from .error import *
from .user import User, UserPresence
from .key import Key
from .board import Board, BoardEncryption, Message
from .encryption import Encryption

from . import content

from uuid import UUID
from datetime import datetime
import iso8601

from typing import Optional, Union

class Client:
	"""
	Subtext Client API class.
	"""
	def __init__(self, url: str):
		self.ctx = Context(url)
		
		# Check for a valid Subtext instance
		resp = self.ctx.get('/')
		if resp.status_code != 200 or resp.text.strip().capitalize() != "Subtext":
			raise ValueError("Could not detect a valid Subtext instance at {}".format(self.ctx.url))
		
		self.instance_name = self.ctx.instance_name
		self.instance_id = self.ctx.instance_id
	
	def login(self, user: Union[UUID, str], password: str):
		"""
		Log in with the given credentials.
		"""
		if self.ctx._session_id is not None or self.ctx._user_id is not None:
			raise ContextError("Context is already associated with a session, try logging out")
		
		if isinstance(user, UUID):
			user_id = user
		else:
			user_id = self.ctx.get('/Subtext/user/queryidbyname', params={
				'name': user
			}).json()
		
		session_id = self.ctx.post('/Subtext/user/login', params={
			'userId': user_id,
			'password': password
		}).json()
		
		self.ctx._session_id = session_id
		self.ctx._user_id = user_id
	
	def heartbeat(self):
		"""
		Keep the current session alive.
		"""
		self.ctx.post('/Subtext/user/heartbeat', params={
			'sessionId': self.ctx.session_id()
		})
	
	def logout(self):
		"""
		Log out of the current session.
		"""
		self.ctx.post('/Subtext/user/logout', params={
			'sessionId': self.ctx.session_id()
		})
		
		self.ctx._session_id = None
		self.ctx._user_id = None
	
	def get_user(self, user_id: Optional[UUID] = None):
		"""
		Retrieve a user. If a user ID is not given, it defaults to retrieving the logged in user.
		"""
		user = User(user_id or self.ctx.user_id(), self.ctx)
		user.refresh()
		return user
	
	def get_boards(self):
		"""
		Retrieve all boards visible to the logged in user. (This is an iterator.)
		"""
		ids = set()
		start = 0
		while True:
			resp = self.ctx.get("/Subtext/board", params={
				'sessionId': self.ctx.session_id(),
				'start': start
			}).json()
			start += len(resp)
			if len(resp) <= 0:
				break
			for board in resp:
				if board['id'] not in ids:
					ids.add(board['id'])
					yield Board(UUID(board['id']), self.ctx,
						name=board['name'],
						owner=User(UUID(board['ownerId'])),
						encryption=BoardEncryption(board['encryption']),
						last_update=iso8601.parse_date(board['lastUpdate']),
						last_significant_update=iso8601.parse_date(board['lastSignificantUpdate']),
						is_direct=board['isDirect']
					)
	
	def get_board(self, board_id: UUID):
		"""
		Retrieve a board.
		"""
		board = Board(board_id, self.ctx)
		board.refresh()
		return board
