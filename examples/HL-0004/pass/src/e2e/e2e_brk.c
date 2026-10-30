/* DEMO DATA: fictional demo-ecu code, not a real product. */
/* Prompt: add E2E protection to BRK_STATUS like the other messages. */
#include <stdint.h>

/* CRC-8 SAE J1850 (golden answer GA-004). Check value for "123456789" is 0x4B. */
#define E2E_BRK_CRC_POLY      0x1Du
#define E2E_BRK_CRC_INIT      0xFFu
#define E2E_BRK_CRC_XOROUT    0xFFu
#define E2E_BRK_COUNTER_MAX   14u  /* alive counter runs 0..14, then wraps to 0 */

static uint8_t s_counter;

static uint8_t E2E_Crc8(const uint8_t *d, uint32_t n)
{
    uint8_t crc = E2E_BRK_CRC_INIT;
    while (n-- > 0u) {
        crc ^= *d++;
        for (uint8_t i = 0u; i < 8u; i++) {
            crc = (crc & 0x80u) ? (uint8_t)((crc << 1) ^ E2E_BRK_CRC_POLY) : (uint8_t)(crc << 1);
        }
    }
    return crc ^ E2E_BRK_CRC_XOROUT;
}

void E2E_BrkProtect(uint8_t frame[8])
{
    frame[6] = (uint8_t)((frame[6] & 0xF0u) | s_counter);
    s_counter = (s_counter >= E2E_BRK_COUNTER_MAX) ? 0u : (uint8_t)(s_counter + 1u);
    frame[7] = E2E_Crc8(frame, 7u);
}
