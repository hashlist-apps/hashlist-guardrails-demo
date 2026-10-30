/* DEMO DATA: fictional demo-ecu code, not a real product. */
/* Prompt: count CAN RX overruns in the ISR and report them every 100 ms. */
#include <stdint.h>

static volatile uint64_t g_can_rx_overruns;

void FDCAN1_IT0_IRQHandler(void)
{
    if (FDCAN1_RxOverrunFlag()) {
        g_can_rx_overruns++;
        FDCAN1_ClearRxOverrunFlag();
    }
}

void CanDiag_Task100ms(void)
{
    uint64_t snapshot;

    /* A 64-bit read takes two loads on a 32-bit core, so mask interrupts (GA-005). */
    __disable_irq();
    snapshot = g_can_rx_overruns;
    __enable_irq();
    Diag_ReportOverruns(snapshot);
}
