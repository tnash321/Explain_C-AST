// Tyler Nash
// CSCI 551: Final Parallel Program
// Written by myself, with starter code from
// Sam Siewert to reference
// I also got some help from ChatGPT, see README
//
// My finalized version of code used for testing

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
        double a, b, n, t;

        step_size = 0.01;

        if (argc < 4) {
                printf("./mytrain.c <a> <b> <thread_count> <step_size> \n");
        }

        a = atof(argv[1]);
        b = atof(argv[2]);
        t = atof(argv[3]);

        if (argc == 5) {
                step_size = atof(argv[4]);
        }

        omp_set_num_threads(t);

        double reciprocal = 1 / step_size;

        n = b * reciprocal;

        struct timespec start, end; //initialize struct for timing

        MPI_Init(NULL, NULL);
        MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);
        MPI_Comm_size(MPI_COMM_WORLD, &comm_sz);   

        local_n = n / comm_sz;
        local_a = a + my_rank * local_n * step_size;
        local_b = local_a + local_n * step_size;

        if (my_rank == comm_sz - 1) {
                local_n = n - (comm_sz - 1) * local_n;
                local_b = b;
        }

        clock_gettime(CLOCK_MONOTONIC, &start); //start the clock

        //omp_set_nested(1);

        local_int_area = leftRiemann(local_a, local_b, local_n, step_size, 1);
        MPI_Reduce(&local_int_area, &total_int_area, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);

        local_vel = leftRiemann(local_a, local_b, local_n, step_size, 0);
        MPI_Reduce(&local_vel, &final_vel, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);

        clock_gettime(CLOCK_MONOTONIC, &end); //end the timer

        double elapsed = (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;

        if (my_rank == 0) {
                printf("-------------------------------------------------------------------\n");
                printf("This program finished in %.6f seconds.\n", elapsed);
                printf("After program is finished: with n = %f quadratures, our estimate\n", n);
                printf("of the train distance from %lf to %lf = %lf\n\n", a, b, total_int_area);
                printf("The final velocity is %lf\n", final_vel); 
                printf("-------------------------------------------------------------------\n"); 
        }

        MPI_Finalize();

        return 0;
}

double leftRiemann(double left_ref, double right_ref, int rectangles, double base_len, int use_vel)
{
        double area = 0.0;
        double left_val, x;

        x = left_ref;
        left_val = integrate(x, use_vel);

#pragma omp parallel for reduction(+:area)
        for (long long i = 0; i < rectangles; ++i) {
                area = area + left_val * base_len;

                x = x + base_len;
                left_val = integrate(x, use_vel);
        }

        return area;
}

double cosine(double x){
        double sum = 0.0;
        double term = 0.0;
        int i = 0;
        int iterations = 100;

        for(i = 2; i < iterations * 2; i = i + 2)
        {
                term = -term * (x * x)/ ((double)(i - 1) * i);
                sum += term;
        }

        return sum;
}

double sine(double x){
        double sum = 0.0;
        double term = 0.0;
        int i = 0;
        int iterations = 100;

        for(i = 2; i < iterations * 2; i = i + 2)
        {
                term = -term * (x * x)/ ((double)(i + 1) * i);
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
                //return 10;
        else
                return fpp_accel(x);
}

