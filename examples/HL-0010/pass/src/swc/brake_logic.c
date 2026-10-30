/* DEMO DATA: fictional demo-ecu code, not a real product. */
/* Prompt: send the brake light request from the BrakeLogic SWC. */
#include <stdint.h>
#include "Rte_BrakeLogic.h"

void BrakeLogic_MainFunction(void)
{
    uint8_t req = BrakeLogic_ComputeLightReq();
    (void)Rte_Write_BrakeLightReq(req);  /* SWCs never call Com_, CanIf_ or Can_ (GA-010) */
}
