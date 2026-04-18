import sys
import os

# This line adds the parent folder to Python's search path
# so we can import our 'scanner' module
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from scanner import walk_codebase, get_file_stats

# We'll scan our OWN project folder as a test
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print(f"Scanning: {project_root}")
print("=" * 50)

files = walk_codebase(project_root)
stats = get_file_stats(files, project_root)

print(f"\nFiles found: {stats['total_files']}")
print(f"Total lines: {stats['total_lines']}")
print(f"\nBy type:")
for ext, count in sorted(stats['by_extension'].items()):
    print(f"  {ext:8} → {count} file(s)")

print(f"\nAll files:")
for f in files:
    # Print relative path (cleaner than full absolute path)
    print(f"  {os.path.relpath(f, project_root)}")