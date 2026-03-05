// Tyler Nash
// CSCI 551: Final Parallel Program
// Finalized version: corrected to remove loop-carried deps in leftRiemann OpenMP loop

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <mpi.h>
#include <omp.h>

static const double PI = 3.14159265359;
static const double ascale = 0.236589076381454;
static const double tscale = 1800.0 / (2.0 * PI);
static const double vscale = ascale * 1800.0 / (2.0 * PI);

double sine(double x);
double cosine(double x);
double fpp_accel(double time);
double fpp_vel(double time);
double integrate(double x, int use_vel);
double leftRiemann(double left_ref, double right_ref, int rectangles, double base_len, int use_vel);

int main(int argc, char *argv[]) {
    int my_rank, comm_sz, local_n;
    double step_size, local_a, local_b;
    double local_int_area, total_int_area;
    double local_vel, final_vel;
    double a, b, n;
    int thread_count;

    step_size = 0.01;

    if (argc < 4) {
        printf("./mytrain.c <a> <b> <thread_count> <step_size>\n");
        return 1;
    }

    a = atof(argv[1]);
    b = atof(argv[2]);
    thread_count = atoi(argv[3]);

    if (argc == 5) {
        step_size = atof(argv[4]);
    }

    omp_set_num_threads(thread_count);

    double reciprocal = 1.0 / step_size;
    n = (b - a) * reciprocal;               // number of rectangles over [a,b]
    if (n < 0) n = -n;                      // just in case user flips a/b
    int n_int = (int)(n + 0.5);             // round to nearest int
    if (n_int <= 0) n_int = 1;

    struct timespec start, end;

    MPI_Init(NULL, NULL);
    MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);
    MPI_Comm_size(MPI_COMM_WORLD, &comm_sz);

    // split rectangles among ranks
    local_n = n_int / comm_sz;
    local_a = a + my_rank * local_n * step_size;
    local_b = local_a + local_n * step_size;

    if (my_rank == comm_sz - 1) {
        local_n = n_int - (comm_sz - 1) * local_n;
        local_b = b;
    }

    clock_gettime(CLOCK_MONOTONIC, &start);

    local_int_area = leftRiemann(local_a, local_b, local_n, step_size, 1);
    MPI_Reduce(&local_int_area, &total_int_area, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);

    local_vel = leftRiemann(local_a, local_b, local_n, step_size, 0);
    MPI_Reduce(&local_vel, &final_vel, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);

    clock_gettime(CLOCK_MONOTONIC, &end);

    double elapsed = (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;

    if (my_rank == 0) {
        printf("-------------------------------------------------------------------\n");
        printf("This program finished in %.6f seconds.\n", elapsed);
        printf("After program is finished: with n = %d quadratures, our estimate\n", n_int);
        printf("of the train distance from %lf to %lf = %lf\n\n", a, b, total_int_area);
        printf("The final velocity is %lf\n", final_vel);
        printf("-------------------------------------------------------------------\n");
    }

    MPI_Finalize();
    return 0;
}

/*
 * Corrected left Riemann sum:
 * Removes loop-carried dependencies by computing x directly from i.
 * No shared x or left_val updated across iterations.
 */
double leftRiemann(double left_ref, double right_ref, int rectangles, double base_len, int use_vel)
{
    (void)right_ref; // not needed when rectangles/base_len define the interval
    double area = 0.0;

#pragma omp parallel for reduction(+:area)
    for (long long i = 0; i < (long long)rectangles; ++i) {
        double x = left_ref + (double)i * base_len;   // independent per-iteration
        double left_val = integrate(x, use_vel);      // independent per-iteration
        area += left_val * base_len;
    }

    return area;
}

/*
 * Taylor series with recurrence.
 * These loops are sequential recurrences internally, but they are not part of
 * the parallel Riemann loop and do not create OpenMP loop-carried deps now.
 */
double cosine(double x){
    double sum = 1.0;          // cos(0) term
    double term = 1.0;         // current term
    int iterations = 100;

    // cos(x) = 1 - x^2/2! + x^4/4! - ...
    for (int k = 1; k < iterations; ++k) {
        double num = -x * x;
        double den = (2.0 * k - 1.0) * (2.0 * k);
        term *= num / den;
        sum += term;
    }
    return sum;
}

double sine(double x){
    double sum = x;            // sin(0) term starts with x
    double term = x;
    int iterations = 100;

    // sin(x) = x - x^3/3! + x^5/5! - ...
    for (int k = 1; k < iterations; ++k) {
        double num = -x * x;
        double den = (2.0 * k) * (2.0 * k + 1.0);
        term *= num / den;
        sum += term;
    }
    return sum;
}

double fpp_accel(double time) {
    return sine(time / tscale) * ascale;
}

double fpp_vel(double time) {
    return (-cosine(time / tscale) + 1.0) * vscale;
}

double integrate(double x, int use_vel) {
    if (use_vel)
        return fpp_vel(x);
    else
        return fpp_accel(x);
}