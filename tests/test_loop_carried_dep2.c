// test_lcd_array_inplace.c
#include <stdio.h>

int main(void) {
    int a[8] = {1, 1, 1, 1, 1, 1, 1, 1};

    // Loop-carried TRUE dependency through memory:
    // a[i] reads a[i-1], which was written by the previous iteration.
    for (int i = 1; i < 8; i++) {
        a[i] = a[i] + a[i - 1];
    }

    // Expected output: 1 2 3 4 5 6 7 8
    for (int i = 0; i < 8; i++) {
        printf("%d%s", a[i], (i == 7) ? "\n" : " ");
    }

    return 0;
}