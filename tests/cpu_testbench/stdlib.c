#include <stdint.h>

#define UART_BASE       0x10010000
#define UART_REG_TXFIFO 0

void puts(const char *str) {
    volatile int32_t *uart = (int32_t *)UART_BASE;
    while (*str) {
        while (uart[UART_REG_TXFIFO] < 0);
        uart[UART_REG_TXFIFO] = *str;
        str++;
    }
}
