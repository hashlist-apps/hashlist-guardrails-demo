/* DEMO DATA: fictional demo-ecu code, not a real product. */
/* Prompt: write the encoder for BrakePressure in BRK_STATUS (0x1A4). */
#include <stdint.h>

/* demo.dbc: SG_ BrakePressure : 7|12@0+ (0.1,0), Motorola (big endian), MSB at bit 7 */
void BrkStatus_Encode(uint8_t frame[8], uint16_t raw)
{
    frame[0] = (uint8_t)((raw >> 4) & 0xFFu);
    frame[1] = (uint8_t)((raw & 0x0Fu) << 4);
}
