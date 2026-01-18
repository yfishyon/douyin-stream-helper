# coding=UTF-8
import os
import sys
import datetime
import subprocess
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PrivateFormat,
    NoEncryption,
)


class certmgr:
    def is_certificate_expired(self, cert_path):
        if not os.path.exists(cert_path):
            return True
        try:
            with open(cert_path, "rb") as f:
                cert = x509.load_pem_x509_certificate(f.read())
            return datetime.datetime.now(datetime.timezone.utc) > cert.not_valid_after_utc
        except Exception:
            return True

    def generate_private_key(self, bits):
        return rsa.generate_private_key(public_exponent=65537, key_size=bits)

    def load_private_key(self, data):
        from cryptography.hazmat.primitives import serialization
        return serialization.load_pem_private_key(data, password=None)

    def generate_ca(self, privatekey):
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Los Angeles"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Douyin Stream Helper CA"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Douyin Stream Helper CA"),
            x509.NameAttribute(NameOID.COMMON_NAME, "Douyin Stream Helper CA"),
        ])
        return (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(privatekey.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=3))
            .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=360))
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .sign(privatekey, hashes.SHA256())
        )

    def generate_cert(self, hostnames, privatekey, ca_cert, ca_key):
        names = [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Los Angeles"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Douyin Stream Helper"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Douyin Stream Helper"),
            x509.NameAttribute(NameOID.COMMON_NAME, hostnames[0]),
        ]

        csr = (
            x509.CertificateSigningRequestBuilder()
            .subject_name(x509.Name(names))
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName(i) for i in hostnames]),
                critical=False,
            )
            .sign(privatekey, hashes.SHA256())
        )

        return (
            x509.CertificateBuilder()
            .subject_name(csr.subject)
            .issuer_name(ca_cert.subject)
            .public_key(csr.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(
                datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=3)
            )
            .not_valid_after(
                datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=360)
            )
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName(i) for i in hostnames]),
                critical=False,
            )
            .sign(ca_key, hashes.SHA256())
        )

    def import_to_root(self, cert_path):
        try:
            subprocess.check_call(
                ["certutil", "-addstore", "Root", cert_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False

    def export_key(self, path, key):
        with open(path, "wb") as f:
            f.write(
                key.private_bytes(
                    Encoding.PEM,
                    PrivateFormat.TraditionalOpenSSL,
                    NoEncryption(),
                )
            )

    def export_cert(self, path, cert):
        with open(path, "wb") as f:
            f.write(cert.public_bytes(Encoding.PEM))
