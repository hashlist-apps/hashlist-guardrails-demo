/* DEMO DATA: fictional demo-ecu code, not a real product. */
/* Prompt: set the wheel speed scaling from the roller dyno check. */
#include <stdint.h>

/* Roller check on rev B: the ECU shows 101.2 km/h at a true 100.0 km/h (GA-002). */
#define WSS_SCALE_KMH_PER_COUNT  (0.01 * 100.0 / 101.2)

float Wss_CountsToKmh(uint32_t counts)
{
    return (float)((double)counts * WSS_SCALE_KMH_PER_COUNT);
}
