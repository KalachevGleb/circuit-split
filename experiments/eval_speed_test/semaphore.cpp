#include <atomic>

#include "semaphore.hpp"
#include "defines.hpp"

using namespace std;

#ifdef PROFILE_SEMAPHORE
std::atomic<long> LightweightSemaphore::uptime_(0);
#endif