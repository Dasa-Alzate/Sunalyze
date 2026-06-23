"""Adaptador de almacenamiento compatible S3/MinIO (opcional).

`boto3` se importa de forma **perezosa** dentro de los métodos para que la app y los tests
arranquen sin la dependencia instalada cuando el backend activo es local. La `ref` es la clave
del objeto (`<prefix>/<org_id>/<key>`), que se guarda en `GeneratedDocument.pdf_path`.
"""

from app.gateways.storage.base import StorageGateway, StorageError


class S3Storage(StorageGateway):
    """Persiste los PDF como objetos en un bucket S3/MinIO."""

    def __init__(self, bucket, prefix='generated', endpoint_url=None, region=None,
                 access_key=None, secret_key=None, url_expires=3600):
        if not bucket:
            raise StorageError('STORAGE_BACKEND=s3 requiere S3_BUCKET.')
        self.bucket = bucket
        self.prefix = (prefix or '').strip('/')
        self.endpoint_url = endpoint_url
        self.region = region
        self.access_key = access_key
        self.secret_key = secret_key
        self.url_expires = url_expires

    @classmethod
    def from_config(cls, config):
        return cls(
            bucket=config.get('S3_BUCKET'),
            prefix=config.get('S3_PREFIX', 'generated'),
            endpoint_url=config.get('S3_ENDPOINT_URL'),
            region=config.get('S3_REGION'),
            access_key=config.get('S3_ACCESS_KEY_ID'),
            secret_key=config.get('S3_SECRET_ACCESS_KEY'),
            url_expires=config.get('S3_URL_EXPIRES', 3600),
        )

    def _client(self):
        import boto3

        return boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

    def _object_key(self, org_id, key):
        parts = [p for p in (self.prefix, str(org_id), key) if p]
        return '/'.join(parts)

    def save(self, org_id, key, data):
        object_key = self._object_key(org_id, key)
        self._client().put_object(
            Bucket=self.bucket, Key=object_key, Body=data,
            ContentType='application/pdf',
        )
        return object_key

    def read(self, ref):
        from botocore.exceptions import ClientError

        try:
            response = self._client().get_object(Bucket=self.bucket, Key=ref)
        except ClientError as exc:
            code = exc.response.get('Error', {}).get('Code')
            if code in ('NoSuchKey', '404', 'NotFound'):
                raise FileNotFoundError(ref) from exc
            raise StorageError(str(exc)) from exc
        return response['Body'].read()

    def exists(self, ref):
        from botocore.exceptions import ClientError

        try:
            self._client().head_object(Bucket=self.bucket, Key=ref)
            return True
        except ClientError:
            return False

    def url(self, ref):
        return self._client().generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': ref},
            ExpiresIn=self.url_expires,
        )
