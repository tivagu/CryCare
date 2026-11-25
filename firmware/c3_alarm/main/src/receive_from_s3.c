#include"receive_from_s3.h"
#include "crycare_protocols.h"
#include<esp_now.h>
#include<esp_log.h>
#include<string.h>
#include<nvs_flash.h>
#include<esp_wifi.h>
static QueueHandle_t rx_queue = NULL;
static void on_data_recv(const esp_now_recv_info_t* esp_now_info, const uint8_t *data, int data_len){
    (void) esp_now_info;
    if (data == NULL || data_len != sizeof(crycare_packet_t)) return;
    crycare_packet_t pkg = {0};
    memcpy(&pkg, data, sizeof(crycare_packet_t));
    if (pkg.magic_byte != 0xCC || pkg.check != checksum_xor(&pkg)){
        ESP_LOGE("C3", "trash packet");
        return;
    }
    xQueueSend(rx_queue, &pkg, 0);
}
esp_err_t receive_from_s3_init(QueueHandle_t queue){
    if (queue == NULL) return ESP_ERR_INVALID_ARG;
    rx_queue = queue;
    esp_err_t check_nvs = nvs_flash_init();
    if (check_nvs == ESP_ERR_NVS_NO_FREE_PAGES || check_nvs == ESP_ERR_NVS_NEW_VERSION_FOUND){
        nvs_flash_erase();
        esp_err_t new_nvs = nvs_flash_init();
        if(new_nvs != ESP_OK) return new_nvs;
    }
    esp_err_t check_netif = esp_netif_init();
    if (check_netif != ESP_OK) return check_netif;
    esp_err_t check_loop = esp_event_loop_create_default();
    if (check_loop != ESP_OK) return check_loop;
    wifi_init_config_t wifi_cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_err_t check_wifi = esp_wifi_init(&wifi_cfg);
    if(check_wifi != ESP_OK) return check_wifi;
    esp_wifi_set_mode(WIFI_MODE_STA);
    esp_wifi_start();
    esp_err_t check_espnow = esp_now_init();
    esp_now_register_recv_cb(on_data_recv); // init espnow then register later
    if(check_espnow != ESP_OK) return check_espnow;
    return ESP_OK;
}


