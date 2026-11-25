#include <stdio.h>
#include <esp_log.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include "crycare_protocols.h"
#include<freertos/queue.h>
#include<math.h>
#include "i2s_mic.h"
#include "espnow_trans.h"
static QueueHandle_t audio_queue = NULL;
static const char *TAG = "S3";
static TickType_t cooldown_time = pdMS_TO_TICKS(0);
static bool is_cooldown = false;
typedef struct{
    int16_t sample[I2S_READ_CHUNK_MAX];
    size_t size;
} audio_chunk_t;

static void produce_task(void *Parameter){
    audio_chunk_t box;
    while(1){
        esp_err_t ret_read = i2s_mic_read(box.sample, I2S_READ_CHUNK_MAX, &box.size);
        if (ret_read != ESP_OK || box.size == 0){
            ESP_LOGE(TAG, "CANNOT READ AUDIO, TRY AGAIN AFTER 32ms");
            vTaskDelay(pdMS_TO_TICKS(32));
            continue;
        }
        xQueueSend(audio_queue, &box, pdMS_TO_TICKS(10));
    }
}
static void consume_task(void *Parameter){
    audio_chunk_t box;
    int total_cried = 0;
    cooldown_time = xTaskGetTickCount();
    while(1){
        BaseType_t res = xQueueReceive(audio_queue, &box, portMAX_DELAY);
        if (res == pdTRUE){
            int64_t sum_sq = 0;
            for (int i = 0; i < box.size;i++){
                int64_t s = box.sample[i];
                sum_sq += s * s;
            }
            float rms = sqrtf((float) sum_sq / (float) box.size);
            float dbfs = 20.0f * log10f((rms + 1e-6f)/32768.0f);
            if (dbfs >= -25.0f){
                // call AI function to detect whether a queue block is cry or not
                TickType_t now = xTaskGetTickCount();
                if (now - cooldown_time < pdMS_TO_TICKS(3000) && is_cooldown){
                    continue;
                }
                else if(now - cooldown_time >= pdMS_TO_TICKS(3000) && is_cooldown) {
                    total_cried = 0;
                    is_cooldown = false;
                }
                else{
                    total_cried++;
                    ESP_LOGI(TAG, "CRY: %d/3", total_cried);
                }
                if(total_cried >= 3 && !is_cooldown){
                    ESP_LOGW(TAG, "CRY_ALERT | dbfs = %.2f", dbfs);
                    esp_err_t check_send = espnow_trans_send(80, dbfs, 600, 70); 
                    // demo 0.8, 20000, 0.7 since we do not have AI model right now
                    cooldown_time = xTaskGetTickCount();
                    if (check_send != ESP_OK){
                        ESP_LOGE(TAG, "CANNOT SEND TO C3, please try again");
                    }
                    else {
                        is_cooldown = true;
                    } 
                    /*what we miss for now:
                    1.AI Model processing: conf, duty_cycle, f0_hz
                    2.Cooldown for packet to send*/ 
                }
            }
            else{
                total_cried = 0;
            }
        }
    }
}
void app_main(void){
    bool is_mic_ok = false;
    while(!is_mic_ok){
        esp_err_t ret_init = i2s_mic_init();
        if (ret_init != ESP_OK){
            ESP_LOGE(TAG, "Cannot init audio, please try again");
            vTaskDelay(pdMS_TO_TICKS(500));
            // question: how will we init and try to init the code again? using for or while?
        }
        else {
            is_mic_ok = true;
        }
    }
    while(1){   
        esp_err_t check_init = espnow_trans_init();
        if (check_init != ESP_OK){
            ESP_LOGE(TAG, "Error, cannot init espnow, please try again");
            vTaskDelay(pdMS_TO_TICKS(1000));
            continue;
        }
        break;
    }
    audio_queue = xQueueCreate(4, sizeof(audio_chunk_t));
    xTaskCreatePinnedToCore(produce_task, "produce", 4096, NULL, 5, NULL, 0); // 0 mean CORE 0 - 5 mean highest priority
    xTaskCreatePinnedToCore(consume_task, "consume", 4096, NULL, 4, NULL, 1); // 1 mean CORE 1 - 4 mean nearly highest priority
}




