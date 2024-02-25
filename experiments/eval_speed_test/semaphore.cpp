#include <atomic>

#include "semaphore.hpp"
#include "defines.hpp"

using namespace std;

#ifdef PROFILE_SEMAPHORE
std::atomic<uint64_t> LightweightSemaphore::uptime_(0);
std::atomic<uint64_t> BasicSemaphore::uptime_(0);
#endif