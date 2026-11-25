#pragma once
#include<stdbool.h>
#include<esp_err.h> // esp_err for esp_err_t
esp_err_t buzzer_volume_init();
esp_err_t buzzer_volume_set (bool on);