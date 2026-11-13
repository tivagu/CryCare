#pragma once
#include <stdint.h>
#include<assert.h>
typedef enum  {
    CRY = 0x00,
    ACK_PRESS = 0x01,
    OFF_ACK = 0x02,
    SENSITIVITY = 0x03
} event_enum;

typedef struct __attribute__ ((packed)){ // ask system not to padding the struct type 
    uint8_t magic_byte; // to recognize packets exactly
    uint8_t event_type; //event type 
    uint8_t conf; // confidence | 3 bytes
    uint16_t f0_hz; // hz | if not stop padding -> 3 + 1 (padding) + 2
    int8_t dbfs; 
    uint8_t duty_cycle; 
    uint32_t seq_id; // id (4 bilions long) | if not stop padding -> 7 + 1 + 4 = 11
    uint8_t back_up[4]; // backup (get 16 bytes) | 11 + 5 + 4
    uint8_t check; // check noise if bitwise | 20 for padding
}crycare_packet_t; 

static_assert(sizeof(crycare_packet_t) == 16, "Packet size must equal to 16 bytes");