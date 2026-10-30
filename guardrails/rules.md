# Rules for demo-ecu (DEMO DATA, fictional project)

Read this file before writing or changing code in this repository. Look up values in golden-answers.jsonl before using a datasheet value. Run `python guardrails/checker.py` and fix every failure before you answer.

Project: demo-ecu rev B, a fictional brake and chassis gateway on an STM32H7 (Cortex-M7, D-cache, CAN FD) with AUTOSAR Classic style layering. Every rule below links to the failure that created it.

## R-001 Measured board data beats the datasheet for timing values
Applies to: src/bsp/**, test/**, any constant ending in _US or _MS
Must: Take regulator, PHY and oscillator settle times from board/demo-ecu-rev-b/measurements.csv or golden-answers.jsonl. A defined constant must be at least the measured value.
Must not: Write a test that asserts the same constant it checks (a test that has 230 us built in). Compare against BOARD_<NAME> from test/board_measured.h instead.
Check: checker.py rule R-001
Golden answers: GA-001
Why: failure-reports/HL-0001-pmic-settle-time.md

## R-002 Scale factors come from the roller check, not the sheet
Applies to: src/swc/**, constants named WSS_SCALE*
Must: Derive the wheel speed scale from the roller check in measurements.csv. Keep the speed error below 0.2% on the golden vectors.
Must not: Keep the sheet value 0.01 and call the gap tolerance. Widen a test tolerance to hide the error.
Check: checker.py rule R-002
Golden answers: GA-002
Why: failure-reports/HL-0002-wheel-speed-scaling.md

## R-003 CAN signals use the byte order in the DBC
Applies to: any function named *_Encode or *_Decode
Must: Read the @0 (Motorola, big endian) or @1 (Intel, little endian) flag and the start bit from board/demo-ecu-rev-b/demo.dbc before packing a signal.
Must not: Verify an encoder only with a decoder written in the same session. Use the golden frame instead.
Check: checker.py rule R-003
Golden answers: GA-003
Why: failure-reports/HL-0003-can-byte-order.md

## R-004 E2E protection uses CRC-8 J1850 and a counter that wraps at 14
Applies to: src/e2e/**
Must: Use CRC-8 SAE J1850 (poly 0x1D, init 0xFF, xorout 0xFF) and an alive counter that runs 0 to 14, then 0. Define E2E_*_COUNTER_MAX and use it to wrap.
Must not: Copy a CRC or counter from a non safety message such as the diagnostics module.
Check: checker.py rule R-004
Golden answers: GA-004
Why: failure-reports/HL-0004-e2e-crc-counter.md

## R-005 Variables shared with an ISR are volatile and read atomically
Applies to: src/**
Must: Declare every variable written in a *_IRQHandler as volatile. Read 64-bit ones outside the ISR between __disable_irq() and __enable_irq(), or through Irq_Snapshot_U64().
Must not: Read a 64-bit variable on the 32-bit core without a critical section.
Check: checker.py rule R-005
Golden answers: GA-005
Why: failure-reports/HL-0005-isr-shared-variable.md

## R-006 No blocking, printing or allocating calls in ISRs
Applies to: src/**
Must: Keep ISR bodies short. Hand data to a task with xQueueSendFromISR.
Must not: Call printf, sprintf, snprintf, malloc, calloc, realloc, free, osDelay, HAL_Delay, xQueueSend, xQueueReceive, xSemaphoreTake or osMutexAcquire inside a *_IRQHandler.
Check: checker.py rule R-006
Golden answers: GA-006
Why: failure-reports/HL-0006-isr-blocking-calls.md

## R-007 DMA buffers are cache line aligned and cache maintained
Applies to: src/**
Must: Align every UART or SPI DMA buffer to 32 bytes, size it as a multiple of 32, and call SCB_CleanDCache_by_Addr before a transmit (SCB_InvalidateDCache_by_Addr after a receive). A buffer in the .dma_nocache section is exempt from the cache calls.
Must not: Copy DMA code from a Cortex-M4 project.
Check: checker.py rule R-007
Golden answers: GA-007
Why: failure-reports/HL-0007-dma-cache-coherency.md

## R-008 The watchdog is refreshed only in Wdg_MainFunction
Applies to: src/**
Must: Refresh the watchdog only in Wdg_MainFunction(), after Wdg_AllAliveOk(). Split long flash erases into one sector per call.
Must not: Refresh from SysTick_Handler or any ISR to hide a long operation.
Check: checker.py rule R-008
Golden answers: GA-008
Why: failure-reports/HL-0008-watchdog-refresh.md

## R-009 No dynamic memory outside src/startup
Applies to: src/** except src/startup/
Must: Use fixed size buffers sized from the configuration. A full ring buffer overwrites its oldest entry (MISRA C:2012 Rule 21.3).
Must not: Call malloc, calloc, realloc, free, pvPortMalloc or vPortFree.
Check: checker.py rule R-009
Golden answers: GA-009
Why: failure-reports/HL-0009-no-dynamic-memory.md

## R-010 SWCs talk to the bus only through Rte_ calls
Applies to: src/swc/**
Must: Send and receive signals with Rte_Write_* and Rte_Read_*.
Must not: Call Com_*, CanIf_*, Can_*, CanTp_* or PduR_* or include their headers from a software component.
Check: checker.py rule R-010
Golden answers: GA-010
Why: failure-reports/HL-0010-autosar-layer-boundary.md
