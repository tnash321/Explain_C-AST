#include <stdio.h>

void log_loop(int n) {
    for (int i = 1; i < n; i *= 2) {
        printf("i = %d\n", i);
    }
}

int main() {
    int n = 64;
    log_loop(n);
    return 0;
}