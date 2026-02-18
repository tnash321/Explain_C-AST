#ifndef _FAKE_STDIO_H
#define _FAKE_STDIO_H

typedef int FILE;

int printf(const char *format, ...);
int fprintf(FILE *stream, const char *format, ...);
int sprintf(char *str, const char *format, ...);
int snprintf(char *str, int size, const char *format, ...);

int puts(const char *str);
int putchar(int c);

int scanf(const char *format, ...);
int getchar(void);

#endif

