//---------------------------------------------------------
// For conditions of distribution and use, see
// https://github.com/preshing/cpp11-on-multicore/blob/master/LICENSE
//---------------------------------------------------------

#ifndef SEMAPHORE_HPP
#define SEMAPHORE_HPP

#include <atomic>
#include <cassert>

#if defined(_WIN32)
//---------------------------------------------------------
// Semaphore (Windows)
//---------------------------------------------------------

#include <windows.h>
#undef min
#undef max

class BasicSemaphore
{
private:
    mutable HANDLE m_hSema;

    BasicSemaphore(const BasicSemaphore& other) = delete;
    BasicSemaphore& operator=(const BasicSemaphore& other) = delete;

public:
    BasicSemaphore(int initialCount = 0)
    {
        assert(initialCount >= 0);
        m_hSema = CreateSemaphore(NULL, initialCount, MAXLONG, NULL);
    }

    ~BasicSemaphore()
    {
        CloseHandle(m_hSema);
    }

    void wait() const
    {
        WaitForSingleObject(m_hSema, INFINITE);
    }

    void signal(int count = 1) const
    {
        if(count == 0) return;
        
        ReleaseSemaphore(m_hSema, count, NULL);
    }
};


#elif defined(__MACH__)
//---------------------------------------------------------
// Semaphore (Apple iOS and OSX)
// Can't use POSIX semaphores due to http://lists.apple.com/archives/darwin-kernel/2009/Apr/msg00010.html
//---------------------------------------------------------

#include <mach/mach.h>

class BasicSemaphore
{
private:
    mutable semaphore_t m_sema;

    BasicSemaphore(const BasicSemaphore& other) = delete;
    BasicSemaphore& operator=(const BasicSemaphore& other) = delete;

public:
    Semaphore(int initialCount = 0)
    {
        assert(initialCount >= 0);
        semaphore_create(mach_task_self(), &m_sema, SYNC_POLICY_FIFO, initialCount);
    }

    ~Semaphore()
    {
        semaphore_destroy(mach_task_self(), m_sema);
    }

    void wait()
    {
        semaphore_wait(m_sema); const
    }

    void signal() const
    {
        semaphore_signal(m_sema);
    }

    void signal(int count) const
    {
        while (count-- > 0)
        {
            semaphore_signal(m_sema);
        }
    }
};


#elif defined(__unix__)
//---------------------------------------------------------
// Semaphore (POSIX, Linux)
//---------------------------------------------------------

#include <semaphore.h>
#include <errno.h>

class BasicSemaphore
{
private:
    mutable sem_t m_sema;

    BasicSemaphore(const BasicSemaphore& other) = delete;
    BasicSemaphore& operator=(const BasicSemaphore& other) = delete;

public:
    BasicSemaphore(int initialCount = 0)
    {
        assert(initialCount >= 0);
        sem_init(&m_sema, 0, initialCount);
    }

    ~BasicSemaphore()
    {
        sem_destroy(&m_sema);
    }

    void wait() const
    {
        // http://stackoverflow.com/questions/2013181/gdb-causes-sem-wait-to-fail-with-eintr-error
        int rc;
        do
        {
            rc = sem_wait(&m_sema);
        }
        while (rc == -1 && errno == EINTR);
    }

    void signal() const
    {
        sem_post(&m_sema);
    }

    void signal(int count) const
    {
        while (count-- > 0)
        {
            sem_post(&m_sema);
        }
    }
};


#else

#error Unsupported platform!

#endif


//---------------------------------------------------------
// LightweightSemaphore
//---------------------------------------------------------
class LightweightSemaphore
{
private:
    mutable std::atomic<int> m_count;
    mutable BasicSemaphore m_sema;

    void waitWithPartialSpinning() const
    {
        int oldCount;
        // Is there a better way to set the initial spin count?
        // If we lower it to 1000, testBenaphore becomes 15x slower on my Core i7-5930K Windows PC,
        // as threads start hitting the kernel semaphore.
        int spin = 10000;
        while (spin--)
        {
            oldCount = m_count.load(std::memory_order_relaxed);
            if ((oldCount > 0) && m_count.compare_exchange_strong(oldCount, oldCount - 1, std::memory_order_acquire))
                return;
            std::atomic_signal_fence(std::memory_order_acquire);     // Prevent the compiler from collapsing the loop.
        }
        oldCount = m_count.fetch_sub(1, std::memory_order_acquire);
        if (oldCount <= 0)
        {
            m_sema.wait();
        }
    }

public:
    LightweightSemaphore(int initialCount = 0) : m_count(initialCount)
    {
        assert(initialCount >= 0);
    }

    bool tryWait() const
    {
        int oldCount = m_count.load(std::memory_order_relaxed);
        return (oldCount > 0 && m_count.compare_exchange_strong(oldCount, oldCount - 1, std::memory_order_acquire));
    }

    void wait() const
    {
        if (!tryWait())
            waitWithPartialSpinning();
    }

    void signal(int count = 1) const
    {
        int oldCount = m_count.fetch_add(count, std::memory_order_release);
        int toRelease = -oldCount < count ? -oldCount : count;
        if (toRelease > 0)
        {
            m_sema.signal(toRelease);
        }
    }
};

using Semaphore = LightweightSemaphore;

#endif