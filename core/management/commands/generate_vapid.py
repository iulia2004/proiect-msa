import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.core.management.base import BaseCommand


def b64(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


class Command(BaseCommand):
    help = "Generate VAPID keys for Web Push"

    def handle(self, *args, **opts):
        key = ec.generate_private_key(ec.SECP256R1())
        priv = key.private_numbers().private_value.to_bytes(32, "big")
        pub = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
        self.stdout.write("\nPaste these two lines into your .env file:\n")
        self.stdout.write(f"VAPID_PUBLIC_KEY={b64(pub)}")
        self.stdout.write(f"VAPID_PRIVATE_KEY={b64(priv)}\n")
