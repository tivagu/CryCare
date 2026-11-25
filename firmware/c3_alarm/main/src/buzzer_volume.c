#include"buzzer_volume.h"
#include "driver/ledc.h"
#define GPIO_AUDIO 4
esp_err_t buzzer_volume_init(){
    ledc_timer_config_t ledc_cfg = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .duty_resolution = LEDC_TIMER_10_BIT,
        .timer_num = LEDC_TIMER_0,
        .freq_hz = 2700,
        .clk_cfg = LEDC_AUTO_CLK
    };
    esp_err_t check_ledc_time = ledc_timer_config(&ledc_cfg);
    if (check_ledc_time != ESP_OK) return check_ledc_time;
    ledc_channel_config_t channel_cfg ={
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .gpio_num = GPIO_AUDIO,
        .channel = LEDC_CHANNEL_0,
        .timer_sel = LEDC_TIMER_0,
        .duty = 0,
        .hpoint = 0
    };
    esp_err_t check_channel = ledc_channel_config(&channel_cfg);
    if (check_channel != ESP_OK) return check_channel;
    return ESP_OK;
}
esp_err_t buzzer_volume_set(bool on){
    ledc_mode_t speed_mode = LEDC_LOW_SPEED_MODE;
    ledc_channel_t channel = LEDC_CHANNEL_0;
    uint16_t duty = on ? 512 : 0;
    esp_err_t check_set_duty = ledc_set_duty(speed_mode, channel, duty);
    if (check_set_duty != ESP_OK) return check_set_duty;
    esp_err_t check_update = ledc_update_duty(speed_mode, channel);
    if (check_update != ESP_OK) return check_update;
    return ESP_OK;
}
