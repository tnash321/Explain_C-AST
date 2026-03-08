// tests/test_io_multiloops.c
//
// This file contains three loops exercising input/output functions.
// It should trigger I/O detection heuristics in your analyzer.

#include <stdio.h>

void test_io_multiloops(void) {
    // Loop 1: prints a message ten times.
    for (int i = 0; i < 10; i++) {
        printf("Loop 1: i = %d\n", i);
    }

    // Loop 2: reads five integers from stdin.
    int value = 0;
    for (int j = 0; j < 5; j++) {
        // Prompt the user
        printf("Enter an integer: ");
        scanf("%d", &value);
    }

    // Loop 3: interleaves printing and scanning three times.
    for (int k = 0; k < 3; k++) {
        printf("Loop 3 (iteration %d). Enter a value: ", k);
        scanf("%d", &value);
        printf("You entered: %d\n", value);
    }
}