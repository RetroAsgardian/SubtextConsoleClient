#!/usr/bin/env python3
"""
subtext.content
"""
import hashlib
import struct

from uuid import UUID

from typing import Optional

class Content:
	"""
	Represents message content.
	"""
	def __init__(self):
		pass
	def from_bytes(self, data: bytes):
		"""
		Deserialize content from raw bytes.
		"""
		raise NotImplementedError()
	def to_bytes(self) -> bytes:
		"""
		Serialize content to raw bytes.
		"""
		raise NotImplementedError()
	def canon_type(self) -> Optional[str]:
		"""
		Get the canonical message type for this content.
		"""
		return None

class FallbackContent(Content):
	"""
	Fallback content type, used if no other suitable type is found.
	"""
	def __init__(self, *, data: Optional[bytes] = None):
		self.data = data
	def from_bytes(self, data: bytes):
		self.data = data
	def to_bytes(self) -> bytes:
		return self.data

class TextContent(Content):
	"""
	Text encoded in UTF-8 format.
	"""
	def __init__(self, *, text: Optional[str] = None):
		self.text = text
	def from_bytes(self, data: bytes):
		self.text = data.decode('utf-8')
	def to_bytes(self) -> bytes:
		return self.text.encode('utf-8')
	def canon_type(self) -> Optional[str]:
		return "TextMessage"

class FileContent(Content):
	"""
	Simple file container.
	"""
	def __init__(self, *, name: Optional[str] = None, type: Optional[str] = None, data: Optional[bytes] = None):
		self.name = name
		self.type = type
		self.data = data
	def to_bytes(self) -> bytes:
		header = bytearray()
		
		# Name
		header.extend(self.name.encode('utf-8'))
		header.append(0x00)
		
		# Type
		header.extend(self.type.encode('utf-8'))
		header.append(0x00)
		
		# Size
		header.extend(struct.pack('>i', len(self.data)))
		
		# Hash
		sha256 = hashlib.sha256()
		sha256.update(self.data)
		header.extend(sha256.digest())
		
		# Data offset, header, data
		return struct.pack('>i', len(header) + 4) + header + self.data
	def from_bytes(self, data: bytes):
		(data_offset,) = struct.unpack('>i', data[:4])
		print("data_offset: 0x{:08x}".format(data_offset))
		
		self.data = data[data_offset:]
		
		header = bytearray(data[4:data_offset])
		
		name_bytes = bytearray()
		while True:
			x = header.pop(0)
			if x == 0x00:
				break
			name_bytes.append(x)
		self.name = name_bytes.decode('utf-8')
		
		type_bytes = bytearray()
		while True:
			x = header.pop(0)
			if x == 0x00:
				break
			type_bytes.append(x)
		self.type = type_bytes.decode('utf-8')
		
		(size, ) = struct.unpack('>i', header[:4])
		if size != len(self.data):
			raise ValueError("Size mismatch")
		
		digest = bytes(header[4:])
		sha256 = hashlib.sha256()
		sha256.update(self.data)
		if sha256.digest() != digest:
			raise ValueError("Hash mismatch")
	def canon_type(self) -> Optional[str]:
		return "FileMessage"

class MemberContent(Content):
	"""
	Indicates that a member has been added or removed.
	"""
	def __init__(self, *, user_id: Optional[UUID] = None):
		self.user_id = user_id
	def to_bytes(self) -> bytes:
		return str(self.user_id).encode('utf-8')
	def from_bytes(self, data: bytes):
		self.user_id = UUID(data.decode('utf-8'))

def parse_content(type: str, data: bytes) -> Content:
	"""
	Convert message data into a Content object based on the given type.
	"""
	if type == "Message" or type == "TextMessage":
		content = TextContent()
	elif type == "FileMessage":
		content = FileContent()
	elif type == "AddMember" or type == "RemoveMember":
		content = MemberContent()
	else:
		content = FallbackContent()
	
	content.from_bytes(data)
	return content
