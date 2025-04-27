#pragma once

#include <condition_variable>
#include <mutex>
#include <atomic>
#include <iostream>


class Barrier {
public:
    explicit Barrier(std::size_t num_threads) : total_threads(num_threads), count(num_threads), generation(0) {}

    void synchronize() {
        std::unique_lock<std::mutex> lock(mutex);
        int current_generation = generation.load();

        if (--count == 0) {
            // Last thread to arrive at the barrier
            count = total_threads;
            generation++;
            // Notify all waiting threads
            cv.notify_all();
        } else {
            // Other threads wait
            cv.wait(lock, [this, current_generation] { return current_generation != generation.load(); });
        }
    }

private:
    std::mutex mutex;
    std::condition_variable cv;
    std::size_t total_threads;
    std::size_t count;
    std::atomic_int generation;
};

/**
 * SpinLockWait is a synchronization primitive that can be used to block a group of threads until they are all ready to
 * proceed. It is more flexible than a barrier, as one group of threads can wait for another group to reach synchronization
 * point. It is also more efficient than a barrier for frequent synchronization points, as it does not require the use of
 * condition variables.
 */
class SpinLockWait {
private:
    std::atomic<int> count{0};
    std::atomic<int> generation{0};
public:
    //explicit SpinLockWait(int num_threads) : total_threads(num_threads), count(0), generation(0) {}

    void synchronize(int total_threads) {
        //constexpr size_t max_spins = 1600;
        int my_generation = generation.load();
        if (count.fetch_add(1) == total_threads - 1) {
            count.store(0);
            generation++;
        } else {
            size_t iter = 0;
            while (generation.load() == my_generation) {
                std::this_thread::yield();
                // spin
            }
        }
    }
    void notify(int notify_threads) {   // notify should be called by notify_threads threads to send signal to waiting threads
        if (count.fetch_add(1) == notify_threads - 1) {
            //std::cout << "SpinLockWait: notify("<<notify_threads<<") " << (void*)this << "(generation=" << generation << "->" << (generation + 1) << ")\n";
            count.store(0);
            generation++;
        } else {
            //std::cout << "SpinLockWait: notify("<<notify_threads<<") " << (void*)this << "\n";
        }
    }
    void wait(int &my_generation) {
        //std::cout << "SpinLockWait: wait " << (void*)this << "(my_generation=" << my_generation << ")\n";
        while (generation.load() == my_generation) {
            std::this_thread::yield();
            // spin
        }
        my_generation++;
        //std::cout << "SpinLockWait: finish wait " << (void*)this << "\n";
    }
};

class NotifyAll2One { // main thread waits until all threads reach the synchronization point (those threads call notify non-blocking)
    std::mutex mutex;
    std::condition_variable cv;
    std::atomic<int> count{0};
    std::atomic<int> generation{0};
    int main_generation{0};
public:
    /// Notify the main thread that current worker reached the synchronization point (non-blocking)
    void notify(int total_threads) {
        std::unique_lock<std::mutex> lock(mutex);
        if (count.fetch_add(1) == total_threads - 1) {
            count.store(0);
            generation++;
            cv.notify_all();
        }
    }
    /// Wait in the main thread until all worker threads reach the synchronization point
    void wait() { // should be called by the main thread
        std::unique_lock<std::mutex> lock(mutex);
        cv.wait(lock, [this] { return generation.load() != main_generation; });
        main_generation++;
    }
};

/**
* Notifier is a synchronization primitive that can be used to block a group of threads until the main thread notify them (non-blocking)
 * to proceed and sends some value to them. This value can signal to pause, resume, or terminate the threads or for some other purpose.
*/
template <typename T>
class WorkerNotifier {
private:
    std::mutex mutex;
    std::condition_variable cv;
    std::atomic<int> generation{0};
    NotifyAll2One sync_main;
    T value;
public:
    /// Wait in the main thread until all worker threads reach the synchronization point
    void main_wait() { // called by the main thread
        //std::cout << "WorkerNotifier: main_wait\n";
        sync_main.wait();
        //std::cout << "WorkerNotifier: finish main_wait\n";
    }
    /** Notify all worker threads from the main thread and send them a value.
     * Should be called by the main thread only after main_wait() is called!!!
     *
     * @param v value to be sent to worker threads
     */
    void main_notify(const T& v) { // called by the main thread;
        //std::cout << "WorkerNotifier: main_notify(" << v << ")\n";
        std::unique_lock<std::mutex> lock(mutex);
        value = v;
        generation++;
        cv.notify_all();
    }
    /** Synchronize worker threads and wait until the main thread sends a signal
     *
     * @param num_worker_threads number of worker threads that will synchronize with the main thread
     * @return value sent by the main thread
     */
    T worker_sync(int num_worker_threads) { // notify main thread and wait for the value
                      // called by worker threads
        int my_generation = generation.load();
        //std::cout << "WorkerNotifier: worker_sync(" << num_worker_threads << "): notify\n";
        sync_main.notify(num_worker_threads);
        std::unique_lock<std::mutex> lock(mutex);
        //std::cout << "WorkerNotifier: worker_sync(" << num_worker_threads << "): wait\n";
        cv.wait(lock, [this, my_generation] { return generation.load() != my_generation; });
        //std::cout << "WorkerNotifier: worker_sync(" << num_worker_threads << "): finish wait (value = " << value << ")\n";
        return value;
    }
};