# Internal-root transfer: verify the physical result

The R20 storage work exposed a useful verification lesson: a successful sparse-transfer command is not proof that the receiving storage contains every expected byte. This is a summary of one diagnosed transfer, **not a generic repair tool or installation procedure**.

## The bounded observation

The complete source used explicit zero-fill chunks rather than skipped regions and passed logical verification before transfer. Complete physical readback then found a mismatch in one MiB range of the initial 16 GiB filesystem. Three 4 KiB ext4 backup-metadata blocks were missing; the surrounding data matched. The source represented those blocks as a final RAW chunk between two non-overlapping fills.

A narrowly scoped correction was applied **before the first native read/write boot**. A second complete physical readback matched the source, with complete read counts verified. Only after that match was writable native boot allowed. This established the corrected transfer; it did not establish whether the client or bootloader caused the original omission.

## What can be reused

1. Validate the logical source, chunk boundaries, payload and total size.
2. Verify the complete physical receiving range, including zero-filled and filesystem metadata regions. Do not substitute an exit code or selected samples for full readback.
3. Treat a mismatch as an unresolved transfer until a narrowly justified correction and complete re-verification pass. Record scope and uncertainty without assigning an unproven cause.
4. Distinguish a **pre-first-write source image** from a filesystem that has already run. After a writable boot, legitimate metadata/data changes make replaying an old repair fragment unsafe.

Skipped ranges were permitted only in that diagnosed, fixed correction to preserve already-verified regions. They are not accepted as proof that a full initial image was written. No fragment, filesystem metadata, device-specific manifest, source/image verification hash or receiving-unit identity is distributed here; those artifacts can contain filesystem identity even when they contain no user files.

The public repository does not include the private provisioning or correction procedure. This note does not supply a flash command, offsets to replay on another device or permission to erase storage. [R20 acceptance boundaries](validation-2026-11-02.md) · [compatibility requirements](compatibility.md).
