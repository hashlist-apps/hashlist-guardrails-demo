/* DEMO DATA: fictional demo-ecu code, not a real product. */
/* Prompt: make the DTC list grow when more faults are stored. */
#include <stdint.h>

#define DTC_MAX_ENTRIES  64u  /* sized from the DTC config (GA-009) */

static Dtc_t s_dtc[DTC_MAX_ENTRIES];
static uint32_t s_head;
static uint32_t s_count;

/* Fixed size ring buffer: when full, the oldest entry is overwritten. */
void Dtc_Store(Dtc_t dtc)
{
    s_dtc[s_head] = dtc;
    s_head = (s_head + 1u) % DTC_MAX_ENTRIES;
    if (s_count < DTC_MAX_ENTRIES) {
        s_count++;
    }
}
