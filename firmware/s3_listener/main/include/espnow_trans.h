#pragma once
#include <esp_err.h>
#include <stdint.h>

/*Workflow:
* 1. espnow_trans_init: init and declare WIFI + MAC for C3
* 2. ready for sending a packet for C3 */

esp_err_t espnow_trans_init(); // init MAC + Wifi, ready for sending event to C3

esp_err_t espnow_trans_send(uint8_t conf, int8_t dbfs, uint16_t f0_hz, uint8_t duty_cycle); // send packet to C3




