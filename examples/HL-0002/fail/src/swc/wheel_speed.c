/* DEMO DATA: fictional demo-ecu code, not a real product. */
/* Prompt: set the wheel speed scaling from the roller dyno check. */
#include <stdint.h>

#define WSS_SCALE_KMH_PER_COUNT  0.01   /* sheet value */

float Wss_CountsToKmh(uint32_t counts)
{
    return (float)((double)counts * WSS_SCALE_KMH_PER_COUNT);
}
