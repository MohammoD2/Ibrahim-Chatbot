import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
from process_pipeline import process_file

class TextFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.txt'):
            print(f"New file detected: {event.src_path}")
            process_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.txt'):
            print(f"File modified: {event.src_path}")
            process_file(event.src_path)

def watch_directory(path):
    event_handler = TextFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nStopping file watcher...")
    
    observer.join()

if __name__ == "__main__":
    watch_directory("local_storage") 