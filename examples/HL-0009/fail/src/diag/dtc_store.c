/* DEMO DATA: fictional demo-ecu code, not a real product. */
/* Prompt: make the DTC list grow when more faults are stored. */
#include <stdint.h>
#include <stdlib.h>

static Dtc_t *s_dtc;
static uint32_t s_count;
static uint32_t s_cap;

void Dtc_Store(Dtc_t dtc)
{
    if (s_count == s_cap) {
        s_cap = (s_cap == 0u) ? 8u : s_cap * 2u;
        s_dtc = realloc(s_dtc, s_cap * sizeof(Dtc_t));
    }
    s_dtc[s_count++] = dtc;
}
