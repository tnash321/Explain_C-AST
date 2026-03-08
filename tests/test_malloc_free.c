// tests/test_malloc_free_loop.c
// Each iteration allocates and then frees an array.
// The analyzer should penalize loops that perform dynamic memory allocation.
#include <stdlib.h>

void test_malloc_free_loop(int n) {
    for (int i = 0; i < n; i++) {
        // allocate memory on each iteration
        int *arr = (int *)malloc(sizeof(int) * 100);
        if (!arr) {
            // handle failure
            return;
        }
        // initialize array
        for (int j = 0; j < 100; j++) {
            arr[j] = j;
        }
        // free memory
        free(arr);
    }
}