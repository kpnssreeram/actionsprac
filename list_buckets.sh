#!/bin/bash

# List all S3 buckets

aws s3 ls | awk '{print $3}'