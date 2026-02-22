#include <stdio.h>

/* Function prototypes */
void process_data(int x);
void log_iteration(int i);
void handle_event(int count);
void update_status();

/* Simulates work inside a for loop */
void process_data(int x) {
    printf("Processing value: %d\n", x);
}

/* Logs loop iteration */
void log_iteration(int i) {
    printf("For loop iteration: %d\n", i);
}

/* Simulates event handling */
void handle_event(int count) {
    printf("Handling event #%d\n", count);
}

/* Updates system status */
void update_status() {
    printf("Status updated\n");
}

int main() {

    // ---------- FOR LOOP TEST ----------
    for (int i = 0; i < 5; i++) {
        process_data(i);     // unique call #1
        log_iteration(i);    // unique call #2
    }

    /* ---------- WHILE LOOP TEST ---------- */
    int counter = 0;
    while (counter < 3) {
        handle_event(counter); // unique call #3
        update_status();       // unique call #4
        counter++;
    }

    return 0;
}
