#!/usr/bin/env python3
"""
subtext.user
"""
from .common import Context, SubtextObj

from uuid import UUID
from datetime import datetime
import iso8601

from enum import Enum
from typing import Optional

from .key import Key

class UserPresence(Enum):
	online = "Online"
	away = "Away"
	busy = "Busy"
	offline = "Offline"

class User(SubtextObj):
	def __init__(self, id: UUID, ctx: Optional[Context] = None):
		super().__init__(id, ctx)
		
		self.name = None
		
		self.presence = None
		self.last_active = None
		self.status = None
		
		self.is_deleted = None
	def refresh(self):
		resp = self.ctx.get("/Subtext/user/{}".format(self.id), params={
			'sessionId': self.ctx.session_id()
		}).json()
		
		self.name = resp.get('name', None)
		
		self.presence = UserPresence(resp['presence']) if resp.get('presence', None) else None
		self.last_active = iso8601.parse_date(resp['lastActive']) if resp.get('lastActive', None) else None
		self.status = resp.get('status', None)
		
		self.is_deleted = resp.get('isDeleted', None)
	
	def get_friends(self, *, page_size: Optional[int] = None):
		"""
		Retrieve this user's friends. (This is an iterator.)
		"""
		ids = set()
		start = 0
		while True:
			resp = self.ctx.get("/Subtext/user/{}/friends".format(self.id), params={
				'sessionId': self.ctx.session_id(),
				'start': start,
				'count': page_size
			}).json()
			start += len(resp)
			if len(resp) <= 0:
				break
			for friend_id in resp:
				if friend_id not in ids:
					ids.add(friend_id)
					yield User(UUID(friend_id), self.ctx)
	
	def unfriend(self):
		"""
		Unfriend this user.
		"""
		self.ctx.delete("/Subtext/user/{}/friends/{}".format(self.ctx.user_id(), self.id), params={
			'sessionId': self.ctx.session_id()
		})
	
	def get_blocked(self, *, page_size: Optional[int] = None):
		"""
		Retrieve this user's blocked users. (This is an iterator.)
		"""
		ids = set()
		start = 0
		while True:
			resp = self.ctx.get("/Subtext/user/{}/blocked".format(self.id), params={
				'sessionId': self.ctx.session_id(),
				'start': start,
				'count': page_size
			}).json()
			start += len(resp)
			if len(resp) <= 0:
				break
			for blocked_id in resp:
				if blocked_id not in ids:
					ids.add(blocked_id)
					yield User(UUID(blocked_id), self.ctx)
	
	def block(self):
		"""
		Block this user.
		"""
		self.ctx.post("/Subtext/user/{}/blocked".format(self.ctx.user_id()), params={
			'sessionId': self.ctx.session_id(),
			'blockedId': self.id
		})
	
	def unblock(self):
		"""
		Unblock this user.
		"""
		self.ctx.delete("/Subtext/user/{}/blocked/{}".format(self.ctx.user_id(), self.id), params={
			'sessionId': self.ctx.session_id()
		})
	
	def get_friend_requests(self, *, page_size: Optional[int] = None):
		"""
		Retrieve this user's friend requests. (This is an iterator.)
		"""
		ids = set()
		start = 0
		while True:
			resp = self.ctx.get("/Subtext/user/{}/friendrequests".format(self.id), params={
				'sessionId': self.ctx.session_id(),
				'start': start,
				'count': page_size
			}).json()
			start += len(resp)
			if len(resp) <= 0:
				break
			for sender_id in resp:
				if sender_id not in ids:
					ids.add(sender_id)
					yield User(UUID(sender_id), self.ctx)
	
	def send_friend_request(self):
		"""
		Send a friend request to this user.
		"""
		self.ctx.post("/Subtext/user/{}/friendrequests".format(self.id), params={
			'sessionId': self.ctx.session_id()
		})
	
	def accept_friend_request(self):
		"""
		Accept this user's friend request.
		"""
		self.ctx.post("/Subtext/user/{}/friendrequests/{}".format(self.ctx.user_id(), self.id), params={
			'sessionId': self.ctx.session_id()
		})
	
	def reject_friend_request(self):
		"""
		Reject this user's friend request.
		"""
		self.ctx.delete("/Subtext/user/{}/friendrequests/{}".format(self.ctx.user_id(), self.id), params={
			'sessionId': self.ctx.session_id()
		})
	
	def get_keys(self, *, page_size: Optional[int] = None):
		"""
		Retrieve this user's public keys. (This is an iterator.)
		"""
		ids = set()
		start = 0
		while True:
			resp = self.ctx.get("/Subtext/user/{}/keys".format(self.id), params={
				'sessionId': self.ctx.session_id(),
				'start': start,
				'count': page_size
			}).json()
			start += len(resp)
			if len(resp) <= 0:
				break
			for key in resp:
				if key['id'] not in ids:
					ids.add(key['id'])
					yield Key(UUID(key['id']), self.ctx,
						publish_time=iso8601.parse_date(key['publishTime'])
					)
	
	def add_key(self, data: bytes):
		"""
		Add a key to this user. (This must be the logged in user.)
		"""
		self.ctx.post("/Subtext/user/{}/keys".format(self.id), params={
			'sessionId': self.ctx.session_id()
		}, data=data)
	
	def set_presence(self, presence: UserPresence, until_time: Optional[datetime] = None, other_data: Optional[str] = None):
		"""
		Set this user's presence. (This must be the logged in user.)
		"""
		self.ctx.put("/Subtext/user/{}/presence".format(self.id), params={
			'sessionId': self.ctx.session_id(),
			'presence': presence,
			'untilTime': until_time,
			'otherData': other_data
		})
