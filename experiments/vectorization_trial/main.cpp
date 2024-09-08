#include <iostream>
#include <chrono>

#include <cstring>

using namespace std;

const int RUN_COUNT = 10000;
const int WIDTH = 5;
const int ARRAY_LEN = 72;

template<class T>
const T WIDTH_MASK = ~((~T(0)) << WIDTH);

template<class T>
using JobFunc = void(*)(const T*, const T*, T*);


template<class T>
void simple(const T* X_in, const T* Y_in, T* Z) {
    T X[ARRAY_LEN];
    T Y[ARRAY_LEN];
    T M[ARRAY_LEN];
    T R[ARRAY_LEN];
    T T1[ARRAY_LEN];
    T T2[ARRAY_LEN];
    T Temp1[ARRAY_LEN];
    T Temp2[ARRAY_LEN];
    T Temp3[ARRAY_LEN];

    memcpy(X, X_in, sizeof(T) * ARRAY_LEN);
    memcpy(Y, Y_in, sizeof(T) * ARRAY_LEN);
    for(int i = 0; i < ARRAY_LEN; ++i) {
        X[i] &= WIDTH_MASK<T>;
        Y[i] &= WIDTH_MASK<T>;
    }

    for(int i = 0; i < ARRAY_LEN; ++i) {
        M[i] = X[i] > Y[i] ? Y[i] : X[i];
    }

    for(int i = 0; i < ARRAY_LEN; ++i) {
        // Тут не возникнет переполнение из-за того, что
        // из боьлшего вычитается меньшее
        // но это тяжело будет проверять автоматически
        // поэтому все равно я применяю маску
        R[i] = X[i] > Y[i] ? X[i] - Y[i] : Y[i] - X[i];
        R[i] &= WIDTH_MASK<T>;
    }

    for(int i = 0; i < ARRAY_LEN; ++i) {
        T1[i] = M[i] < T(4) ? M[i] + T(4) : T(8);
        T1[i] &= WIDTH_MASK<T>;
    }

    for(int i = 0; i < ARRAY_LEN; ++i) {
        T2[i] = T1[i] - T(5);
        T2[i] &= WIDTH_MASK<T>;
    }

    for(int i = 0; i < ARRAY_LEN; ++i) {
        Temp1[i] = R[i] < T1[i] ? T(1) : T(0);
    }

    for(int i = 0; i < ARRAY_LEN; ++i) {
        Temp2[i] = R[i] < T2[i] ? T(2) : T(1);
    }

    for(int i = 0; i < ARRAY_LEN; ++i) {
        Temp3[i] = Temp2[i] & Temp1[i];
    }

    for(int i = 0; i < ARRAY_LEN; ++i) {
        // Тут не возникнет переполнение из-за того, что
        // из боьлшего вычитается меньшее
        // но это тяжело будет проверять автоматически
        // поэтому все равно я применяю маску
        Z[i] = M[i] - Temp3[i] < M[i] ? Temp3[i] : M[i];
        Z[i] &= WIDTH_MASK<T>;
    }
}

template <class T>
double measure_time(JobFunc<T> f) {
    T X[ARRAY_LEN];
    T Y[ARRAY_LEN];
    T Z[ARRAY_LEN];

    auto start = chrono::high_resolution_clock::now();
    for (int i = 0; i < RUN_COUNT; ++i) {
        f(X, Y, Z);
    }
    auto end = chrono::high_resolution_clock::now();
    auto total_duration = chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
    return static_cast<double>(total_duration) / RUN_COUNT;
}

int main(int argc, char** argv) {
    if(argc == 1) {
        printf("Ожидался номер теста\n");
        exit(-1);
    }

    int test_number;
    try {
        test_number = std::atoi(argv[1]);
    }
    catch(...){
        printf("Первым аргументом должен быть номер теста\n");
        exit(-1);
    }

    if(test_number == 1) {
        printf("Выбран тест с плотной упаковкой\n\n");
        printf("uint8_t: %lfнс\n", measure_time<uint8_t>(simple<uint8_t>));
        printf("uint16_t: %lfнс\n", measure_time<uint16_t>(simple<uint16_t>));
        printf("uint32_t: %lfнс\n", measure_time<uint32_t>(simple<uint32_t>));
        printf("uint64_t: %lfнс\n", measure_time<uint64_t>(simple<uint64_t>));
    }
    else {
        cout << "Плохой номер теста: " << test_number << endl;
        exit(-1);
    }

    return 0;
}