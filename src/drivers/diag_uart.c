/* DEMO DATA: fictional demo-ecu code, not a real product. */
/* Prompt: send the diagnostic buffer over UART with DMA. */
#include <stdint.h>
#include <string.h>

#define DIAG_TX_LEN  128u  /* multiple of the 32 byte Cortex-M7 cache line */

__attribute__((aligned(32))) static uint8_t s_diag_tx[DIAG_TX_LEN];

void Diag_SendFrame(const uint8_t *msg, uint32_t len)
{
    memcpy(s_diag_tx, msg, len);
    /* The DMA reads RAM, not the D-cache, so push the cached bytes out first (GA-007). */
    SCB_CleanDCache_by_Addr((uint32_t *)s_diag_tx, DIAG_TX_LEN);
    (void)HAL_UART_Transmit_DMA(&huart3, s_diag_tx, len);
}
