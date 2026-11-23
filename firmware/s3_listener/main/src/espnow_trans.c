#include "espnow_trans.h"
#include "crycare_protocols.h"
#include<string.h>
#include <esp_log.h> 
#include <nvs_flash.h>
#include <esp_netif.h>
#include<esp_event.h>
#include<esp_wifi.h>
#include<esp_now.h>

/*Experience: for every .c file, we should add const char *TAG to ESP_LOGI*/
static const char *TAG = "ESPNOW_TX";
static const uint8_t C3_MAC[6] = {0xFF, 0xFF, 0xFF,0xFF, 0xFF, 0xFF}; // DEMO

static void on_data_sent(const esp_now_send_info_t *tx_info, esp_now_send_status_t status){ // to check whether C3 is earned packet or not
    if (status == ESP_NOW_SEND_SUCCESS){
        ESP_LOGI(TAG, "Sucessfully sent to C3");
    }
    else{
        ESP_LOGW(TAG, "CANNOT send to C3, try again...");
    }
    (void) tx_info;
}

esp_err_t espnow_trans_init(){
    /*Workflow:
    *1. init nvs for Wifi storage
    *2. init esp_netif and esp_event_loop to config for wifi
    *3. init wifi config and run wifi to run 2.4GHz anten
    *4. then init netif_init and esp_event_loop for for hardware and higher software to communicate
    *5. then init esp_now and register peer -> we will store these peer value to nvs for a faster run in next run
    */

    // init: nvs (check whether new version or no free_pages) -> create another nvs for storing
    // init: netif_init() create a TCP/IP protocol to communicate with higher protocals include MQTT/HTTP
    // init: esp_event_loop_default to store and track all current events from wifi + esp_now
    // init: esp_wifi_config and esp_wifi_init(), we use 2.4 GHz anten from Wifi but not use Wifi literally
    // init: esp_now_init() create an esp_now and create a register_send_cd(on_data_sent) to write past event
    // init: esp_now_peer_info_t, we copy C3_MAC and set peer.channel = 0 and encrypt = false
    // init: add_peer(&peer) and return;
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND){
        nvs_flash_erase();
        esp_err_t ret_nvs = nvs_flash_init();
        if (ret_nvs != ESP_OK) return ret_nvs;
    }

    esp_err_t ret_netif = esp_netif_init(); // create a TCP/IP for ESP-IDF to communicate with higher protocol includes MQTT/ HTTP 
    esp_err_t event_loop = esp_event_loop_create_default(); // create a loop event for wifi to track and attach
    if (ret_netif != ESP_OK) return ret_netif;
    if (event_loop != ESP_OK) return event_loop; 
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT(); // default config for wifi
    esp_wifi_init(&cfg); 
    esp_wifi_set_mode(WIFI_MODE_STA); 
    esp_wifi_start();
    esp_err_t ret_esp_now = esp_now_init();
    if (ret_esp_now != ESP_OK) return ret_esp_now;
    esp_err_t ret_register =  esp_now_register_send_cb(on_data_sent); // send event and information to event_loop (on_data_sent mean track C3 whether C3 get and send back)
    if (ret_register != ESP_OK) return ret_register;
    esp_now_peer_info_t peer = {0};
    memcpy(peer.peer_addr, C3_MAC, 6); // write 6 MAC bytes + peer.channel = 0; peer.encrypt = false;
    esp_err_t peer_config = esp_now_add_peer(&peer);
    if (peer_config != ESP_OK) return peer_config;
    return ESP_OK;
}

esp_err_t espnow_trans_send(uint8_t conf, int8_t dbfs, uint16_t f0_hz, uint8_t duty_circle){
/*Workflow:
* 1. After getting at least 3 Crycare packets -> we immediately send an esp now packet to C3 to alert.
* 2. However, since baby cry non stop for minutes and wait for mom or someone come -> we need to create a cooldown time after send an alert (stop spamming)
* 3. People are afraid of scam and mis-understand things. Therefore, after sending -> cooldown activate and only 1 JSON is available*
* 4. However, we only care about send a packet to C3 through ESP_NOW*/

}