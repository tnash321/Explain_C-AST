#include <stdio.h>
#include <stdlib.h>

int global_total = 0;

void helper(int x) {
    printf("helper: %d\n", x);
}

void stress_many_issues(int n) {
    int sum = 0;

    for (int i = 0; i < n; i++) {
        printf("i = %d\n", i);

        int *arr = malloc(sizeof(int) * 10);
        arr[0] = i;

        global_total += arr[0];
        sum += i;

        helper(i);

        if (i == 5) {
            break;
        }

        free(arr);
    }
}

int main() {
    stress_many_issues(20);
    return 0;
}