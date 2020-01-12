#!/usr/bin/env python3
"""
subtext.error
"""
import iso8601 as _iso8601
import re as _re
import inspect as _inspect
import sys as _sys

# https://stackoverflow.com/a/1176023 - camelCase to snake_case
_RE_SNAKE_CASE = _re.compile(r'(?<!^)(?=[A-Z])')
def _snake_case(name: str) -> str:
	return _RE_SNAKE_CASE.sub('_', name).lower()

class APIError(Exception):
	"""
	Generic API error.
	"""
	def __init__(self, message: str, status_code: int, **data):
		self.message = message
		self.status_code = status_code
		self.__dict__.update({_snake_case(key): data[key] for key in data})

class AuthError(APIError):
	"""
	Generic authentication error.
	"""

class AdminLoggedIn(APIError):
	"""
	Admin already has an active session elsewhere.
	"""

class AdminLoggedOut(APIError):
	"""
	Admin has logged out.
	"""

class IncorrectResponse(APIError):
	"""
	Incorrect response was given for admin challenge-response login.
	"""

class UserLocked(APIError):
	"""
	User account is locked.
	"""
	def __init__(self, message: str, status_code: int, **data):
		super().__init__(message, status_code, **data)
		if 'lock_expiry' in self.__dict__:
			self.lock_expiry = _iso8601.parse_date(self.lock_expiry)

class SessionExpired(APIError):
	"""
	Session has expired.
	"""

class NotAuthorized(APIError):
	"""
	User or admin is not authorized to perform this action.
	"""

class NoObjectWithId(APIError):
	"""
	Object does not exist on the server.
	"""

class ObjectDeleted(APIError):
	"""
	Object is marked as deleted, action may not be executed on it.
	"""

class InvalidRequest(APIError):
	"""
	Request is invalid.
	"""

class NameTaken(APIError):
	"""
	User or board name is taken.
	"""

class NameInvalid(APIError):
	"""
	User or board name is not valid.
	"""

class PasswordInsecure(APIError):
	"""
	Password does not fulfill server requirements.
	"""

class AlreadyBlocked(APIError):
	"""
	You have already blocked this user.
	"""

class AlreadyFriends(APIError):
	"""
	You are already friends with this user.
	"""

class AlreadySent(APIError):
	"""
	You have already sent a friend request to this user.
	"""

class AlreadyAdded(APIError):
	"""
	User is already added to the board.
	"""

class NotFriends(APIError):
	"""
	You are not friends with this user.
	"""

def api_error(message: str, status_code: int, **data) -> APIError:
	"""
	Construct an APIError or one of its subclasses.
	"""
	
	for name, obj in _inspect.getmembers(_sys.modules[__name__], _inspect.isclass):
		if message == name and issubclass(obj, APIError):
			return obj(message, status_code, **data)
	
	return APIError(message, status_code, **data)
