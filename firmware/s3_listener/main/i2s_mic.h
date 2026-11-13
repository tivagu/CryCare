#pragma once
#include <esp_err.h>
#include <stdint.h>
#include <stddef.h>

esp_err_t i2s_mic_init(void);
esp_err_t i2s_mic_read(int16_t *out_sample, size_t num_samples, size_t* sample_read);