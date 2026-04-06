// tests/test_n_cubed.c

void cubic_loop(int n) {
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            for (int k = 0; k < n; k++) {
                int x = i + j + k;
            }
        }
    }
}