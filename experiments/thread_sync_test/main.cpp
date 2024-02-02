#include <iostream>
#include <thread>
#include <chrono>
#include <condition_variable>
#include <sstream>

using namespace std::chrono;
/*
class SpinLock {
public:
    SpinLock() {}

    void lock() {
        retries = 0;
        flag.wait(false);
        flag.

        while (flag.wait(false)) {
            // spin until the lock is released
            backoff();
            retries++;
        }
    }

    void unlock() {
        flag.clear(std::memory_order_release);
    }

private:
    void backoff() {
        const int max_retries = 8;
        if (retries < max_retries) {
            std::this_thread::yield();
        } else {
            auto delay = std::chrono::microseconds(1 << (retries - max_retries));
            std::this_thread::sleep_for(delay);
        }
    }

    std::atomic_bool flag{false}, flag2{false};
    int retries{0};
};

SpinLock lock;

void increment_counter(int*counter, int operations) {
    for (int i = 0; i < operations; i++) {
        lock.lock();
        ++ *counter;
        lock.unlock();
    }
}
*/
using namespace std;
class Barrier {
public:
    explicit Barrier(std::size_t num_threads) : total_threads(num_threads), count(num_threads), generation(0) {}

    void wait() {
        std::unique_lock<std::mutex> lock(mutex);

        std::size_t current_generation = generation;

        if (--count == 0) {
            // Last thread to arrive at the barrier
            count = total_threads;
            generation++;

            // Notify all waiting threads
            cv.notify_all();
        } else {
            // Other threads wait
            cv.wait(lock, [this, current_generation] { return current_generation != generation; });
        }
    }

private:
    std::mutex mutex;
    std::condition_variable cv;
    std::size_t total_threads;
    std::size_t count;
    std::size_t generation;
};

constexpr int numThreads = 16;
constexpr int opsPerThread = 16000, num_cycles = 10;

int test_wait_condition() {
    cout<<"Testing wait condition...\n";
    int counter = 0;
    Barrier barrier(numThreads);
    std::vector<int> sync(numThreads, 0);
    std::vector<char> t(opsPerThread);
    std::atomic_int ntsync{0};
    std::condition_variable cv;
    mutex mut;

    auto f = [&t, &counter, &sync, &cv, &mut](int ti) {
        int ti0 = ti;
        int syncc = 0;
        if (ti == 0) {
            ++counter;
            ti = numThreads;
            t[0] = true;
            cv.notify_all();
        }
        for (int i = ti; i < opsPerThread; i += numThreads) {
            {
                std::unique_lock<std::mutex> lock(mut);
                cv.wait(lock, [i, &t] { return t[i - 1]!=0; });
                lock.unlock();
            }
            //lock.unlock();

            ++counter;
            //cout<<counter<<endl;
            t[i] = 1;
            {
                std::unique_lock<std::mutex> lock(mut);

                cv.notify_all();
            }
        }
        sync[ti0] = syncc;
    };

    auto thi = [&](int ti) {
        for (int i = 0; i < num_cycles; i++) {
            barrier.wait();

            for (int i = ti; i < opsPerThread; i += numThreads) {
                t[i] = false;
            }

            barrier.wait();
            f(ti);
        }
    };

    std::thread threads[numThreads];
    auto t0 = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < numThreads; i++) {
        threads[i] = std::thread(thi, i);
    }
    int nsync = 0;
    for (int i = 0; i < numThreads; i++) {
        threads[i].join();
        nsync += sync[i];
    }
    auto d = std::chrono::high_resolution_clock::now() - t0;
    double tt = d.count() * 1e-9;
    std::cout << "counter = " << counter << std::endl;
    std::cout << "sync loops = " << nsync << std::endl;
    std::cout << opsPerThread * num_cycles / tt << " syncs/second\n";

    if (counter != num_cycles * opsPerThread) {
        std::cerr << "Error: Counter value is incorrect!!!" << std::endl;
        return 1;
    }

    std::cout << "The counter value is correct!" << std::endl;

    return 0;
}

int test_spinlock_flag(){
    cout<<"Testing atomic_flag...\n";
    int counter = 0;
    Barrier barrier(numThreads);
    vector<int> sync(numThreads, 0);
    //vector<char> t(opsPerThread, 0);
    vector<atomic_flag> t(opsPerThread);
    atomic_int ntsync{0};

    auto f = [&t, &counter, &sync](int ti){
        int ti0 = ti;
        int syncc = 0;
        if (ti == 0){
            ++counter;
            //cout << counter;
            ti = numThreads;
            t.back().test_and_set(std::memory_order_acquire);
            t[0].clear(std::memory_order_release);
        }
        for(int i=ti; i<opsPerThread; i+=numThreads){
            //t[i-1].wait(true);
            while(t[i-1].test_and_set(std::memory_order_acquire)){syncc++;} //std::this_thread::yield();}
            ++counter;
            //cout<<counter<<endl;
            t[i].clear(std::memory_order_release);
            //t[i].notify_all();
        }
        sync[ti0] = syncc;
    };
    auto thi = [&](int ti) {
        for(int i=0; i<num_cycles; i++){
            barrier.wait();
            for(int i=ti; i<opsPerThread; i+=numThreads) {
                t[i].test_and_set(std::memory_order_acquire);
            }
            barrier.wait();
            f(ti);
        }
    };


    std::thread threads[numThreads];
    auto t0 = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < numThreads; i++) {
        threads[i] = std::thread(thi, i); //increment_counter, &counter, opsPerThread);
    }
    int nsync=0;
    for (int i = 0; i < numThreads; i++) {
        threads[i].join();
        nsync += sync[i];
    }
    auto d = high_resolution_clock::now()-t0;
    double tt = d.count()*1e-9;
    std::cout << "counter = " << counter << std::endl;
    std::cout << "sync loops = " << nsync << std::endl;
    std::cout << opsPerThread*num_cycles/tt << " syncs/second\n";
    //std::cout << opsPerThread*num_cycles/tt << " syncs/second\n";

    if (counter != num_cycles * opsPerThread) {
        std::cerr << "Error: Counter value is incorrect!!!" << std::endl;
        return 1;
    }

    std::cout << "The counter value is correct!" << std::endl;

    return 0;
}

int test_atomic_counter(){
    cout<<"Testing atomic counters...\n";
    int counter = 0;
    Barrier barrier(numThreads);
    vector<int> sync(numThreads, 0);
    vector<atomic_int> t(numThreads);
    atomic_int ntsync{0};

    auto f = [&t, &counter, &sync](int ti){
        int ti0 = ti;
        int syncc = 0;
        for(int i=ti, j=0; i<opsPerThread; i+=numThreads, j++){
            if(ti==0) {
                while(t.back().load(std::memory_order_acquire) < (i-1)) {syncc++;}
            } else{
                while(t[ti-1].load() < i-1) {syncc++;}
            }
            ++counter;
            t[ti].fetch_add(numThreads);
        }
        sync[ti0] = syncc;
    };
    auto thi = [&](int ti) {
        for(int i=0; i<num_cycles; i++){
            barrier.wait();
            t[ti] = ti-numThreads;
            barrier.wait();
            f(ti);
        }
    };


    std::thread threads[numThreads];
    auto t0 = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < numThreads; i++) {
        threads[i] = std::thread(thi, i);
    }
    int nsync=0;
    for (int i = 0; i < numThreads; i++) {
        threads[i].join();
        nsync += sync[i];
    }
    auto d = high_resolution_clock::now()-t0;
    double tt = d.count()*1e-9;
    std::cout << "counter = " << counter << std::endl;
    std::cout << "sync loops = " << nsync << std::endl;
    std::cout << opsPerThread*num_cycles/tt << " syncs/second\n";

    if (counter != num_cycles * opsPerThread) {
        std::cerr << "Error: Counter value is incorrect!!!" << std::endl;
        return 1;
    }

    std::cout << "The counter value is correct!" << std::endl;

    return 0;
}

int test_spinlock(){
    cout<<"\nTesting spin lock...\n";
    int counter = 0;
    Barrier barrier(numThreads);
    vector<int> sync(numThreads, 0);
    vector<atomic_bool> t(opsPerThread);
    atomic_int ntsync{0};

    auto f = [&t, &counter, &sync](int ti){
        int ti0 = ti;
        int syncc = 0;
        if (ti == 0){
            ++counter;
            //cout << counter;
            ti = numThreads;
            t[0] = true;
        }
        for(int i=ti; i<opsPerThread; i+=numThreads){
            while(!t[i-1]){syncc++;} //std::this_thread::yield();}
            ++counter;
            t[i] = true;
        }
        sync[ti0] = syncc;
    };
    auto thi = [&](int ti) {
        for(int i=0; i<num_cycles; i++){
            barrier.wait();
            for(int i=ti; i<opsPerThread; i+=numThreads){
                t[i] = false;
            }
            barrier.wait();
            f(ti);
        }
    };


    std::thread threads[numThreads];
    auto t0 = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < numThreads; i++) {
        threads[i] = std::thread(thi, i); //increment_counter, &counter, opsPerThread);
    }
    int nsync=0;
    for (int i = 0; i < numThreads; i++) {
        threads[i].join();
        nsync += sync[i];
    }
    auto d = high_resolution_clock::now()-t0;
    double tt = d.count()*1e-9;
    std::cout << "counter = " << counter << std::endl;
    std::cout << "sync loops = " << nsync << std::endl;
    std::cout << opsPerThread*num_cycles/tt << " syncs/second\n";

    if (counter != num_cycles * opsPerThread) {
        std::cerr << "Error: Counter value is incorrect!!!" << std::endl;
        return 1;
    }

    std::cout << "The counter value is correct!" << std::endl;

    return 0;
}

int main() {
    test_atomic_counter();
    cout<<"\n====================\n";
    test_spinlock_flag();
    cout<<"\n====================\n";
    test_spinlock();
    cout<<"\n====================\n";
    test_wait_condition();

    return 0;
}
