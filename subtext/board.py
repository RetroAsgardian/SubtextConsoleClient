#!/usr/bin/env python3
"""
subtext.board
"""
from .common import Context, SubtextObj
# from .content import Content, parse_content

from uuid import UUID
from datetime import datetime
import iso8601
import json
import base64

from enum import Enum
from typing import Optional, List

from .user import User

class BoardEncryption(Enum):
	gnupg = "GnuPG"
	shared_key = "SharedKey"
	none = "None"

class Board(SubtextObj):
	def __init__(self, id: UUID, ctx: Optional[Context] = None, *,
		name: Optional[str] = None,
		owner: Optional[User] = None,
		encryption: Optional[BoardEncryption] = None,
		last_update: Optional[datetime] = None,
		last_significant_update: Optional[datetime] = None,
		is_direct: Optional[bool] = None,
		members: Optional[List[User]] = None
	):
		super().__init__(id, ctx)
		
		self.name = name
		self.owner = owner
		self.encryption = encryption
		
		self.last_update = last_update
		self.last_significant_update = last_significant_update
		
		self.is_direct = is_direct
		
		self.members = members
	def refresh(self):
		resp = self.ctx.get("/Subtext/board/{}".format(self.id), params={
			'sessionId': self.ctx.session_id()
		}).json()
		
		self.name = resp.get('name', None)
		self.owner = User(UUID(resp['ownerId']), self.ctx) if resp.get('ownerId', None) else None
		self.encryption = BoardEncryption(resp['encryption']) if resp.get('encryption', None) else None
		
		self.last_update = iso8601.parse_date(resp['lastUpdate']) if resp.get('lastUpdate', None) else None
		self.last_significant_update = iso8601.parse_date(resp['lastSignificantUpdate']) if resp.get('lastSignificantUpdate', None) else None
		
		self.is_direct = resp.get('isDirect', None)
		
		self.members = list(self._get_members())
		
	def _get_members(self, *, page_size: Optional[int] = None):
		"""
		Retrieve this board's members. (This is an iterator.)
		"""
		ids = set()
		start = 0
		while True:
			resp = self.ctx.get("/Subtext/board/{}/members".format(self.id), params={
				'sessionId': self.ctx.session_id(),
				'start': start,
				'count': page_size
			}).json()
			start += len(resp)
			if len(resp) <= 0:
				break
			for member_id in resp:
				if member_id not in ids:
					ids.add(member_id)
					yield User(UUID(member_id), self.ctx)
	def add_member(self, user: User):
		"""
		Add a user to this board.
		"""
		self.ctx.post("/Subtext/board/{}/members".format(self.id), params={
			'sessionId': self.ctx.session_id(),
			'userId': user.id
		})
	def remove_member(self, user: User):
		"""
		Remove a user from this board.
		"""
		self.ctx.delete("/Subtext/board/{}/members".format(self.id), params={
			'sessionId': self.ctx.session_id(),
			'userId': user.id
		})
	def get_messages(self, *, type: Optional[str] = None, only_system: bool = False, since_time: Optional[datetime] = None, page_size: Optional[int] = None):
		"""
		Retrieve this board's messages. (This is an iterator.)
		"""
		ids = set()
		start = 0
		while True:
			resp = self.ctx.get("/Subtext/board/{}/messages".format(self.id), params={
				'sessionId': self.ctx.session_id(),
				'start': start,
				'count': page_size,
				'type': type,
				'onlySystem': only_system,
				'sinceTime': since_time
			}).json()
			start += len(resp)
			if len(resp) <= 0:
				break
			for message in resp:
				if message['id'] not in ids:
					ids.add(message['id'])
					yield Message(UUID(message['id']), self.ctx,
						board=self,
						timestamp=iso8601.parse_date(message['timestamp']),
						author=User(UUID(message['authorId'])),
						is_system=message['isSystem'],
						type=message['type'],
						content=base64.b64decode(message['content']) if message.get('content', None) else None
					)
	def send_message(self, content: bytes, *, type: Optional[str] = None, is_system: bool = False):
		"""
		Send a message to this board.
		"""
		self.ctx.post("/Subtext/board/{}/messages".format(self.id), params={
			'sessionId': self.ctx.session_id(),
			'isSystem': is_system,
			'type': type or "Message"
		}, data=content)
	@classmethod
	def direct(cls, user: User):
		"""
		Get the direct message board for communicating with the given user.
		If it doesn't already exist, it will be created.
		"""
		resp = user.ctx.post("/Subtext/board/createdirect", params={
			'sessionId': user.ctx.session_id(),
			'recipientId': user.id
		}).json()
		board = cls(UUID(resp), ctx=user.ctx)
		board.refresh()
		return board

class Message(SubtextObj):
	def __init__(self, id: UUID, ctx: Optional[Context] = None, *,
		board: Optional[Board] = None,
		timestamp: Optional[datetime] = None,
		author: Optional[User] = None,
		is_system: Optional[bool] = None,
		type: Optional[str] = None,
		content: Optional[bytes] = None
	):
		super().__init__(id, ctx)
		
		self.board = board
		
		self.timestamp = timestamp
		self.author = author
		
		self.is_system = is_system
		self.type = type
		
		self.content = content
	def refresh(self):
		resp = self.ctx.get("/Subtext/board/{}/messages/{}".format(self.board.id, self.id), params={
			'sessionId': self.ctx.session_id()
		})
		
		if 'X-Metadata' in resp.headers:
			metadata = json.loads(resp.headers['X-Metadata'])
			self.timestamp = iso8601.parse_date(metadata['timestamp'])
			self.author = User(UUID(metadata['authorId']), self.ctx)
			self.is_system = metadata['isSystem']
			self.type = metadata['type']
		
		self.content = resp.content
