# Bug Report

## Title
Cold tier files are not promoted after recent access

## Description
According to requirements, recently accessed files should move back toward warmer tiers.
However, files in the COLD tier do not move up even after access.

## Steps to Reproduce
1. Upload file
2. Move file to COLD tier (90+ days)
3. Download the file
4. Run tiering API

## Expected Result
File should move from COLD → WARM

## Actual Result
File remains in COLD tier

## Impact
Violates expected data lifecycle behavior

## Severity
Medium