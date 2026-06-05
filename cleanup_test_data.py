"""
⚠️  DEPRECATED - Use cleanup_all_duplicates.py instead

This script was a nuclear option that deleted all test data indiscriminately.
The new comprehensive cleanup script is much smarter:

    python cleanup_all_duplicates.py

That script handles:
- Duplicate emails (intelligently keeps the most active/recent user)
- Orphaned staff profiles  
- Orphaned tasks and activities
- Detailed reporting

This old script just deleted everything, which wasn't ideal.
Use the new one for safer, more controlled cleanup.
"""
import sys

print("\n⚠️  DEPRECATED SCRIPT - NUCLEAR OPTION")
print("="*70)
print("This script deleted ALL test data indiscriminately.")
print("A much better option is now available:")
print("    python cleanup_all_duplicates.py")
print("\nThe new script is smarter and safer!")
print("="*70 + "\n")
sys.exit(0)
