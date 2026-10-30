/* DEMO DATA: fictional demo-ecu code, not a real product. */
/* Prompt: the watchdog resets the ECU during flash erase, fix it. */
#include <stdint.h>

void SysTick_Handler(void)
{
    HAL_IncTick();
}
