import subprocess

def main():
    scripts = [
        "run_baby_suit.py",
        "run_handbag.py",
        "run_skincare.py",
        "run_shoes.py",
        "run_lawn_suit.py"
    ]
    
    print("=== STARTING BATCH EXECUTION OF ALL 5 ISOLATED CATEGORIES ===")
    for script in scripts:
        print(f"\n--- Running {script} ---")
        result = subprocess.run(["python", script])
        if result.returncode != 0:
            print(f"Error executing {script}")
        else:
            print(f"Finished {script} successfully.")

if __name__ == "__main__":
    main()
