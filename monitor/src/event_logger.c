#include "event_logger.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static FILE* g_log_file = NULL;
static CRITICAL_SECTION g_logger_cs;
static int g_cs_initialized = 0;
static unsigned long g_run_id = 0;

static void escape_json_string(const char* input, char* output, size_t max_len) {
    size_t out_idx = 0;
    for (size_t in_idx = 0; input[in_idx] != '\0' && out_idx + 2 < max_len; ++in_idx) {
        char c = input[in_idx];
        if (c == '"') {
            output[out_idx++] = '\\';
            output[out_idx++] = '"';
        } else if (c == '\\') {
            output[out_idx++] = '/'; /* Normalize path separators */
        } else if (c == '\n') {
            output[out_idx++] = ' ';
        } else if (c == '\r') {
            /* skip */
        } else {
            output[out_idx++] = c;
        }
    }
    output[out_idx] = '\0';
}

void logger_get_iso_timestamp(char* buffer, size_t buf_size) {
    SYSTEMTIME st;
    GetLocalTime(&st);
    snprintf(buffer, buf_size, "%04d-%02d-%02dT%02d:%02d:%02d.%03d",
             st.wYear, st.wMonth, st.wDay,
             st.wHour, st.wMinute, st.wSecond, st.wMilliseconds);
}

int logger_init(const char* log_file_path) {
    if (!g_cs_initialized) {
        InitializeCriticalSection(&g_logger_cs);
        g_cs_initialized = 1;
    }

    if (g_run_id == 0) {
        SYSTEMTIME st;
        GetLocalTime(&st);
        g_run_id = (unsigned long)((st.wHour * 3600 + st.wMinute * 60 + st.wSecond) * 1000 + st.wMilliseconds);
    }

    EnterCriticalSection(&g_logger_cs);

    /* Open in append mode */
    g_log_file = fopen(log_file_path, "a");
    if (!g_log_file) {
        fprintf(stderr, "[ERROR] Failed to open log file for writing: %s\n", log_file_path);
        LeaveCriticalSection(&g_logger_cs);
        return 0;
    }

    LeaveCriticalSection(&g_logger_cs);
    return 1;
}

void logger_log_event(const MonitorEvent* evt) {
    if (!g_log_file || !evt) return;

    char escaped_path[MAX_PATH_LEN * 2];
    char escaped_details[MAX_DETAILS_LEN * 2];
    escape_json_string(evt->relative_path, escaped_path, sizeof(escaped_path));
    escape_json_string(evt->details, escaped_details, sizeof(escaped_details));

    EnterCriticalSection(&g_logger_cs);

    /* Write JSON Line */
    fprintf(g_log_file,
            "{\"event_id\":\"EVT-%08lu-%04lu\",\"timestamp\":\"%s\",\"event_type\":\"%s\",\"relative_path\":\"%s\",",
            g_run_id, evt->event_id, evt->timestamp, evt->event_type, escaped_path);

    if (evt->file_id[0] != '\0' && strcmp(evt->file_id, "null") != 0) {
        fprintf(g_log_file, "\"file_id\":\"%s\",", evt->file_id);
    } else {
        fprintf(g_log_file, "\"file_id\":null,");
    }

    fprintf(g_log_file, "\"is_decoy\":%s,\"source\":\"%s\",\"details\":\"%s\"}\n",
            evt->is_decoy ? "true" : "false",
            evt->source[0] != '\0' ? evt->source : "windows_monitor_c",
            escaped_details);

    fflush(g_log_file);

    LeaveCriticalSection(&g_logger_cs);

    /* Also print to stdout for interactive visibility */
    printf("[EVENT] EVT-%08lu-%04lu | %s | %-10s | %s | %s%s%s\n",
           g_run_id,
           evt->event_id,
           evt->timestamp,
           evt->event_type,
           escaped_path,
           evt->is_decoy ? "[DECOY: " : "",
           evt->is_decoy ? (evt->file_id[0] ? evt->file_id : "YES") : "",
           evt->is_decoy ? "]" : "[NORMAL]");
    fflush(stdout);
}

void logger_flush(void) {
    if (g_log_file) {
        EnterCriticalSection(&g_logger_cs);
        fflush(g_log_file);
        LeaveCriticalSection(&g_logger_cs);
    }
}

void logger_close(void) {
    if (g_log_file) {
        EnterCriticalSection(&g_logger_cs);
        fflush(g_log_file);
        fclose(g_log_file);
        g_log_file = NULL;
        LeaveCriticalSection(&g_logger_cs);
    }
    if (g_cs_initialized) {
        DeleteCriticalSection(&g_logger_cs);
        g_cs_initialized = 0;
    }
}
