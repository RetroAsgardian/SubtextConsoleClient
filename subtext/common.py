#!/usr/bin/env python3
"""
subtext.common
"""
import requests
from uuid import UUID
from typing import Optional

from .error import api_error

class ContextError(Exception):
	"""
	Generic context error.
	"""

class Context:
	"""
	Stores Subtext client context information.
	"""
	def __init__(self, url: str, *, session_id: Optional[UUID] = None, user_id: Optional[UUID] = None):
		self.url = url.rstrip("/")
		self._session_id = session_id
		self._user_id = user_id
		
		try:
			resp = self.get('/Subtext').json()
			self.instance_name = resp['instanceName']
			self.instance_id = UUID(resp['instanceId'])
		except:
			self.instance_name = None
			self.instance_id = None
	def session_id(self):
		"""
		Retrieve the associated session ID, or raise a ContextError if there is none.
		"""
		if self._session_id is None:
			raise ContextError("Context is not associated with a session, try logging in")
		return self._session_id
	def user_id(self):
		"""
		Retrieve the associated user ID, or raise a ContextError if there is none.
		"""
		if self._user_id is None:
			raise ContextError("Context is not associated with a session, try logging in")
		return self._user_id
	
	def request(self, method: str, url: str, **kwargs):
		"""
		Send an HTTP request.
		"""
		resp = requests.request(method, self.url + url, **kwargs)
		
		# Handle error
		if resp.status_code // 100 != 2:
			if resp.headers.get('Content-Type', None).startswith('application/json'):
				errdata = resp.json()
				errmsg = errdata.pop('error')
				raise api_error(errmsg, resp.status_code, **errdata)
			else:
				raise api_error(None, resp.status_code, text=resp.text)
		
		return resp
	
	def get(self, url: str, **kwargs):
		"""
		Send an HTTP GET request.
		"""
		return self.request('GET', url, **kwargs)
	def post(self, url: str, **kwargs):
		"""
		Send an HTTP POST request.
		"""
		return self.request('POST', url, **kwargs)
	def put(self, url: str, **kwargs):
		"""
		Send an HTTP PUT request.
		"""
		return self.request('PUT', url, **kwargs)
	def patch(self, url: str, **kwargs):
		"""
		Send an HTTP PATCH request.
		"""
		return self.request('PATCH', url, **kwargs)
	def delete(self, url: str, **kwargs):
		"""
		Send an HTTP DELETE request.
		"""
		return self.request('DELETE', url, **kwargs)

class SubtextObj:
	"""
	An object that exists on a Subtext instance, represented by a UUID.
	"""
	def __init__(self, id: UUID, ctx: Optional[Context] = None):
		self.id = id
		self.ctx = ctx
	def refresh(self):
		"""
		Update this object with the latest data from the Subtext instance.
		"""
		raise NotImplementedError()
