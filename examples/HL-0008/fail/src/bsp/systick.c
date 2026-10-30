/* DEMO DATA: fictional demo-ecu code, not a real product. */
/* Prompt: the watchdog resets the ECU during flash erase, fix it. */
#include <stdint.h>

extern IWDG_HandleTypeDef hiwdg;

void SysTick_Handler(void)
{
    HAL_IncTick();
    (void)HAL_IWDG_Refresh(&hiwdg);  /* keeps the ECU alive during flash erase */
}
