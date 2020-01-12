#!/usr/bin/env python3
"""
subtext.encryption
"""
import gnupg, subprocess

from .user import User

from typing import Optional, List, Tuple, Union

class Encryption:
	"""
	Provides encryption functionality for Subtext.
	"""
	def __init__(self, my_key: Optional[Union[User, str]] = None, *, gpg_dir: Optional[str] = None):
		self.gpg = gnupg.GPG(use_agent=True, gnupghome=gpg_dir)
		self.gpg.encoding = 'utf-8'
		
		self.my_key = None
		if my_key is not None:
			self.change_my_key(my_key)
	
	def gen_key(self, user: User, *, expire_years: int = 5) -> str:
		"""
		Generate a key for use with Subtext.
		"""
		name, email = self.get_user_key_uid(user)
		
		key = self.gpg.gen_key(self.gpg.gen_key_input(
			# RSA-2048 for signing and RSA-3072 for encryption
			# provides good security while reducing message size
			key_type='RSA',
			key_length=2048,
			key_usage='sign',
			subkey_type='RSA',
			subkey_length=3072,
			subkey_usage='encrypt',
			
			name_real=name,
			name_comment='Subtext',
			name_email=email,
			expire_date=(0 if expire_years <= 0 else "{}y".format(expire_years)),
		))
		
		return key.fingerprint
	
	def change_my_key(self, my_key: Union[User, str]):
		"""
		Change the key used for signing and decryption.
		If a User is given, GnuPG will automatically select the best key for that user.
		"""
		if isinstance(my_key, User):
			self.my_key = self.get_user_key_uid(my_key)[1]
		else:
			self.my_key = my_key
	
	def get_user_key_uid(self, user: User) -> Tuple[str, str]:
		"""
		Return key "name" and "email" for the given user.
		"""
		if user.name is None:
			user.refresh()
		
		return (
			'{}@{}'.format(user.name, user.ctx.instance_name),
			'{}@{}'.format(user.id, user.ctx.instance_id)
		)
	
	def get_user_keys(self, user: User) -> List[str]:
		"""
		Return a list of key fingerprints for the given user, sorted with most recent key first.
		"""
		name, email = self.get_user_key_uid(user)
		keys = self.gpg.list_keys(keys=[name, email])
		
		keys.sort(key=(lambda key: (
			0 if key['trust'] == 'u' else 1 if key['trust'] == 'f' else 2 if key['trust'] == 'm' else 3,
			-int(key['date'])
		)))
		
		return [key['fingerprint'] for key in keys]
	
	def get_key_info(self, key_fp: str):
		"""
		Get information about the given key.
		"""
		keys = self.gpg.list_keys(keys=key_fp)
		return keys[0]
	
	def sign_key(self, key_fp: str):
		"""
		Sign the key. You should ONLY do this after verifying that it belongs to the correct person.
		To verify a key, contact the owner in person or over the phone, and compare the key's fingerprint
		to the owner's copy's fingerprint.
		"""
		subprocess.run(['gpg', '--batch', '--yes', '-u', self.my_key, '--sign-key', key_fp], check=False)
	
	def trust_key_owner(self, key_fp: str, *, untrust: bool = False, full_trust: bool = False):
		"""
		Set the key's owner's trust level. This represents how much you trust them to correctly verify
		other keys before signing them.
		
		Without any additional parameters, the owner will be given marginal trust. Three signatures from
		marginally trusted users will validate a key. This is a good choice for most of your friends.
		
		If untrust is set to True, the owner will have all trust removed. This should be used for people
		who have a habit of signing keys without verifying them first, or for people you don't know.
		
		If full_trust is set to True, the owner will be given full trust. One signature from a fully
		trusted user will validate a key, so assign this level of trust with care.
		"""
		if not untrust and not full_trust:
			self.gpg.trust_keys([key_fp], 'TRUST_MARGINAL')
		elif untrust:
			self.gpg.trust_keys([key_fp], 'TRUST_NEVER')
		elif full_trust:
			self.gpg.trust_keys([key_fp], 'TRUST_FULL')
	
	def export_keys(self, keys: List[Union[User, str]]) -> bytes:
		"""
		Export keys in binary format.
		"""
		key_ids = []
		for x in keys:
			if isinstance(x, User):
				key_ids.append(self.get_user_key_uid(x)[1])
			else:
				key_ids.append(x)
		return self.gpg.export_keys(key_ids, armor=False)
	
	def export_secret_keys(self, keys: List[Union[User, str]]) -> bytes:
		"""
		Export secret keys in binary format.
		"""
		key_ids = []
		for x in keys:
			if isinstance(x, User):
				key_ids.append(self.get_user_key_uid(x)[1])
			else:
				key_ids.append(x)
		return self.gpg.export_keys(key_ids, True, armor=False, expect_passphrase=False)
	
	def import_keys(self, key_data: bytes):
		"""
		Import key data.
		"""
		self.gpg.import_keys(key_data)
	
	def encrypt(self,
		data: bytes,
		recipients: List[Union[User, str]],
		*,
		compress: bool = False
	) -> bytes:
		"""
		Encrypt and sign some data.
		"""
		recipient_keys = []
		for x in recipients:
			if isinstance(x, User):
				recipient_keys.append(self.get_user_key_uid(x)[1])
			else:
				recipient_keys.append(x)
		
		crypt = self.gpg.encrypt(
			data,
			recipient_keys,
			sign=self.my_key,
			always_trust=True,
			armor=False,
			extra_args=(['-z', '0'] if not compress else None)
		)
		return crypt.data
	
	def decrypt(self,
		data: bytes
	) -> Tuple[bytes, bool]:
		"""
		Decrypt and verify some data.
		"""
		crypt = self.gpg.decrypt(data)
		return (crypt.data, crypt.trust_level is not None and crypt.trust_level >= crypt.TRUST_FULLY)
