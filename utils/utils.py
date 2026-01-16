class utils:
    def size(self, size: float):
        size_bytes = float(size)
        size_mb = size_bytes / (1024 * 1024)
        return f"{size_mb:.1f}MB"