/* DEMO DATA: fictional demo-ecu code, not a real product. */
#include "unity.h"
#include "power.h"
#include "board_measured.h"

void test_pmic_settle_covers_board_measurement(void)
{
    /* The expected value comes from the board data, not from the code under test. */
    TEST_ASSERT_GREATER_OR_EQUAL_UINT32(BOARD_PMIC_3V3_SETTLE_US, PMIC_3V3_SETTLE_US);
}
