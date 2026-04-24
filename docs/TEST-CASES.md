# Cloud Storage Tiering System – Testcases

## Functional Testcases
## 1. File Upload API – "POST /files"

| TC ID | Test Scenario | Steps | Expected Result | Priority |
|-------|----------------|-------|----------------|----------|
| TC-001 | Upload valid eligible file | Upload file >1MB and <10GB | File uploads successfully, returns fileId, initial tier is HOT | High |
| TC-002 | Upload exactly 1MB file | Upload file exactly 1MB | Upload succeeds and file is eligible for tiering | High |
| TC-003 | Upload file exactly 10GB | Upload file exactly 10GB | Upload succeeds if upper limit inclusive | Medium |
| TC-004 | Upload file over 10GB | Upload file >10GB | Upload rejected with proper error | High | 
| TC-005 | Upload 0-byte file | Upload empty file | System rejects or marks as non-tierable | High |
| TC-005 | Upload malformed request | Send request without file payload | Return validation error | High | 
| TC-007 | Upload different content type | Send wrong content type | Return error message | Medium |
| TC-008 | Upload same file twice | Upload identical file twice | Each upload should generate unique fileId unless deduplication exists | Medium | 
| TC-009| Upload filename with special characters | Upload file with spaces/unicode/special chars in name | Upload succeeds and filename stored correctly | Medium | 
| TC-010| Upload different content type |  |  Upload succeeds | Medium | 

---

## 2. File Download API – "GET /files/{fileId}"

| TC ID  | Test Scenario | Steps | Expected Result | Priority |
|--------|----------------|-------|----------------|----------|
| TC-011 | Download existing file | Upload file then download it | Download succeeds and content matches original | High |
| TC-012 | Download invalid fileId | Use nonexistent fileId | Return 404 or appropriate error | High |
| TC-013 | Download updates last accessed time | Upload → Download → Fetch metadata | lastAccessed timestamp updates | High |
| TC-014 | Download file after tier transition | Move file to Warm/Cold then download | Download succeeds regardless of tier | High |


---

## 3. File Metadata API – "GET /files/{fileId}/metadata"

| TC ID  | Test Scenario | Steps | Expected Result | Priority |
|--------|----------------|-------|----------------|----------|
| TC-015 | Get metadata for valid file | Upload file then fetch metadata | Metadata contains fileId, filename, size, timestamps, tier | High |
| TC-016 | Metadata for invalid fileId | Use nonexistent fileId | Return 404 or appropriate error | High | 
| TC-017 | Metadata for deleted file | Upload → Delete → Metadata | Return not found error | High | 


---

## 4. File Delete API – "DELETE /files/{fileId}"

| TC ID  | Test Scenario | Steps | Expected Result | Priority |
|--------|----------------|-------|----------------|----------|
| TC-018 | Delete existing file | Upload file then delete it | Delete succeeds | High | 
| TC-019 | Delete invalid fileId | Use nonexistent fileId | Return 404 or appropriate error | High | 
| TC-020 | Delete already deleted file | Upload → Delete → Delete again | Return not found or idempotent success | Medium |
| TC-021 | Delete malformed fileId | Use blank or invalid fileId | Return validation error | Medium | 
| TC-022 | Delete updates stats | Upload → Delete → Stats | File count and storage usage decrease | High | 

---

## 5. Tiering API – "POST /admin/tiering/run"

| TC ID  | Test Scenario | Steps | Expected Result | Priority |
|--------|----------------|-------|----------------|----------|
| TC-023 | Move HOT file to WARM tier | Age file >30 days → Run tiering | File moves from HOT → WARM and files_moved ≥ 1 | High |
| TC-024 | Move WARM file to COLD tier | Age file >30 days → Run tiering → Age again >90 days → Run tiering | File moves from WARM → COLD | High |
| TC-025 | No movement for recent HOT file | Upload file → Run tiering without aging | File remains in HOT tier | High |
| TC-026 | Idempotent tiering execution | Age file → Run tiering twice | File remains in WARM after second run, no duplicate movement | High |
| TC-027 | Tiering processes multiple files | Upload multiple files → Age all → Run tiering | All eligible files move to WARM tier correctly | High |
| TC-028 | Validate tiering API response structure | Age file → Run tiering | Response contains status and files_moved with correct values | Medium |


---

## 6. Stats API – "GET /admin/stats"

| TC ID  | Test Scenario | Steps | Expected Result | Priority |
|--------|----------------|-------|----------------|----------|
| TC-029 | Validate stats response structure | Call stats API | Response contains total_files, total_size, tiers (HOT, WARM, COLD) with count and size | High |
| TC-030 | Stats on empty system | Call stats before any upload | All counts and total size are zero across all tiers | High |
| TC-031 | Stats after single upload | Upload one file then fetch stats | total_files = 1, total_size matches file size, HOT tier count = 1 | High |
| TC-032 | Stats after multiple uploads | Upload multiple files then fetch stats | total_files and total_size reflect sum of all uploads, all files in HOT tier | High |
| TC-033 | Stats after tier transition | Age file and run tiering, then fetch stats | File moves from HOT → WARM and stats reflect updated tier counts | High |
| TC-034 | Stats after delete | Upload → Delete → Fetch stats | total_files and total_size decrease to zero, all tier counts reset | High |

---

## 7. Special file Test Scenarios

| TC ID  | Test Scenario | Steps | Expected Result | Priority |
|--------|----------------|-------|----------------|----------|
| TC-035 | Priority file forces HOT tier | Create metadata with PRIORITY filename in WARM tier | File is forced to HOT tier | High |
| TC-036 | Priority rule is case-insensitive | Create metadata with lowercase priority filename in COLD tier | File is forced to HOT tier | High |
| TC-037 | Legal file stays WARM within 180 days | Create LEGAL file in WARM tier accessed within 180 days | File remains in WARM tier | High |
| TC-038 | Legal file stays WARM at 180-day boundary | Create LEGAL file in WARM tier accessed exactly 180 days ago | File remains in WARM tier | High |
| TC-039 | Legal file over 180 days has no special rule | Create LEGAL file in WARM tier accessed 181 days ago | No special rule is applied | Medium |
| TC-040 | Legal file in HOT has no special rule | Create LEGAL file already in HOT tier | No special rule is applied | Medium |
| TC-041 | Legal file in COLD has no special rule | Create LEGAL file already in COLD tier | No special rule is applied | Medium |
| TC-042 | Regular file has no special rule | Create normal file without special keywords | No special rule is applied | High |
| TC-043 | Priority rule overrides Legal rule | Create filename containing both LEGAL and PRIORITY | PRIORITY takes precedence and file is forced to HOT tier | High |



## Fault Injection Testcases
## 1. Concurrent Modification Test Scenarios

| TC ID  | Test Scenario | Steps | Expected Result | Priority |
|--------|----------------|-------|----------------|----------|
| TC-044 | Concurrent delete during download | Start file download → Remove file content before read completes | Download fails gracefully with HTTP 500 | High |
| TC-045 | Metadata corruption during tiering | Corrupt last_accessed while tiering job is running | Tiering API returns HTTP 500 due to invalid metadata state | High |

---

## 2. Corrupted Data Test Scenarios

| TC ID  | Test Scenario | Steps | Expected Result | Priority |
|--------|----------------|-------|----------------|----------|
| TC-046 | Corrupted last accessed type | Set last_accessed as non-datetime value → Run tiering | Tiering API returns HTTP 500 | High |
| TC-047 | Corrupted invalid tier value | Set file tier as invalid value → Run tiering | Tiering API returns HTTP 500 | High |
| TC-048 | Corrupted file size type | Set file size as string → Fetch admin stats | Stats API returns HTTP 500 | High |
| TC-049 | Missing metadata with existing content | Delete metadata but keep file content → Download file | API returns HTTP 404 with “File not found” | High |

---

## 3. Network Modification Test Scenarios

| TC ID  | Test Scenario | Steps | Expected Result | Priority |
|--------|----------------|-------|----------------|----------|
| TC-050 | Network failure during upload | Simulate client disconnect while reading upload body | Upload fails with HTTP 500 and no file is stored in metadata or content | High |
| TC-051 | Network timeout during upload | Simulate timeout while reading upload request body | Upload fails with HTTP 500 and no file is stored in metadata or content | High |


---

## 4. Storage Test Scenarios

| TC ID  | Test Scenario | Steps | Expected Result | Priority |
|--------|----------------|-------|----------------|----------|
| TC-052 | Storage read failure during download | Simulate disk read failure while fetching file content | Download API returns HTTP 500 | High |
| TC-053 | Storage write failure during upload | Simulate disk write failure while saving file content | Upload API returns HTTP 500 and metadata is created but content is not stored | High |
| TC-054 | Missing content with existing metadata | Remove file content but keep metadata → Download file | API returns HTTP 500 due to storage inconsistency | High |


## Performance Testcases
## 1. Performance Benchmark tests

| TC ID  | Test Scenario | Steps | Expected Result | Priority |
|--------|----------------|-------|----------------|----------|
| TC-088 | Tiering performance for 100 files | Upload 100 files in parallel → Mark as old → Run tiering | All files move to WARM tier within acceptable time (<30s) and no failures | High |
| TC-089 | Tiering upload throughput validation | Upload 100 files concurrently | System handles parallel uploads with stable throughput and no failures | High |
| TC-090 | Tiering execution time benchmark | Run tiering on 100 eligible files | Tiering completes within defined SLA and processes all files successfully | High |
| TC-091 | Tiering correctness under load | Upload and age multiple files → Run tiering | All files correctly transition to WARM tier without misses | High |
| TC-092 | Repeated tiering idempotency with performance | Run tiering twice on same file | Second run is faster and does not reprocess already tiered file | Medium |
| TC-093 | Tiering repeated run performance | Execute tiering again on already processed data | Execution completes quickly (<10s) with no unnecessary processing | Medium |
| TC-094 | Parallel tiering requests stability | Trigger multiple tiering requests concurrently | All requests succeed (200) and system remains stable | High |
| TC-095 | Tiering consistency under concurrent admin requests | Run multiple tiering jobs in parallel | No data inconsistency; all files correctly move to WARM | High |
| TC-096 | Concurrent tiering performance SLA | Execute parallel tiering requests | All requests complete within acceptable time (<20s) | Medium |

