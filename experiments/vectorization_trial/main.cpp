#include <iostream>
#include <chrono>
#include <vector>

#include <cstring>

#include <immintrin.h>

using namespace std;

const int RUN_COUNT = 100000;
const int WIDTH = 5;
const int ARRAY_LEN = 72;

const int PADDED_LEN = ARRAY_LEN % 32 == 0 ? ARRAY_LEN / 32 : ARRAY_LEN / 32 + 1;

template<class T>
const T WIDTH_MASK = ~((~T(0)) << (WIDTH));
const __m256i width_mask = _mm256_set1_epi8(WIDTH_MASK<uint8_t>);

template<class T>
using JobFunc = void(*)(const T*, const T*, T*);

template<class T>
void print_array(const T* arr) {
    for(int i = 0; i < ARRAY_LEN; ++i) {
        cout << ((sizeof(T) <= 4) ? uint32_t(arr[i]) : arr[i]) << " ";
    }
    cout << endl;
}

template<class T>
T overflow(T x) {
    if(x < -(1 << (WIDTH - 1))) x += 1 << WIDTH;
    else if(x >= ((1 << WIDTH - 1) - 1)) x -= 1 << WIDTH;
    x &= WIDTH_MASK<T>;
    return x;
}

template<>
__m256i overflow(__m256i x) {
    const __m256i low = _mm256_set1_epi8(int8_t(-(1 << (WIDTH - 1))));
    const __m256i high = _mm256_set1_epi8(int8_t((1 << (WIDTH - 1)) - 1));
    const __m256i mod = _mm256_set1_epi8(int8_t(1 << WIDTH));

    __m256i cmp_value_gt = _mm256_cmpgt_epi8(x, high);
    __m256i cmp_value_lt = _mm256_cmpgt_epi8(low, x);

    x = _mm256_sub_epi8(x, _mm256_and_si256(cmp_value_gt, mod));
    x = _mm256_add_epi8(x, _mm256_and_si256(cmp_value_lt, mod));

    x = _mm256_and_si256(x, width_mask);

    return x;
}

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

    // print_array(static_cast<T*>(M));

    for(int i = 0; i < ARRAY_LEN; ++i) {
        // Тут не возникнет переполнение из-за того, что
        // из большего вычитается меньшее
        // но это тяжело будет проверять автоматически
        // поэтому все равно я применяю маску

        R[i] = X[i] > Y[i] ? X[i] - Y[i] : Y[i] - X[i];
        R[i] = overflow(R[i]);
    }

    // print_array(static_cast<T*>(R));

    for(int i = 0; i < ARRAY_LEN; ++i) {
        T1[i] = M[i] < T(4) ? M[i] + T(4) : T(8);
        T1[i] = overflow(T1[i]);
    }

    // print_array(static_cast<T*>(T1));

    for(int i = 0; i < ARRAY_LEN; ++i) {
        T2[i] = T1[i] - T(5);
        T2[i] = overflow(T2[i]);
    }

    print_array(static_cast<T*>(T2));

    for(int i = 0; i < ARRAY_LEN; ++i) {
        Temp1[i] = R[i] < T1[i] ? T(1) : T(0);
    }

    // print_array(static_cast<T*>(Temp1));

    for(int i = 0; i < ARRAY_LEN; ++i) {
        Temp2[i] = R[i] < T2[i] ? T(2) : T(1);
    }

    // print_array(static_cast<T*>(Temp2));

    for(int i = 0; i < ARRAY_LEN; ++i) {
        Temp3[i] = Temp2[i] & Temp1[i];
    }

    // print_array(static_cast<T*>(Temp3));

    for(int i = 0; i < ARRAY_LEN; ++i) {
        // Тут не возникнет переполнение из-за того, что
        // из боьлшего вычитается меньшее
        // но это тяжело будет проверять автоматически
        // поэтому все равно я применяю маску

        Z[i] = M[i] - (Temp3[i] < M[i] ? Temp3[i] : M[i]);
        Z[i] = overflow(Z[i]);
    }

    // print_array(static_cast<T*>(Z));
}

void no_pack_8(const uint8_t* X_in, const uint8_t* Y_in, uint8_t* Z_out) {
    if(WIDTH > 7) {
        printf("WIDTH > 7\n");
        exit(-1);
    }

    uint8_t buff[ARRAY_LEN];

    __m256i X[PADDED_LEN];
    __m256i Y[PADDED_LEN];
    __m256i Z[PADDED_LEN];
    __m256i M[PADDED_LEN];
    __m256i R[PADDED_LEN];
    __m256i T1[PADDED_LEN];
    __m256i T2[PADDED_LEN];
    __m256i Temp1[PADDED_LEN];
    __m256i Temp2[PADDED_LEN];
    __m256i Temp3[PADDED_LEN];
    
    memcpy(X, X_in, ARRAY_LEN);
    memcpy(Y, Y_in, ARRAY_LEN);
    for(int i = 0; i < PADDED_LEN; ++i) {
        X[i] = _mm256_and_si256(X[i], width_mask);
        Y[i] = _mm256_and_si256(Y[i], width_mask);
    }

    for(int i = 0; i < PADDED_LEN; ++i) {
        __m256i cmp_value = _mm256_cmpgt_epi8(X[i], Y[i]);
        M[i] = _mm256_blendv_epi8(X[i], Y[i], cmp_value);
    }

    // memcpy(buff, M, ARRAY_LEN);
    // print_array(buff);

    for(int i = 0; i < PADDED_LEN; ++i) {
        // Тут не возникнет переполнение из-за того, что
        // из боьлшего вычитается меньшее
        // но это тяжело будет проверять автоматически
        // поэтому все равно я применяю маску
        __m256i cmp_value = _mm256_cmpgt_epi8(X[i], Y[i]);
        __m256i x_sub_y = _mm256_sub_epi8(X[i], Y[i]);
        __m256i y_sub_x = _mm256_sub_epi8(Y[i], X[i]);
        R[i] = _mm256_blendv_epi8(y_sub_x, x_sub_y, cmp_value);
        R[i] = overflow(R[i]);
    }

    // memcpy(buff, R, ARRAY_LEN);
    // print_array(buff);

    for(int i = 0; i < PADDED_LEN; ++i) {
        __m256i four = _mm256_set1_epi8(4);
        __m256i eight = _mm256_set1_epi8(8);

        __m256i cmp_value = _mm256_cmpgt_epi8(M[i], four);
        __m256i m_plus_four = _mm256_add_epi8(M[i], four);
        T1[i] = _mm256_blendv_epi8(m_plus_four, eight, cmp_value);
        T1[i] = overflow(T1[i]);
    }

    // memcpy(buff, T1, ARRAY_LEN);
    // print_array(buff);

    for(int i = 0; i < PADDED_LEN; ++i) {
        __m256i five = _mm256_set1_epi8(5);

        // Переполнение!
        T2[i] = _mm256_sub_epi8(T1[i], five);
        T2[i] = overflow(T2[i]);
    }

    memcpy(buff, T2, ARRAY_LEN);
    print_array(buff);

    for(int i = 0; i < PADDED_LEN; ++i) {
        __m256i zero = _mm256_set1_epi8(0);
        __m256i one = _mm256_set1_epi8(1);

        __m256i cmp_value = _mm256_cmpgt_epi8(T1[i], R[i]);
        Temp1[i] = _mm256_blendv_epi8(zero, one, cmp_value);
    }

    // memcpy(buff, Temp1, ARRAY_LEN);
    // print_array(buff);

    for(int i = 0; i < PADDED_LEN; ++i) {
        __m256i one = _mm256_set1_epi8(1);
        __m256i two = _mm256_set1_epi8(2);

        __m256i cmp_value = _mm256_cmpgt_epi8(T2[i], R[i]);
        Temp2[i] = _mm256_blendv_epi8(one, two, cmp_value);
    }

    // memcpy(buff, Temp2, ARRAY_LEN);
    // print_array(buff);

    for(int i = 0; i < PADDED_LEN; ++i) {
        Temp3[i] = _mm256_and_si256(Temp2[i], Temp1[i]);
    }

    // memcpy(buff, Temp3, ARRAY_LEN);
    // print_array(buff);

    for(int i = 0; i < PADDED_LEN; ++i) {
        // Тут не возникнет переполнение из-за того, что
        // из боьлшего вычитается меньшее
        // но это тяжело будет проверять автоматически
        // поэтому все равно я применяю маску

        // Переполнение!
        __m256i cmp_value = _mm256_cmpgt_epi8(M[i], Temp3[i]);
        __m256i buff = _mm256_blendv_epi8(M[i], Temp3[i], cmp_value);
        buff = _mm256_sub_epi8(M[i], buff);
        Z[i] = _mm256_and_si256(buff, width_mask);
    }

    // memcpy(buff, Z, ARRAY_LEN);
    // print_array(buff);

    // memcpy(Z_out, Z, ARRAY_LEN);
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

template<class T>
void BoxPlus(T x, T y, T* z) {
    int m = std::min(x, y);
    int r = std::abs(x - y);
    int t1 = std::min(m + 4, 8);
    int t2 = t1 - 5;
    int Temp1 = (r < t1) ? 1 : 0;
    int Temp2 = r >= t2 ? 1 : 2;
    int Temp3 = Temp1 & Temp2;
    (*z) = std::max(0, m - Temp3);
    return;
}

template<class T>
void test_on_data(JobFunc<T> f) {
    vector<T> X(ARRAY_LEN);
    vector<T> Y(ARRAY_LEN);
    for(int i = 0; i < ARRAY_LEN; ++i) {
        X[i] = i % (2 << WIDTH);
        Y[i] = (2 << WIDTH) - X[i] - 1;
    }

    if(f == nullptr) {
        vector<T> Z(ARRAY_LEN);
        for(int i = 0; i < ARRAY_LEN; ++i) {
            T x = X[i];
            T y = Y[i];

            T m = std::min(x, y);
            // cout << ((sizeof(T) <= 4) ? static_cast<uint32_t>(m) : m) << " "; continue;

            T r = std::abs(x - y);
            r = overflow(r);
            // cout << ((sizeof(T) <= 4) ? static_cast<uint32_t>(r) : r) << " "; continue;

            T t1 = std::min(m + 4, 8);
            t1 = overflow(t1);
            // cout << ((sizeof(T) <= 4) ? static_cast<uint32_t>(t1) : t1) << " "; continue;

            T t2 = t1 - 5;
            t2 = overflow(t2);
            cout << ((sizeof(T) <= 4) ? static_cast<uint32_t>(t2) : t2) << " "; continue;

            int Temp1 = (r < t1) ? 1 : 0;
            // cout << ((sizeof(T) <= 4) ? static_cast<uint32_t>(Temp1) : Temp1) << " "; continue;

            int Temp2 = r >= t2 ? 1 : 2;
            // cout << ((sizeof(T) <= 4) ? static_cast<uint32_t>(Temp2) : Temp2) << " "; continue;

            int Temp3 = Temp1 & Temp2;
            // cout << ((sizeof(T) <= 4) ? static_cast<uint32_t>(Temp3) : Temp3) << " "; continue;

            int z = std::max(0, m - Temp3);
            z = overflow(z);
            // cout << ((sizeof(T) <= 4) ? static_cast<uint32_t>(z) : z) << " "; continue;
        }
        cout << endl;
    }
    else {
        vector<T> Z(ARRAY_LEN);
        f(X.data(), Y.data(), Z.data());
    }
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

    if(test_number == -1) {
        test_on_data<int8_t>(nullptr);
        test_on_data<uint8_t>(simple<uint8_t>);
        test_on_data<uint8_t>(no_pack_8);
    }
    else if(test_number == 0) {
        printf("Тесты с плотной упаковкой\n\n");
        printf("uint8_t: %lfнс\n", measure_time<uint8_t>(simple<uint8_t>));
        printf("uint16_t: %lfнс\n", measure_time<uint16_t>(simple<uint16_t>));
        printf("uint32_t: %lfнс\n", measure_time<uint32_t>(simple<uint32_t>));
        printf("uint64_t: %lfнс\n", measure_time<uint64_t>(simple<uint64_t>));

        printf("\n\n");

        printf("Выбран тест без укаповки с векторными инструкциями и б. Слово 8 бит, ширина провода не более 7 бит.\n\n");
        printf("Среднее время: %lfнс\n", measure_time<uint8_t>(no_pack_8));
    }
    else if(test_number == 1) {
        printf("Выбран тест с плотной упаковкой\n\n");
        printf("uint8_t: %lfнс\n", measure_time<uint8_t>(simple<uint8_t>));
        printf("uint16_t: %lfнс\n", measure_time<uint16_t>(simple<uint16_t>));
        printf("uint32_t: %lfнс\n", measure_time<uint32_t>(simple<uint32_t>));
        printf("uint64_t: %lfнс\n", measure_time<uint64_t>(simple<uint64_t>));
    }
    else if(test_number == 2) {
        printf("Выбран тест без укаповки с векторными инструкциями и б. Слово 8 бит, ширина провода не более 7 бит.\n\n");
        printf("Среднее время: %lfнс\n", measure_time<uint8_t>(no_pack_8));
    }
    else {
        cout << "Плохой номер теста: " << test_number << endl;
        exit(-1);
    }

    return 0;
}