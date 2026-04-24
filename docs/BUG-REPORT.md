# Bug Report

## Title
COLD tier files are not promoted after recent access

---

## Description
According to the expected storage behavior, recently accessed files should move back toward warmer tiers (COLD → WARM → HOT).  

However, in the current implementation, files in the **COLD** tier remain in COLD even after being accessed and after executing the tiering process.

---

## Steps to Reproduce

1. Upload a valid file (>1MB)
2. Set file last accessed to 31 days ago  
   → Run tiering → File moves from HOT → WARM  
3. Set file last accessed to 91 days ago  
   → Run tiering → File moves from WARM → COLD  
4. Download the file (simulates recent access)
5. Run tiering again
6. Fetch file metadata

---

## Expected Result

After recent access and tiering execution , The tier should change to WARM from COLD, But it stays as COLD

`

## Steps to Reproduce through Automated test```bash

```bash
pytest tests/functional/Bug_test.py::test_cold_file_should_promote_to_warm_after_recent_access -v 


