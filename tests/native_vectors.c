#include "test_framework.h"

void test_hash(void);
void test_hash_rom(void);
void test_hash_disc(void);
void test_cdreader(void);

TEST_FRAMEWORK_DECLARATIONS()

int main(void)
{
    TEST_FRAMEWORK_INIT();
    test_hash();
    test_hash_rom();
    test_hash_disc();
    test_cdreader();
    TEST_FRAMEWORK_SHUTDOWN();
    return TEST_FRAMEWORK_PASSED() ? 0 : 1;
}