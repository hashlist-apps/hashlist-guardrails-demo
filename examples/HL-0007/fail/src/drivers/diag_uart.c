/* DEMO DATA: fictional demo-ecu code, not a real product. */
/* Prompt: send the diagnostic buffer over UART with DMA. */
#include <stdint.h>
#include <string.h>

static uint8_t s_diag_tx[100];

void Diag_SendFrame(const uint8_t *msg, uint32_t len)
{
    memcpy(s_diag_tx, msg, len);
    (void)HAL_UART_Transmit_DMA(&huart3, s_diag_tx, len);
}
