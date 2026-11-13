#include <stdio.h>
#include <esp_log.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

static const char *TAG = "S3";

void app_main(void){
    ESP_LOGI(TAG, "=====================");
    ESP_LOGI(TAG, "CRYCARE - S3");
    ESP_LOGI(TAG, "=====================");
    while(1){
        ESP_LOGI(TAG, "HeartBeat: System is alive...");
        vTaskDelay(pdMS_TO_TICKS(3000));
    }
}




