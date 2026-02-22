#include <stdio.h>

/* Function prototypes */
void outer_for(int i);
void inner_for(int i, int j);
void outer_while(int x);
void inner_while(int x, int y);
void mixed_call(int a, int b);

/* Outer for-loop function */
void outer_for(int i) {
    printf("Outer for: %d\n", i);
}

/* Inner for-loop function */
void inner_for(int i, int j) {
    printf("Inner for: %d %d\n", i, j);
}

/* Outer while-loop function */
void outer_while(int x) {
    printf("Outer while: %d\n", x);
}

/* Inner while-loop function */
void inner_while(int x, int y) {
    printf("Inner while: %d %d\n", x, y);
}

/* Mixed nesting call */
void mixed_call(int a, int b) {
    printf("Mixed loop call: %d %d\n", a, b);
}

int main() {

    // -------- Nested FOR loops --------
    for (int i = 0; i < 3; i++) {
        outer_for(i);

        for (int j = 0; j < 2; j++) {
            inner_for(i, j);
        }
    }

    /* -------- Nested WHILE loops -------- */
    int x = 0;
    while (x < 2) {
        outer_while(x);

        int y = 0;
        while (y < 2) {
            inner_while(x, y);
            y++;
        }

        x++;
    }

    // -------- Mixed nesting: FOR inside WHILE --------
    int a = 0;
    while (a < 2) {
        for (int b = 0; b < 3; b++) {
            mixed_call(a, b);
        }
        a++;
    }

    return 0;
}
