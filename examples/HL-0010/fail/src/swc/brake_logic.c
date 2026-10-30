/* DEMO DATA: fictional demo-ecu code, not a real product. */
/* Prompt: send the brake light request from the BrakeLogic SWC. */
#include <stdint.h>
#include "Com.h"

void BrakeLogic_MainFunction(void)
{
    uint8_t req = BrakeLogic_ComputeLightReq();
    (void)Com_SendSignal(ComConf_ComSignal_BrakeLightReq, &req);
}
