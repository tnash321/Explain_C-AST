#include <stdio.h>

/* Function prototypes */
void recursive_worker(int depth);
void loop_helper(int i);
void nested_helper(int i, int j);

/* Simple helper called from loops */
void loop_helper(int i) {
    printf("loop_helper: %d\n", i);
}

/* Nested helper */
void nested_helper(int i, int j) {
    printf("nested_helper: %d %d\n", i, j);
}

/*
 * Recursive function:
 * - calls itself
 * - contains loops
 * - loops contain function calls
 */
void recursive_worker(int depth) {

    printf("Entering recursion depth: %d\n", depth);

    // Base case
    if (depth <= 0) {
        printf("Base case reached\n");
        return;
    }

    // --- for-loop inside recursion ---
    for (int i = 0; i < 2; i++) {
        loop_helper(i);

        // nested loop
        for (int j = 0; j < 2; j++) {
            nested_helper(i, j);
        }
    }

    // --- while-loop inside recursion ---
    int x = 0;
    while (x < 2) {
        printf("while loop x=%d at depth %d\n", x, depth);
        x++;
    }

    // Recursive call
    recursive_worker(depth - 1);

    printf("Exiting recursion depth: %d\n", depth);
}

int main() {

    // Loop that triggers recursion multiple times
    for (int k = 0; k < 2; k++) {
        printf("Main loop iteration: %d\n", k);
        recursive_worker(3);
    }

    return 0;
}
