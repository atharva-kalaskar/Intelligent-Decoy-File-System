#ifndef EVENT_LOGGER_H
#define EVENT_LOGGER_H

#include <stdio.h>
#include <windows.h>

#define MAX_PATH_LEN 512
#define MAX_ID_LEN 64
#define MAX_TYPE_LEN 24
#define MAX_SOURCE_LEN 32
#define MAX_DETAILS_LEN 128

typedef struct {
    unsigned long event_id;
    char timestamp[32];      /* ISO 8601 string: YYYY-MM-DDTHH:MM:SS.mmm */
    char event_type[MAX_TYPE_LEN]; /* CREATE, DELETE, MODIFY, RENAME_OLD, RENAME_NEW */
    char relative_path[MAX_PATH_LEN];
    char file_id[MAX_ID_LEN];      /* DECOY-001 or NULL */
    int is_decoy;                  /* 1 if decoy, 0 otherwise */
    char source[MAX_SOURCE_LEN];   /* windows_monitor_c */
    char details[MAX_DETAILS_LEN];
} MonitorEvent;

/* Initializes logger with target JSON Lines file path. Returns 1 on success, 0 on failure. */
int logger_init(const char* log_file_path);

/* Writes a single validated JSON Line record to log and flushes buffer. */
void logger_log_event(const MonitorEvent* evt);

/* Flushes file buffers to disk. */
void logger_flush(void);

/* Closes log file handle. */
void logger_close(void);

/* Formats current system local time into ISO-8601 string (buffer >= 32 chars). */
void logger_get_iso_timestamp(char* buffer, size_t buf_size);

#endif /* EVENT_LOGGER_H */
