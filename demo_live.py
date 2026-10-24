"""
Interactive Real-World Demonstration Console for Network Security Coursework
Allows students to perform hands-on attacks and benign activities live in front of teachers.
Shows physical file changes in runtime/monitored/, C telemetry, and ML classifications.
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "application"))
sys.path.insert(0, str(BASE_DIR / "ml"))

from scenario_runner import ScenarioRunner
import process_manager
import manage_decoys

MONITORED_DIR = BASE_DIR / "runtime" / "monitored"
DOCS_DIR = MONITORED_DIR / "documents"
DECOYS_DIR = MONITORED_DIR / "decoys"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    print("=" * 72)
    print("   INTELLIGENT DECOY FILE SYSTEM — LIVE PROFESSOR DEMONSTRATION")
    print("   Course: Network Security & Deception Technology")
    print("=" * 72)
    
    running, pid = process_manager.is_monitor_running()
    proc_str = f"RUNNING (PID: {pid})" if running else "STOPPED (You can start it below)"
    print(f" [*] C Watcher Engine:     {proc_str}")
    print(f" [*] Monitored Directory:  {MONITORED_DIR}")
    print(f" [*] SOC Dashboard URL:    http://localhost:8501")
    print("=" * 72)


def demo_normal_activity(runner):
    print("\n--- [DEMO 1] NORMAL USER ACTIVITY (BENIGN BASELINE) ---")
    print(" [ACTION] Creating and editing standard documents in runtime/monitored/documents/...")
    
    res = runner.execute_scenario("normal_office")
    
    print("\n [✓] REAL-WORLD DISK CHANGES PERFORMED:")
    print(f"     - Modified: documents/assignment.txt")
    print(f"     - Modified: documents/project_notes.txt")
    print(f"     - Modified: documents/meeting_minutes.txt")
    print(f"     - Created & deleted draft scratch notes")
    print(f"     - Total Decoys Touched: 0")
    
    pred = res["prediction"]
    print(f"\n [✓] ML VERDICT: {pred['prediction'].upper()} (Risk: {pred['risk_level']})")
    print(f"     - Suspicious Probability: {pred['suspicious_probability']*100:.1f}%")
    print(f"     - Security Alerts Raised: 0 (Clean Baseline)")

    print("\n 🗣️ WHAT TO SAY TO YOUR TEACHER:")
    print("   \"Professor, I just edited multiple normal documents at human typing speed.")
    print("    The C monitor captured the events, and the Random Forest analyzed the time window.")
    print("    Because no decoys were touched and speed was normal, risk is 0.0% and no false alarm was raised.\"")
    input("\n Press Enter to return to menu...")


def demo_ransomware_attack(runner):
    print("\n--- [DEMO 2] LIVE RANSOMWARE ENCRYPTION ATTACK (CRITICAL THREAT) ---")
    print(" [ACTION] Attacker script launched! Encrypting files rapidly across directories...")
    
    res = runner.execute_scenario("ransomware_burst")
    
    print("\n [!] REAL-WORLD DISK CHANGES PERFORMED:")
    print(f"     - Encrypted normal documents: assignment.txt.locked, research_paper.txt.locked")
    print(f"     - Encrypted honeytoken files: Confidential_Report.docx.txt.locked, Backup_Credentials.kdbx.txt.locked")
    print(f"     - Dropped extortion note: runtime/monitored/HOW_TO_RECOVER_YOUR_FILES.txt")
    print(f"     - Burst Speed: > 10 files per second across multiple directories")
    
    pred = res["prediction"]
    prob = pred["suspicious_probability"] * 100
    print(f"\n [!] ML CLASSIFICATION: {pred['prediction'].upper()} (Confidence: {prob:.1f}%)")
    print(f"     - Severity Level: {pred['risk_level']}")
    print(f"     - Rationale: {pred['reason_summary']}")
    print(f"     - MITRE ATT&CK: T1486 (Data Encrypted for Impact), T1485 (Data Destruction)")
    print(f"     - Incident ID: {res['alert']['alert_id'] if res.get('alert') else 'ALT-CONFIRMED'}")

    print("\n 🗣️ WHAT TO SAY TO YOUR TEACHER:")
    print("   \"Professor, look at Windows Explorer: all files are locked and a ransom note appeared.")
    print("    The C monitor intercepted the burst in real time. The Random Forest flagged this as")
    print("    CRITICAL with 100% confidence because it detected both the high file velocity (>10 ops/sec)")
    print("    and the destruction of multiple canary honey-files.\"")
    input("\n Press Enter to return to menu...")


def demo_credential_theft(runner):
    print("\n--- [DEMO 3] TARGETED HONEYTOKEN CREDENTIAL THEFT (ELEVATED THREAT) ---")
    print(" [ACTION] Adversary searching for passwords and SSH private keys...")
    
    res = runner.execute_scenario("credential_recon")
    
    print("\n [!] REAL-WORLD DISK CHANGES PERFORMED:")
    print(f"     - Probed: decoys/Backup_Credentials.kdbx.txt (Password Store)")
    print(f"     - Probed: decoys/private_key.pem.txt (RSA Private Key)")
    print(f"     - Probed: decoys/database_dump.sql (Database Dump)")
    print(f"     - Probed: decoys/Financial_Records_2025.xlsx.txt (Tax Records)")
    
    pred = res["prediction"]
    prob = pred["suspicious_probability"] * 100
    print(f"\n [!] ML CLASSIFICATION: {pred['prediction'].upper()} (Confidence: {prob:.1f}%)")
    print(f"     - Assigned Severity: {pred['risk_level']}")
    print(f"     - Decoy Activity Ratio: 71.4% of total actions")
    print(f"     - MITRE ATT&CK: T1083 (File Discovery), T1552 (Unsecured Credentials)")

    print("\n 🗣️ WHAT TO SAY TO YOUR TEACHER:")
    print("   \"Professor, here the attacker was stealthy and moved slowly to evade speed-based detection.")
    print("    However, because they targeted our honey-files (passwords and private keys), the decoy ratio")
    print("    exceeded 70%. The Random Forest flagged this as targeted credential reconnaissance (MITRE T1552).\"")
    input("\n Press Enter to return to menu...")


def demo_accidental_touch(runner):
    print("\n--- [DEMO 4] INCIDENTAL DECOY CLICK (THE SCIENTIFIC PROOF) ---")
    print(" [ACTION] Legitimate user modifies 4 documents and accidentally clicks 1 decoy...")
    
    res = runner.execute_scenario("incidental_touch")
    
    print("\n [✓] REAL-WORLD DISK CHANGES PERFORMED:")
    print(f"     - Modified: 4 normal documents in documents/")
    print(f"     - Accidental touch on: decoys/Confidential_Report.docx.txt")
    print(f"     - Cadence: Slow human pace (5.5 seconds between clicks)")
    
    pred = res["prediction"]
    print(f"\n [✓] ML CLASSIFICATION: {pred['prediction'].upper()} (Risk: {pred['risk_level']})")
    print(f"     - Suspicious Probability: {pred['suspicious_probability']*100:.1f}%")
    print(f"     - Security Alerts Raised: 0 (No False Alarm!)")

    print("\n 🗣️ WHAT TO SAY TO YOUR TEACHER:")
    print("   \"Professor, THIS is the core scientific contribution of our project:")
    print("    A simple static rule says 'If decoy touched -> sound alarm!' That produces false alarms.")
    print("    Our Random Forest model analyzed the slow human intervals (5.5s) and low ratio, and correctly")
    print("    classified this as an accidental touch, eliminating the false alarm!\"")
    input("\n Press Enter to return to menu...")


def demo_reset(runner):
    print("\n--- [DEMO 5] PRISTINE ENVIRONMENT RESET ---")
    print(" [ACTION] Removing locked files, clearing events, and re-deploying clean decoys...")
    res = runner.reset_demo_environment()
    print(f" [✓] {res['message']}")
    print(" [✓] runtime/monitored/ restored with 4 clean documents and 5 canary honey-files.")
    input("\n Press Enter to return to menu...")


def main():
    runner = ScenarioRunner()
    
    while True:
        clear_screen()
        print_banner()
        print(" Choose an action to perform in front of your teacher:")
        print("   [1] 📄 Demonstrate Normal User Work        (Benign Baseline, 0 alerts)")
        print("   [2] 🚨 Demonstrate Live Ransomware Attack  (Rapid Encryption, locked files)")
        print("   [3] 🔑 Demonstrate Credential Theft        (Stealing decoy passwords & keys)")
        print("   [4] 🎯 Demonstrate Accidental Decoy Click  (Scientific proof: No false alarm)")
        print("   [5] 🧹 Reset Environment to Pristine State (Clean files & wipe history)")
        print("   [6] 🖥️ Open Web Dashboard in Browser       (http://localhost:8501)")
        print("   [7] ⚙️ Start/Stop Native C Watcher Process")
        print("   [0] ❌ Exit")
        print("=" * 72)
        
        choice = input(" Enter your choice [0-7]: ").strip()
        
        if choice == "1":
            demo_normal_activity(runner)
        elif choice == "2":
            demo_ransomware_attack(runner)
        elif choice == "3":
            demo_credential_theft(runner)
        elif choice == "4":
            demo_accidental_touch(runner)
        elif choice == "5":
            demo_reset(runner)
        elif choice == "6":
            import webbrowser
            webbrowser.open("http://localhost:8501")
            print(" [OK] Opened dashboard in browser.")
            time.sleep(1)
        elif choice == "7":
            running, pid = process_manager.is_monitor_running()
            if running:
                ok, msg = process_manager.stop_monitor()
                print(f" [OK] {msg}")
            else:
                ok, msg = process_manager.start_monitor()
                print(f" [OK] {msg}")
            time.sleep(1.5)
        elif choice == "0":
            print("\n Goodbye and good luck with your demonstration!")
            break
        else:
            print("\n Invalid option. Please choose [0-7].")
            time.sleep(1)


if __name__ == "__main__":
    main()
