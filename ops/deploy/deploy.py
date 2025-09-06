#!/usr/bin/env python3
import subprocess
import sys
import os

def run_command(cmd, description):
    print(f"\n{description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    print(result.stdout)

def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else "dev"
    
    print(f"Deploying to {stage} environment...")
    
    # Install dependencies
    run_command("pip install -r requirements.txt", "Installing dependencies")
    
    # Copy shared modules to services
    run_command("cp -r shared services/api/", "Copying shared modules to API")
    
    # Deploy CDK stacks
    run_command(f"cdk deploy --all --require-approval never -c stage={stage}", f"Deploying CDK stacks to {stage}")
    
    print(f"\n✓ Deployment to {stage} completed!")
    print(f"Run smoke tests: python ops/smoke/test_health.py")

if __name__ == "__main__":
    main()
