import os

# These folders have nothing to do with YOUR code.
# Scanning them wastes time and tokens.
SKIP_DIRS = {
    'venv', '.venv', 'env',          # virtual environments
    'node_modules',                   # JS dependencies (can be 50k files)
    '.git', '.svn', '.hg',           # version control internals
    '__pycache__', '.pytest_cache',  # Python bytecode cache
    'dist', 'build', 'out',          # compiled/bundled output
    '.next', '.nuxt',                # JS framework build outputs
    'coverage', '.nyc_output',       # test coverage artifacts
}

# Only scan files that actually contain code.
# We skip images, fonts, lock files, compiled binaries, etc.
SCAN_EXTENSIONS = {
    '.py',   # Python
    '.js',   # JavaScript
    '.ts',   # TypeScript
    '.jsx',  # React JS
    '.tsx',  # React TS
    '.php',  # PHP
    '.java', # Java
    '.go',   # Go
    '.rb',   # Ruby
    '.cs',   # C#
    '.cpp',  # C++
    '.c',    # C
    '.env',  # Environment files (critical to scan for exposed secrets)
    '.yml',  # Config files (can contain secrets)
    '.yaml', # Config files
    '.json', # Config / package files
    '.xml',  # Config files
    '.sh',   # Shell scripts
    '.sql',  # Database queries (SQL injection risk)
}

def walk_codebase(root_path):
    """
    Walks a directory tree and returns a list of files to scan.
    
    root_path: the folder you want to scan (e.g. "/home/user/my-project")
    returns: a list of absolute file paths
    """
    
    # Make sure the path actually exists before we do anything
    if not os.path.exists(root_path):
        print(f"[ERROR] Path does not exist: {root_path}")
        return []
    
    files_to_scan = []  # we'll collect results here

    # os.walk() is Python's built-in directory traverser.
    # For each folder it visits, it gives us:
    #   current_dir  = the folder we're currently in
    #   subdirs      = list of subfolders inside it (we can modify this!)
    #   files        = list of files inside it
    for current_dir, subdirs, files in os.walk(root_path):
        
        # This is the key trick: by MODIFYING subdirs in-place,
        # we tell os.walk() which folders NOT to descend into.
        # If we remove 'node_modules' here, os.walk skips it entirely.
        subdirs[:] = [
            d for d in subdirs
            if d not in SKIP_DIRS and not d.startswith('.')
        ]
        
        for filename in files:
            # Get the file extension, e.g. ".py" from "app.py"
            _, ext = os.path.splitext(filename)
            
            # Only include files whose extension is in our allow-list
            if ext.lower() in SCAN_EXTENSIONS:
                # Build the full path, e.g. "/home/user/project/src/app.py"
                full_path = os.path.join(current_dir, filename)
                files_to_scan.append(full_path)
    
    return files_to_scan


def get_file_stats(file_paths, root_path):
    """
    Given a list of file paths, returns a summary of what we found.
    Useful for showing the user what's about to be scanned.
    """
    stats = {
        'total_files': len(file_paths),
        'total_lines': 0,
        'by_extension': {},  # e.g. { '.py': 12, '.js': 8 }
    }
    
    for path in file_paths:
        # Count by extension
        _, ext = os.path.splitext(path)
        stats['by_extension'][ext] = stats['by_extension'].get(ext, 0) + 1
        
        # Count lines (safely — skip files that can't be read as text)
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                stats['total_lines'] += sum(1 for _ in f)
        except Exception:
            pass  # if a file can't be read, just skip it
    
    return stats