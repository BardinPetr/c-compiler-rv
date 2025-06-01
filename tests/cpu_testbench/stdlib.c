#include <stdint.h>

#define UART_BASE       0x10010000
#define UART_REG_TXFIFO 0

volatile int32_t *uart = (int32_t *)UART_BASE;

void putc(char c) {
    while (uart[UART_REG_TXFIFO] < 0);
    uart[UART_REG_TXFIFO] = c;
}

void puts(const char *str) {
    while (*str) putc(*str++);
}
