"""Publish only the tested Glue script. Never starts a job or changes IAM."""
import argparse
import hashlib
from pathlib import Path


def deploy(client, source, bucket, key, commit):
    content = Path(source).read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    client.put_object(
        Bucket=bucket, Key=key, Body=content, ContentType="text/x-python",
        ServerSideEncryption="AES256",
        Metadata={"sha256": digest, "git-commit": commit},
    )
    # Read back actual bytes; metadata alone would not prove content integrity.
    response = client.get_object(Bucket=bucket, Key=key)
    try:
        actual = hashlib.sha256(response["Body"].read()).hexdigest()
    finally:
        response["Body"].close()
    if actual != digest:
        raise RuntimeError("Deployed script checksum does not match; deployment verification failed")
    print("Verified Glue script SHA256: " + digest)
    return digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--key", default="scripts/germany-energy-cloud-pipeline.py")
    parser.add_argument("--region", default="eu-central-1")
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    import boto3
    deploy(boto3.client("s3", region_name=args.region),
           Path(__file__).resolve().parents[1] / "cloud/glue_energy_pipeline.py",
           args.bucket, args.key, args.commit)


if __name__ == "__main__":
    main()
