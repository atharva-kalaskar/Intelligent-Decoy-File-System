# Operational Realities, Limitations, and Security Considerations

## 1. Operating System & Telemetry Realities

### 1.1 `ReadDirectoryChangesW` vs. Kernel Minifilters
- **Notification Scope:** The Win32 `ReadDirectoryChangesW` API reports directory metadata changes: file additions, removals, renames, size changes, attribute modifications, and last-write updates.
- **Read-Access Limitation:** Pure read operations (e.g. an application opening a file in read-only mode, scanning its bytes, and closing it without altering last-access timestamps) are **not** reliably reported by standard user-mode change notifications on NTFS/ReFS. The project strictly documents this constraint and does not invent artificial "read" telemetry.
- **Kernel Minifilter Comparison:** To capture pre-operation I/O request packets (`IRP_MJ_READ`, `IRP_MJ_CREATE`), a Windows File System Minifilter Driver (`FltRegisterFilter`) or Event Tracing for Windows (`Microsoft-Windows-Kernel-File` ETW provider) is required. These mechanisms require administrative elevation, kernel-mode code signing, and driver installation, which exceeds the safe user-mode constraints of an academic course assignment.

### 1.2 Process Attribution
- `ReadDirectoryChangesW` returns information regarding the *affected file path* and the *action*, but does **not** include the Process ID (`PID`), executable image path, or user security identifier (`SID`) that executed the operation.
- Consequently, behavioral windows aggregate file-system activity across the monitored folder rather than attributing actions to specific running binaries.

### 1.3 Buffer Overflows & Dropped Telemetry
- The C monitoring engine allocates a 64KB DWORD-aligned buffer for change notifications.
- Under extreme I/O bursts (e.g. tens of thousands of simultaneous disk operations), the Windows kernel notification buffer can experience an overflow (`ERROR_NOTIFY_ENUM_DIR`).
- The C watcher detects this error condition and emits an explicit diagnostic warning rather than treating missing events as evidence of safety.

---

## 2. Machine Learning & Dataset Constraints

### 2.1 Synthetic Scenario Boundaries
- The initial dataset was generated using controlled, deterministic behavioral simulations covering four distinct operational modes:
  1. Benign routine document work.
  2. Incidental single-decoy interaction.
  3. Multi-decoy reconnaissance.
  4. High-velocity burst tampering.
- **Metric Interpretation:** High evaluation scores (100% on the held-out test set) indicate that the 11 engineered features cleanly separate these defined scenarios in a controlled laboratory environment. They **must not** be interpreted as proof that the model will generalize perfectly to real-world advanced persistent threats (APTs) or bespoke ransomware strains.

### 2.2 Decoy Placement & Visibility Limitations
- **Tripwire Dependency:** Deception technology relies entirely on an adversary or automated malware scanning, traversing, or modifying files in the monitored path. If an attacker knows target paths in advance and accesses them directly without enumerating the directory, decoy canary tripwires will not be activated.
- **Adversarial Awareness:** If an adversary obtains access to `decoys/manifest.json` or detects canary string markers, they can intentionally filter out known decoy paths to evade detection.

---

## 3. Defensive Security Posture
- **Educational Prototype:** This application is engineered strictly as an educational proof-of-concept for university Network Security studies. It does not replace commercial Endpoint Detection and Response (EDR), Security Information and Event Management (SIEM), or antivirus systems.
- **Minimum Privilege:** Operates entirely within standard user privileges without requesting elevated administrative rights or modifying system security configurations.
- **Non-Destructive Guarantee:** Monitoring and decoy operations are strictly confined to the project directory (`runtime/monitored/`), with path traversal checks preventing interaction with any external user or system files.
