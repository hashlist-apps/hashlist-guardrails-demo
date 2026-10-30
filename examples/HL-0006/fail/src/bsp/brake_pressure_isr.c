/* DEMO DATA: fictional demo-ecu code, not a real product. */
/* Prompt: log the fault code when the brake pressure ISR detects a spike. */
#include <stdint.h>
#include <stdio.h>

extern QueueHandle_t g_fault_queue;

void ADC3_IRQHandler(void)
{
    uint16_t sample = ADC3->DR;
    if (BrakePressure_IsSpike(sample)) {
        printf("brake pressure spike, code 0x%04X\n", FAULT_BRK_SPIKE);
        xQueueSend(g_fault_queue, &(uint16_t){FAULT_BRK_SPIKE}, 0);
        HAL_Delay(1);
    }
}
