#pragma once
#include<esp_err.h>
#include<freertos/FreeRTOS.h>


esp_err_t receive_from_s3_init(QueueHandle_t queue);
