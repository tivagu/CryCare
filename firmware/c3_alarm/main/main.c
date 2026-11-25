#include "include/receive_from_s3.h"
#include "crycare_protocols.h"
#include"buzzer_volume.h"
#include<freertos/FreeRTOS.h>
#include<freertos/task.h>
#include <esp_log.h>
static const char* TAG = "C3";
void app_main(){
    QueueHandle_t rx_queue = xQueueCreate(8, sizeof(crycare_packet_t));
    esp_err_t init = receive_from_s3_init(rx_queue);
    if (init != ESP_OK){
        ESP_LOGE(TAG, "Error cannot init remote access");
        return;
    }
    esp_err_t check_volume = buzzer_volume_init();
    if (check_volume != ESP_OK){
        ESP_LOGE(TAG, "cannot init volume");
        return;
    }
    crycare_packet_t pkt = {0};
    while(1){
        if (xQueueReceive(rx_queue,&pkt, portMAX_DELAY) == pdTRUE){
            ESP_LOGW(TAG, "SUCCESSFULLY RECEIVED A PACKET FROM S3");
            ESP_LOGI(TAG, "event = %d, conf = %d, dbfs = %d, f0_hz = %d",pkt.event_type, pkt.conf, pkt.dbfs, pkt.f0_hz);
            if (pkt.event_type == CRY){
                for (int i = 0; i < 5; i++){
                    buzzer_volume_set(true);
                    vTaskDelay(pdMS_TO_TICKS(200));
                    buzzer_volume_set(false);
                    vTaskDelay(pdMS_TO_TICKS(200));
                }
            }
        }
    }
}