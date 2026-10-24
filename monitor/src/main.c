#include "watcher.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>

static WatcherConfig g_config;

static BOOL WINAPI console_ctrl_handler(DWORD signal) {
    if (signal == CTRL_C_EVENT || signal == CTRL_BREAK_EVENT || signal == CTRL_CLOSE_EVENT) {
        printf("\n[INFO] Interrupt signal received (%lu). Initiating graceful shutdown...\n", signal);
        g_config.stop_requested = 1;
        watcher_stop();
        return TRUE;
    }
    return FALSE;
}

static void print_usage(const char* prog_name) {
    printf("=================================================================\n");
    printf(" Intelligent Decoy File System - Windows C Monitoring Engine\n");
    printf("=================================================================\n");
    printf("Usage: %s [options]\n\n", prog_name);
    printf("Options:\n");
    printf("  --dir <path>         Path to directory to monitor (default: runtime/monitored)\n");
    printf("  --log <path>         Path to output JSONL log (default: logs/events.jsonl)\n");
    printf("  --manifest <path>    Path to decoy manifest (default: decoys/manifest.json)\n");
    printf("  --timeout <ms>       Automatic exit after N milliseconds (0 = indefinite)\n");
    printf("  --max-events <n>     Exit after capturing N events (0 = indefinite)\n");
    printf("  --help               Display this help text\n\n");
}

int main(int argc, char* argv[]) {
    /* Initialize default configuration */
    memset(&g_config, 0, sizeof(WatcherConfig));
    strncpy(g_config.monitored_dir, "runtime/monitored", sizeof(g_config.monitored_dir) - 1);
    strncpy(g_config.log_file, "logs/events.jsonl", sizeof(g_config.log_file) - 1);
    strncpy(g_config.manifest_file, "decoys/manifest.json", sizeof(g_config.manifest_file) - 1);
    g_config.watch_subtree = 1;
    g_config.max_events = 0;
    g_config.timeout_ms = 0;
    g_config.stop_requested = 0;

    /* Parse CLI arguments */
    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--dir") == 0 && i + 1 < argc) {
            strncpy(g_config.monitored_dir, argv[++i], sizeof(g_config.monitored_dir) - 1);
        } else if (strcmp(argv[i], "--log") == 0 && i + 1 < argc) {
            strncpy(g_config.log_file, argv[++i], sizeof(g_config.log_file) - 1);
        } else if (strcmp(argv[i], "--manifest") == 0 && i + 1 < argc) {
            strncpy(g_config.manifest_file, argv[++i], sizeof(g_config.manifest_file) - 1);
        } else if (strcmp(argv[i], "--timeout") == 0 && i + 1 < argc) {
            g_config.timeout_ms = (unsigned long)strtoul(argv[++i], NULL, 10);
        } else if (strcmp(argv[i], "--max-events") == 0 && i + 1 < argc) {
            g_config.max_events = (unsigned long)strtoul(argv[++i], NULL, 10);
        } else if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
            print_usage(argv[0]);
            return 0;
        } else {
            fprintf(stderr, "[WARN] Unrecognized option: %s\n", argv[i]);
        }
    }

    /* Set up Console Ctrl Handler for clean exit */
    if (!SetConsoleCtrlHandler(console_ctrl_handler, TRUE)) {
        fprintf(stderr, "[WARN] Could not set console control handler.\n");
    }

    printf("=================================================================\n");
    printf(" Intelligent Decoy File System - C Telemetry Watcher Starting\n");
    printf(" Monitored Dir: %s\n", g_config.monitored_dir);
    printf(" Event Log:     %s\n", g_config.log_file);
    printf(" Manifest:      %s\n", g_config.manifest_file);
    if (g_config.timeout_ms > 0) printf(" Timeout:       %lu ms\n", g_config.timeout_ms);
    if (g_config.max_events > 0) printf(" Max Events:    %lu\n", g_config.max_events);
    printf("=================================================================\n");

    int res = watcher_run(&g_config);
    return res ? 0 : 1;
}
