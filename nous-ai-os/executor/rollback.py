from executor.file_ops import restore_backup

def rollback(backup_path, original_path):
    try:
        restore_backup(backup_path, original_path)
        print("ROLLBACK SUCCESS")
    except Exception as e:
        print("ROLLBACK FAILED:", e)
