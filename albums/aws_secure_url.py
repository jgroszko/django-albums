import hashlib
import base64
import time
from M2Crypto import RSA

from django.conf import settings

def policy_urlsafe(policy):
    safe = ['+-', '=_', '/~']
    data = base64.b64encode(policy)
    for s, r in safe:
        data = data.replace(s, r)
    return data

def policy_sign(policy):
    rsa_key = RSA.load_key_string(settings.ALBUMS_AMAZON_PRIVATE_KEY)

    return policy_urlsafe(
        rsa_key.sign(
            hashlib.sha1(policy).digest(), 'sha1'
            )
        )

def policy(resource, expires, host=None):
    return """{ 
  "Statement": [{ 
    "Resource":"%s", 
      "Condition":{ 
        "DateLessThan":{"AWS:EpochTime":%s}%s      
    } 
  }] 
}
""" % (resource,
       expires,
       "" if host is None else """,
        "IpAddress":{"AWS:SourceIp":"%s/32"}""" % host)

def secure_url(resource, expires_in=60*60, host=None):
    expires = int(time.time() + expires_in)
    str_policy = policy(resource, expires, host)

    safe_policy = policy_urlsafe(str_policy)
    signature = policy_sign(str_policy)

    return "%s?Policy=%s%sSignature=%s%sKey-Pair-Id=%s" % (resource, 
                                            safe_policy,
                                            "%26",
                                            signature,
                                            "%26",
                                            settings.ALBUMS_AMAZON_PRIVATE_KEY_ID)  
