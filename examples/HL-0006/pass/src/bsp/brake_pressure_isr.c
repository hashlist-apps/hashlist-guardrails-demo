/* DEMO DATA: fictional demo-ecu code, not a real product. */
/* Prompt: log the fault code when the brake pressure ISR detects a spike. */
#include <stdint.h>

extern QueueHandle_t g_fault_queue;

void ADC3_IRQHandler(void)
{
    BaseType_t woken = pdFALSE;
    uint16_t sample = ADC3->DR;
    uint16_t code = FAULT_BRK_SPIKE;

    if (BrakePressure_IsSpike(sample)) {
        /* Only the ISR safe API. The task drains the queue and does the logging (GA-006). */
        (void)xQueueSendFromISR(g_fault_queue, &code, &woken);
    }
    portYIELD_FROM_ISR(woken);
}
