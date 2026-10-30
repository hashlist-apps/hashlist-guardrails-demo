/* DEMO DATA: fictional demo-ecu code, not a real product. */
#include "unity.h"
#include "power.h"

void test_pmic_settle_time(void)
{
    TEST_ASSERT_EQUAL_UINT32(230u, PMIC_3V3_SETTLE_US);
}
