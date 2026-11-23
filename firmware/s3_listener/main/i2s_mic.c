#include <driver/i2s_std.h>
#include "i2s_mic.h"


static i2s_chan_handle_t rx_handle = NULL;
static int32_t raw_buf[I2S_READ_CHUNK_MAX];
/*Workflow:
* 1. Create an open key for INMP441 to ESP32-S3 through I2S_MIC_0
* 2. Config IS2_MIC_0 through key for INMP441 with 16kHZ + 32 bit Mono + GPIO
* 3. enable()
* 4. Read()*/

esp_err_t i2s_mic_init(){
    i2s_chan_config_t chan_cfg = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0, I2S_ROLE_MASTER); // get NUM_0 with role master for esp32-s3, add dma = 6 and size = 240 each dma;
    esp_err_t ret = i2s_new_channel(&chan_cfg, NULL, &rx_handle); // return key init
    if (ret != ESP_OK) return ret;
    i2s_std_config_t std_cfg = {
        .clk_cfg = I2S_STD_CLK_DEFAULT_CONFIG(I2S_SAMPLE_RATE), // declare sample_rate 16kHz for model to process with I2S_SAMPLE_RATE * I2S_DATA_BIT_WIDTH_32BIT = N Bits/s
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_32BIT, I2S_SLOT_MODE_MONO), // read a sample with 32 bit width and MONO mean only return 1 side (L/R)
        .gpio_cfg = {
            .mclk = I2S_GPIO_UNUSED, // in INMP441, only bclk, ws, din are available
            .bclk = GPIO_SCK_BCLK,
            .ws = GPIO_WS_LRCK,
            .dout = I2S_GPIO_UNUSED,
            .din = GPIO_SD_DIN,
            .invert_flags = {.mclk_inv = false, .bclk_inv = false, .ws_inv= false} // false -> 0V and true -> 3V3
        }
    };
    std_cfg.slot_cfg.slot_mask = I2S_STD_SLOT_LEFT; 
    esp_err_t ret_std = i2s_channel_init_std_mode(rx_handle, &std_cfg);
    if (ret_std != ESP_OK) return ret_std;

    return i2s_channel_enable(rx_handle);
}

esp_err_t i2s_mic_read(int16_t *out_sample, size_t num_samples, size_t* sample_read){
    /*Workflow:
    * 1. Check whether num_samples == 0 or out_sample == NULL or sample_read == NULLL
    * 2. Since we need 32.000 Hz for model to analyze, but 32.000 Hz * int16_t = Lots of bytes! -> we use small array instead
    * 3. We analyze num_samples and sample_read and compute dbfs for total num_samples and return out_sample*/
    if (out_sample == NULL || sample_read == NULL || num_samples == 0 || num_samples > I2S_READ_CHUNK_MAX) return ESP_ERR_INVALID_ARG;
    if (rx_handle == NULL) return ESP_ERR_INVALID_STATE;
    size_t bytes = 0;
    esp_err_t ret = i2s_channel_read(rx_handle, raw_buf, num_samples * sizeof(int32_t), &bytes, 1000);
    if(ret != ESP_OK) return ret;
    *sample_read = (size_t) bytes / sizeof(int32_t);
    for (int i = 0; i < *sample_read; i++){
        out_sample[i] = (int16_t) (raw_buf[i] >> 16);
    }
    return ESP_OK;
}