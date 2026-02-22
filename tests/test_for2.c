#include <stdio.h>
#include <stdlib.h>

void heavy_compute(int n) {
    for (int i = 0; i < n; i++) {
        printf("compute %d\n", i);
    }
}

void matrix_op(int n) {
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            if ((i + j) % 10 == 0) {
                printf("special case\n");
            }
        }
    }
}

void allocate_inside_loop(int n) {
    for (int i = 0; i < n; i++) {
        int *arr = malloc(sizeof(int) * 100);

        for (int j = 0; j < 100; j++) {
            arr[j] = j;
        }

        free(arr);
    }
}

void early_exit(int n) {
    for (int i = 0; i < n; i++) {
        if (i == 5) {
            break;
        }
    }
}

void constant_loop() {
    for (int i = 0; i < 10; i++) {
        printf("constant\n");
    }
}

int main() {
    int n = 20;

    heavy_compute(n);
    matrix_op(n);
    allocate_inside_loop(n);
    early_exit(n);
    constant_loop();

    return 0;
}
