"""
Standalone script to display test credentials without Django setup.

Usage:
    python show_test_credentials.py
    python show_test_credentials.py --format=json
    python show_test_credentials.py --format=simple
"""

import sys
import json

# Test credentials - hardcoded for quick reference
TEST_CREDENTIALS = [
    {
        'role': 'Admin',
        'username': 'admin_test',
        'email': 'admin@test.com',
        'password': 'password123',
        'redirect': '/admin/',
    },
    {
        'role': 'Teacher',
        'username': 'teacher_test',
        'email': 'teacher@test.com',
        'password': 'password123',
        'redirect': '/teacher/',
    },
    {
        'role': 'Support Staff',
        'username': 'staff_test',
        'email': 'staff@test.com',
        'password': 'password123',
        'redirect': '/',
    },
    {
        'role': 'Parent',
        'username': 'parent_test',
        'email': 'parent@test.com',
        'password': 'password123',
        'redirect': '/',
    },
]


def print_table():
    """Print as formatted table"""
    print('\n' + '='*90)
    print('TEST LOGIN CREDENTIALS')
    print('='*90)
    
    # Header
    header = f"{'Role':<18} {'Username':<15} {'Email':<22} {'Password':<15} {'Redirect':<10}"
    print(header)
    print('-'*90)
    
    # Rows
    for cred in TEST_CREDENTIALS:
        row = (
            f"{cred['role']:<18} "
            f"{cred['username']:<15} "
            f"{cred['email']:<22} "
            f"{cred['password']:<15} "
            f"{cred['redirect']:<10}"
        )
        print(row)
    
    print('='*90 + '\n')


def print_simple():
    """Print as simple list"""
    print('\nTEST LOGIN CREDENTIALS:\n')
    
    for cred in TEST_CREDENTIALS:
        print(f"{cred['role']}:")
        print(f"  Email:    {cred['email']}")
        print(f"  Username: {cred['username']}")
        print(f"  Password: {cred['password']}")
        print(f"  Redirect: {cred['redirect']}")
        print()


def print_json():
    """Print as JSON"""
    print(json.dumps(TEST_CREDENTIALS, indent=2))


def print_copy_paste():
    """Print ready to copy-paste"""
    print('\n' + '='*60)
    print('COPY-PASTE CREDENTIALS')
    print('='*60 + '\n')
    
    for cred in TEST_CREDENTIALS:
        print(f"{cred['role']}:")
        print(f"{cred['email']} / {cred['password']}")
        print()
    
    print('='*60 + '\n')


def main():
    format_type = 'table'
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--format=json':
            format_type = 'json'
        elif sys.argv[1] == '--format=simple':
            format_type = 'simple'
        elif sys.argv[1] == '--format=copy-paste':
            format_type = 'copy-paste'
        elif sys.argv[1] in ['-h', '--help']:
            print(__doc__)
            return
    
    if format_type == 'table':
        print_table()
    elif format_type == 'json':
        print_json()
    elif format_type == 'simple':
        print_simple()
    elif format_type == 'copy-paste':
        print_copy_paste()


if __name__ == '__main__':
    main()
