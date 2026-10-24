#ifndef WATCHER_H
#define WATCHER_H

#include <windows.h>

#define MAX_DECOYS 256
#define BUFFER_SIZE 65536

typedef struct {
    char file_id[64];
    char relative_path[512];
} DecoyEntry;

typedef struct {
    char monitored_dir[512];
    char log_file[512];
    char manifest_file[512];
    int watch_subtree;
    unsigned long max_events;   /* 0 for continuous */
    unsigned long timeout_ms;   /* 0 for indefinite */
    volatile int stop_requested;
} WatcherConfig;

/* Loads decoy manifest JSON file. Returns count of loaded decoys. */
int watcher_load_manifest(const char* manifest_path);

/* Checks if given relative path corresponds to a decoy. Fills file_id if matched. */
int watcher_check_decoy(const char* relative_path, char* out_file_id, size_t out_id_size);

/* Starts the directory monitoring loop. Blocks until stop_requested or error. */
int watcher_run(WatcherConfig* config);

/* Requests the running watcher loop to stop gracefully. */
void watcher_stop(void);

#endif /* WATCHER_H */
