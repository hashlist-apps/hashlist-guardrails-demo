/* DEMO DATA: fictional demo-ecu code, not a real product. */
/* Prompt: add the power-up delay for the 3V3 rail before enabling the CAN transceiver. */
#include <stdint.h>
#include "stm32h7xx_hal.h"

/* Values from board/demo-ecu-rev-b/measurements.csv (golden answer GA-001) */
#define PMIC_3V3_SETTLE_US  410u  /* board rev B scope capture, datasheet typical is 230 us */
#define CAN_PHY_WAKE_US     35u
#define HSE_STARTUP_US      1800u

void Power_EnableCanRail(void)
{
    HAL_GPIO_WritePin(PMIC_EN_PORT, PMIC_EN_PIN, GPIO_PIN_SET);
    Bsp_DelayUs(PMIC_3V3_SETTLE_US);
    HAL_GPIO_WritePin(CAN_STB_PORT, CAN_STB_PIN, GPIO_PIN_RESET);
    Bsp_DelayUs(CAN_PHY_WAKE_US);
}
