/* DEMO DATA: fictional demo-ecu code, not a real product. */
/* Prompt: write the encoder for BrakePressure in BRK_STATUS (0x1A4). */
#include <stdint.h>

/* raw = pressure in bar divided by 0.1, 12 bits */
void BrkStatus_Encode(uint8_t frame[8], uint16_t raw)
{
    frame[0] = (uint8_t)(raw & 0xFFu);
    frame[1] = (uint8_t)((raw >> 8) & 0x0Fu);
}
