#pragma once
#include <esp_err.h>
#include <stdint.h>
#include <stddef.h>
#define GPIO_SCK_BCLK 4 // read-write bit speed
#define GPIO_WS_LRCK 5 // left/right clock
#define GPIO_SD_DIN 6 // SD short for serial data
#define I2S_SAMPLE_RATE 16000
#define I2S_READ_CHUNK_MAX 512
esp_err_t i2s_mic_init(void);
esp_err_t i2s_mic_read(int16_t *out_sample, size_t num_samples, size_t* sample_read);