#include "watcher.h"
#include "event_logger.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

static DecoyEntry g_decoys[MAX_DECOYS];
static int g_num_decoys = 0;
static volatile int g_global_stop = 0;

static void normalize_path(char* path) {
    for (int i = 0; path[i] != '\0'; ++i) {
        if (path[i] == '\\') {
            path[i] = '/';
        }
    }
}

static int str_case_cmp(const char* s1, const char* s2) {
    while (*s1 && *s2) {
        if (tolower((unsigned char)*s1) != tolower((unsigned char)*s2)) {
            return (tolower((unsigned char)*s1) - tolower((unsigned char)*s2));
        }
        s1++;
        s2++;
    }
    return (tolower((unsigned char)*s1) - tolower((unsigned char)*s2));
}

int watcher_load_manifest(const char* manifest_path) {
    g_num_decoys = 0;
    FILE* f = fopen(manifest_path, "r");
    if (!f) {
        fprintf(stderr, "[WARN] Could not open manifest file: %s. Using path heuristics only.\n", manifest_path);
        return 0;
    }

    /* Read entire manifest into memory */
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (sz <= 0 || sz > 1048576) {
        fclose(f);
        return 0;
    }

    char* content = (char*)malloc(sz + 1);
    if (!content) {
        fclose(f);
        return 0;
    }
    size_t read_bytes = fread(content, 1, sz, f);
    content[read_bytes] = '\0';
    fclose(f);

    /* Parse file_id and relative_path pairs */
    char* cursor = content;
    while ((cursor = strstr(cursor, "\"file_id\"")) != NULL && g_num_decoys < MAX_DECOYS) {
        cursor += 9;
        while (*cursor && (*cursor == ' ' || *cursor == ':' || *cursor == '"' || *cursor == '\t')) cursor++;
        char cur_id[64] = {0};
        int id_idx = 0;
        while (*cursor && *cursor != '"' && id_idx < 63) {
            cur_id[id_idx++] = *cursor++;
        }
        cur_id[id_idx] = '\0';

        char* path_marker = strstr(cursor, "\"relative_path\"");
        if (path_marker) {
            path_marker += 15;
            while (*path_marker && (*path_marker == ' ' || *path_marker == ':' || *path_marker == '"' || *path_marker == '\t')) path_marker++;
            char cur_path[512] = {0};
            int path_idx = 0;
            while (*path_marker && *path_marker != '"' && path_idx < 511) {
                cur_path[path_idx++] = *path_marker++;
            }
            cur_path[path_idx] = '\0';
            normalize_path(cur_path);

            strncpy(g_decoys[g_num_decoys].file_id, cur_id, sizeof(g_decoys[g_num_decoys].file_id) - 1);
            strncpy(g_decoys[g_num_decoys].relative_path, cur_path, sizeof(g_decoys[g_num_decoys].relative_path) - 1);
            g_num_decoys++;
            cursor = path_marker;
        } else {
            break;
        }
    }

    free(content);
    printf("[INFO] Loaded %d decoy definitions from manifest.\n", g_num_decoys);
    return g_num_decoys;
}

int watcher_check_decoy(const char* relative_path, char* out_file_id, size_t out_id_size) {
    if (!relative_path) return 0;

    char norm[MAX_PATH_LEN];
    strncpy(norm, relative_path, sizeof(norm) - 1);
    norm[sizeof(norm) - 1] = '\0';
    normalize_path(norm);

    /* 1. Exact or suffix match against manifest entries */
    for (int i = 0; i < g_num_decoys; ++i) {
        if (str_case_cmp(norm, g_decoys[i].relative_path) == 0) {
            if (out_file_id && out_id_size > 0) {
                strncpy(out_file_id, g_decoys[i].file_id, out_id_size - 1);
                out_file_id[out_id_size - 1] = '\0';
            }
            return 1;
        }
    }

    /* 2. Substring/prefix check for decoys/ directory */
    if (strncmp(norm, "decoys/", 7) == 0 || strstr(norm, "/decoys/") != NULL) {
        if (out_file_id && out_id_size > 0) {
            strncpy(out_file_id, "DECOY-DYNAMIC", out_id_size - 1);
            out_file_id[out_id_size - 1] = '\0';
        }
        return 1;
    }

    if (out_file_id && out_id_size > 0) {
        out_file_id[0] = '\0';
    }
    return 0;
}

void watcher_stop(void) {
    g_global_stop = 1;
}

static const char* action_to_string(DWORD action) {
    switch (action) {
        case FILE_ACTION_ADDED: return "CREATE";
        case FILE_ACTION_REMOVED: return "DELETE";
        case FILE_ACTION_MODIFIED: return "MODIFY";
        case FILE_ACTION_RENAMED_OLD_NAME: return "RENAME_OLD";
        case FILE_ACTION_RENAMED_NEW_NAME: return "RENAME_NEW";
        default: return "MODIFY";
    }
}

int watcher_run(WatcherConfig* config) {
    if (!config || !config->monitored_dir[0]) {
        fprintf(stderr, "[ERROR] Invalid watcher configuration.\n");
        return 0;
    }

    g_global_stop = 0;

    /* Initialize logger */
    if (!logger_init(config->log_file)) {
        fprintf(stderr, "[ERROR] Logger initialization failed.\n");
        return 0;
    }

    /* Load manifest */
    watcher_load_manifest(config->manifest_file);

    /* Open directory handle with OVERLAPPED and BACKUP_SEMANTICS */
    HANDLE hDir = CreateFileA(
        config->monitored_dir,
        FILE_LIST_DIRECTORY,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        NULL,
        OPEN_EXISTING,
        FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OVERLAPPED,
        NULL
    );

    if (hDir == INVALID_HANDLE_VALUE) {
        DWORD err = GetLastError();
        fprintf(stderr, "[ERROR] Failed to open monitored directory '%s' (Win32 Error: %lu)\n",
                config->monitored_dir, err);
        logger_close();
        return 0;
    }

    /* Create notification event handle for overlapped I/O */
    OVERLAPPED overlapped;
    ZeroMemory(&overlapped, sizeof(OVERLAPPED));
    overlapped.hEvent = CreateEvent(NULL, TRUE, FALSE, NULL);
    if (!overlapped.hEvent) {
        fprintf(stderr, "[ERROR] Failed to create overlapped event.\n");
        CloseHandle(hDir);
        logger_close();
        return 0;
    }

    /* Buffer must be DWORD aligned */
    BYTE buffer[BUFFER_SIZE] __attribute__((aligned(sizeof(DWORD))));
    DWORD filter = FILE_NOTIFY_CHANGE_FILE_NAME |
                   FILE_NOTIFY_CHANGE_DIR_NAME  |
                   FILE_NOTIFY_CHANGE_ATTRIBUTES|
                   FILE_NOTIFY_CHANGE_SIZE      |
                   FILE_NOTIFY_CHANGE_LAST_WRITE|
                   FILE_NOTIFY_CHANGE_CREATION;

    unsigned long event_counter = 0;
    DWORD start_time = GetTickCount();

    printf("[INFO] Monitoring initialized on directory: %s\n", config->monitored_dir);
    printf("[INFO] Logging events to: %s\n", config->log_file);
    printf("[INFO] Awaiting file-system activity... (Ctrl+C to stop)\n");
    fflush(stdout);

    while (!config->stop_requested && !g_global_stop) {
        ResetEvent(overlapped.hEvent);
        DWORD bytes_returned = 0;

        BOOL ok = ReadDirectoryChangesW(
            hDir,
            buffer,
            sizeof(buffer),
            config->watch_subtree ? TRUE : FALSE,
            filter,
            &bytes_returned,
            &overlapped,
            NULL
        );

        if (!ok) {
            DWORD err = GetLastError();
            if (err != ERROR_IO_PENDING) {
                fprintf(stderr, "[ERROR] ReadDirectoryChangesW failed (Win32 Error: %lu)\n", err);
                break;
            }
        }

        /* Wait for directory changes with periodic 100ms timeout to check stop signal */
        BOOL change_occurred = FALSE;
        while (!config->stop_requested && !g_global_stop) {
            DWORD wait_res = WaitForSingleObject(overlapped.hEvent, 100);
            if (wait_res == WAIT_OBJECT_0) {
                change_occurred = TRUE;
                break;
            } else if (wait_res == WAIT_TIMEOUT) {
                /* Check optional timeout */
                if (config->timeout_ms > 0 && (GetTickCount() - start_time) >= config->timeout_ms) {
                    printf("[INFO] Execution timeout reached (%lu ms). Terminating watcher.\n", config->timeout_ms);
                    g_global_stop = 1;
                    break;
                }
                continue;
            } else {
                fprintf(stderr, "[ERROR] WaitForSingleObject error: %lu\n", GetLastError());
                g_global_stop = 1;
                break;
            }
        }

        if (!change_occurred) {
            CancelIo(hDir);
            break;
        }

        /* Retrieve overlapped result */
        if (!GetOverlappedResult(hDir, &overlapped, &bytes_returned, TRUE)) {
            DWORD err = GetLastError();
            if (err == ERROR_NOTIFY_ENUM_DIR) {
                fprintf(stderr, "[WARN] Buffer overflow detected! Some events may have been dropped.\n");
            } else {
                fprintf(stderr, "[ERROR] GetOverlappedResult failed: %lu\n", err);
            }
            continue;
        }

        if (bytes_returned == 0) {
            fprintf(stderr, "[WARN] Zero bytes returned from directory changes notification.\n");
            continue;
        }

        /* Parse FILE_NOTIFY_INFORMATION linked list */
        BYTE* ptr = buffer;
        while (ptr < buffer + bytes_returned) {
            FILE_NOTIFY_INFORMATION* record = (FILE_NOTIFY_INFORMATION*)ptr;

            /* Extract filename from wide chars */
            int wlen = record->FileNameLength / sizeof(WCHAR);
            char file_name[MAX_PATH_LEN] = {0};
            int converted = WideCharToMultiByte(CP_UTF8, 0, record->FileName, wlen, file_name, sizeof(file_name) - 1, NULL, NULL);
            if (converted <= 0) {
                strncpy(file_name, "unknown", sizeof(file_name) - 1);
            } else {
                file_name[converted] = '\0';
            }

            normalize_path(file_name);

            /* Filter out temporary .gitkeep or log files inside monitored directory */
            if (strstr(file_name, ".gitkeep") != NULL) {
                if (record->NextEntryOffset == 0) break;
                ptr += record->NextEntryOffset;
                continue;
            }

            event_counter++;
            MonitorEvent evt;
            ZeroMemory(&evt, sizeof(MonitorEvent));
            evt.event_id = event_counter;
            logger_get_iso_timestamp(evt.timestamp, sizeof(evt.timestamp));
            strncpy(evt.event_type, action_to_string(record->Action), sizeof(evt.event_type) - 1);
            strncpy(evt.relative_path, file_name, sizeof(evt.relative_path) - 1);
            strncpy(evt.source, "windows_monitor_c", sizeof(evt.source) - 1);
            snprintf(evt.details, sizeof(evt.details), "ActionCode=%lu;Bytes=%lu", (unsigned long)record->Action, (unsigned long)bytes_returned);

            /* Decoy lookup */
            char decoy_id[64] = {0};
            evt.is_decoy = watcher_check_decoy(file_name, decoy_id, sizeof(decoy_id));
            if (evt.is_decoy) {
                strncpy(evt.file_id, decoy_id, sizeof(evt.file_id) - 1);
            } else {
                evt.file_id[0] = '\0';
            }

            logger_log_event(&evt);

            if (config->max_events > 0 && event_counter >= config->max_events) {
                printf("[INFO] Max events limit (%lu) reached. Stopping watcher.\n", config->max_events);
                g_global_stop = 1;
                break;
            }

            if (record->NextEntryOffset == 0) {
                break;
            }
            ptr += record->NextEntryOffset;
        }
    }

    printf("[INFO] Shutting down watcher engine...\n");
    CancelIo(hDir);
    CloseHandle(overlapped.hEvent);
    CloseHandle(hDir);
    logger_close();
    printf("[INFO] Watcher terminated cleanly. Total events recorded: %lu\n", event_counter);
    return 1;
}
