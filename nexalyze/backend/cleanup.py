import os
import shutil

files_to_delete = [
    r"c:\Hackathon Final Code\nexalyze\nexalyze\backend\services\enhanced_scraper_service.py",
    r"c:\Hackathon Final Code\nexalyze\nexalyze\backend\services\enhanced_data_sources.py",
    r"c:\Hackathon Final Code\nexalyze\nexalyze\backend\utils\reset_neo4j.py"
]

files_to_rename = [
    (r"c:\Hackathon Final Code\nexalyze\nexalyze\backend\services\web_scraper_service.py", r"c:\Hackathon Final Code\nexalyze\nexalyze\backend\services\scraper_service.py"),
    (r"c:\Hackathon Final Code\nexalyze\nexalyze\backend\services\data_sources_external.py", r"c:\Hackathon Final Code\nexalyze\nexalyze\backend\services\external_data_service.py")
]

for f in files_to_delete:
    try:
        if os.path.exists(f):
            os.remove(f)
            print(f"Deleted {f}")
        else:
            print(f"File not found: {f}")
    except Exception as e:
        print(f"Error deleting {f}: {e}")

for src, dst in files_to_rename:
    try:
        if os.path.exists(src):
            if os.path.exists(dst):
                os.remove(dst)
            os.rename(src, dst)
            print(f"Renamed {src} to {dst}")
        else:
            print(f"Source not found: {src}")
    except Exception as e:
        print(f"Error renaming {src}: {e}")
