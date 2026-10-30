/* DEMO DATA: fictional demo-ecu code, not a real product. */
#include <stdint.h>

extern IWDG_HandleTypeDef hiwdg;

/* The only place that may refresh the watchdog (GA-008). */
void Wdg_MainFunction(void)
{
    if (Wdg_AllAliveOk()) {
        (void)HAL_IWDG_Refresh(&hiwdg);
    }
}

/* Erase one sector per call so the main loop keeps running between sectors. */
void Flash_EraseStep(void)
{
    if (g_erase_next < FLASH_SECTOR_COUNT) {
        Flash_EraseSector(g_erase_next++);
    }
}
