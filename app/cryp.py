import rsa

PUBLICKEY, PRIVATEKEY = rsa.newkeys(512)


def encrypt(message):
    return rsa.encrypt(message.encode(), PUBLICKEY)


def decrypt(encMessage):
    return rsa.decrypt(encMessage, PRIVATEKEY).decode()

