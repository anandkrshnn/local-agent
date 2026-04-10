#!/usr/bin/env python3
"""
Master QA Orchestration Script
Runs all 4 phases and generates comprehensive report
"""

import subprocess
import sys
import time
import json
from datetime import datetime
from pathlib import Path

def run_phase(phase_name: str, script_path: str, args: list = None) -> dict:
    """Run a single QA phase and return results"""
    print(f"\n{'='*60}")
    print(f"Starting {phase_name}")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=300)
        duration = time.time() - start_time
        
        return {
            "phase": phase_name,
            "success": result.returncode == 0,
            "duration_seconds": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "phase": phase_name,
            "success": False,
            "duration_seconds": 300,
            "error": "Timeout exceeded"
        }
    except Exception as e:
        return {
            "phase": phase_name,
            "success": False,
            "error": str(e)
        }

def generate_report(results: list):
    """Generate QA report"""
    print("\n" + "="*60)
    print("📊 QA MASTER REPORT")
    print("="*60)
    print(f"Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-"*40)
    
    all_passed = True
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"\n{result['phase']}: {status}")
        if "duration_seconds" in result:
            print(f"  Duration: {result['duration_seconds']:.2f}s")
        if result.get("error"):
            print(f"  Error: {result['error']}")
        if not result["success"]:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL QA PHASES PASSED - PRODUCTION READY!")
    else:
        print("⚠️ SOME QA PHASES FAILED - Review issues above")
    print("="*60)
    
    return all_passed

def main():
    phases = [
        ("Phase 1: Database Stress", "qa_database_stress.py"),
        ("Phase 2: Ollama Load", "qa_ollama_load.py"),
        ("Phase 3: Chaos Testing", "qa_edge_cases.py"),
    ]
    
    results = []
    
    for phase_name, script in phases:
        script_path = Path(__file__).parent / script
        if not script_path.exists():
            print(f"⚠️ Script not found: {script}")
            continue
        
        result = run_phase(phase_name, str(script_path))
        results.append(result)
        
        # Output sub-phase details to visually simulate the run
        print(result.get("stdout", ""))
        
        # Brief pause between phases
        time.sleep(2)
    
    all_passed = generate_report(results)
    
    # Phase 4 is PowerShell script
    print("\n" + "="*60)
    print("Starting Phase 4: Desktop Builder")
    print("="*60)
    
    ps_result = subprocess.run(
        ["powershell.exe", "-File", "qa_desktop_builder.ps1", "-CleanOnly"],
        capture_output=True,
        text=True
    )
    
    phase4_passed = ps_result.returncode == 0
    results.append({
        "phase": "Phase 4: Desktop Builder",
        "success": phase4_passed,
        "stdout": ps_result.stdout,
        "stderr": ps_result.stderr
    })
    
    print(ps_result.stdout)
    
    generate_report(results)
    
    return 0 if all_passed and phase4_passed else 1

if __name__ == "__main__":
    sys.exit(main())
