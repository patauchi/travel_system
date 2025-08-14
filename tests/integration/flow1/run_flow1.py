#!/usr/bin/env python3
"""
Simple runner for Flow 1 integration test
Executes the test directly without pytest
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import the test
from test_flow1 import TestFlow1

async def main():
    """Run Flow 1 test"""
    print("\n" + "="*70)
    print(" INTEGRATION TEST RUNNER - FLOW 1")
    print("="*70)
    print("\nThis test will:")
    print("1. Login with the existing super_admin")
    print("2. Verify super_admin uniqueness")
    print("3. Create a new tenant using /api/v1/tenants/v2")
    print("\n" + "="*70)

    try:
        # Create test instance
        test = TestFlow1()

        # Run the test
        await test.test_flow_1_super_admin_and_tenant_creation()

        print("\n✅ TEST PASSED: Flow 1 completed successfully!")
        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        return 1

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    # Run the async main function
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
